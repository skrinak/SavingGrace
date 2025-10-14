"""
Custom Exception Classes
Domain-specific errors for SavingGrace application
"""
from typing import Any, Dict, Optional


class SavingGraceError(Exception):
    """Base exception for SavingGrace application"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERROR_{status_code}"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SavingGraceError):
    """Input validation error"""

    def __init__(
        self,
        message: str = "Invalid input",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(SavingGraceError):
    """Resource not found error"""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with ID '{resource_id}' not found"

        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
        )


class AuthorizationError(SavingGraceError):
    """Authorization/permission error"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_role: Optional[str] = None,
    ):
        details = {}
        if required_role:
            details["required_role"] = required_role

        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class ConflictError(SavingGraceError):
    """Resource conflict error (e.g., duplicate)"""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class DatabaseError(SavingGraceError):
    """Database operation error"""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details,
        )
