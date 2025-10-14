"""
Authentication and Authorization Utilities
Cognito integration and role-based access control
"""
from typing import Any, Dict, List, Optional, Set
from functools import wraps

from .errors import AuthorizationError


# Role hierarchy and permissions
ROLE_HIERARCHY = {
    "Admin": 5,
    "DonorCoordinator": 4,
    "DistributionManager": 3,
    "Volunteer": 2,
    "ReadOnly": 1,
}

# Permissions by role
ROLE_PERMISSIONS = {
    "Admin": {
        "users:create",
        "users:read",
        "users:update",
        "users:delete",
        "donors:*",
        "donations:*",
        "recipients:*",
        "distributions:*",
        "inventory:*",
        "reports:*",
    },
    "DonorCoordinator": {
        "donors:create",
        "donors:read",
        "donors:update",
        "donations:create",
        "donations:read",
        "donations:update",
        "inventory:read",
        "inventory:adjust",
        "reports:read",
    },
    "DistributionManager": {
        "recipients:create",
        "recipients:read",
        "recipients:update",
        "distributions:create",
        "distributions:read",
        "distributions:update",
        "distributions:complete",
        "inventory:read",
        "inventory:adjust",
        "reports:read",
    },
    "Volunteer": {
        "donors:read",
        "donations:read",
        "recipients:read",
        "distributions:read",
        "distributions:complete",
        "inventory:read",
        "reports:read",
    },
    "ReadOnly": {
        "donors:read",
        "donations:read",
        "recipients:read",
        "distributions:read",
        "inventory:read",
        "reports:read",
    },
}


class AuthHelper:
    """Helper class for authentication and authorization"""

    @staticmethod
    def get_user_from_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from API Gateway event

        Args:
            event: API Gateway event

        Returns:
            User information dict with sub, email, role, groups

        Raises:
            AuthorizationError: If user context not found
        """
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        claims = authorizer.get("claims", {})

        if not claims:
            raise AuthorizationError(message="No user context found in request")

        return {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "role": claims.get("custom:role", "ReadOnly"),
            "groups": claims.get("cognito:groups", "").split(",") if claims.get("cognito:groups") else [],
            "given_name": claims.get("given_name"),
            "family_name": claims.get("family_name"),
        }

    @staticmethod
    def has_permission(user_role: str, permission: str) -> bool:
        """
        Check if user role has specific permission

        Args:
            user_role: User's role
            permission: Permission to check (e.g., "donors:create")

        Returns:
            True if user has permission
        """
        if user_role not in ROLE_PERMISSIONS:
            return False

        user_permissions = ROLE_PERMISSIONS[user_role]

        # Check exact permission
        if permission in user_permissions:
            return True

        # Check wildcard permissions (e.g., "donors:*")
        resource = permission.split(":")[0]
        if f"{resource}:*" in user_permissions:
            return True

        return False

    @staticmethod
    def has_role(user_role: str, required_role: str) -> bool:
        """
        Check if user has required role or higher in hierarchy

        Args:
            user_role: User's role
            required_role: Required role

        Returns:
            True if user has required role or higher
        """
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    @staticmethod
    def check_resource_access(
        user: Dict[str, Any],
        resource_type: str,
        action: str,
        resource_owner: Optional[str] = None,
    ) -> bool:
        """
        Check if user can access specific resource

        Args:
            user: User information dict
            resource_type: Type of resource (donors, donations, etc.)
            action: Action to perform (create, read, update, delete)
            resource_owner: Optional owner ID for ownership check

        Returns:
            True if user has access

        Raises:
            AuthorizationError: If user lacks permission
        """
        user_role = user.get("role", "ReadOnly")
        permission = f"{resource_type}:{action}"

        # Check permission
        if not AuthHelper.has_permission(user_role, permission):
            raise AuthorizationError(
                message=f"Insufficient permissions for {permission}",
                required_role=user_role,
            )

        # For read operations, always allow if user has read permission
        if action == "read":
            return True

        # For other operations, check if user is owner (if ownership matters)
        if resource_owner and resource_owner != user.get("sub"):
            # Only Admin can modify other users' resources
            if user_role != "Admin":
                raise AuthorizationError(
                    message="Can only modify your own resources",
                    required_role="Admin",
                )

        return True


def require_role(required_role: str):
    """
    Decorator to require specific role for Lambda function

    Args:
        required_role: Minimum required role

    Usage:
        @require_role("DonorCoordinator")
        def lambda_handler(event, context):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            user = get_user_from_event(event)
            if not AuthHelper.has_role(user.get("role"), required_role):
                raise AuthorizationError(
                    message=f"Role {required_role} or higher required",
                    required_role=required_role,
                )
            return func(event, context)

        return wrapper

    return decorator


def require_permission(permission: str):
    """
    Decorator to require specific permission for Lambda function

    Args:
        permission: Required permission (e.g., "donors:create")

    Usage:
        @require_permission("donors:create")
        def lambda_handler(event, context):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(event, context):
            user = get_user_from_event(event)
            if not AuthHelper.has_permission(user.get("role"), permission):
                raise AuthorizationError(
                    message=f"Permission {permission} required",
                )
            return func(event, context)

        return wrapper

    return decorator


# Convenience function for getting user from event
def get_user_from_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from API Gateway event

    Args:
        event: API Gateway event

    Returns:
        User information dict
    """
    return AuthHelper.get_user_from_event(event)
