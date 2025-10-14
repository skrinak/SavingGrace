"""
Update User Role Lambda Function
PUT /users/{userId}/role - Update user role in Cognito and DynamoDB
"""
import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import AuthorizationError, NotFoundError, ValidationError, SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()
cognito_client = boto3.client('cognito-idp', region_name='us-west-2')

# Valid roles
VALID_ROLES = ["Admin", "DonorCoordinator", "DistributionManager", "Volunteer", "ReadOnly"]


@require_role("Admin")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update user role

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with updated user
    """
    try:
        # Log request
        current_user = get_user_from_event(event)
        logger.info(
            "Update user role request",
            user_id=current_user.get("sub"),
            user_email=current_user.get("email")
        )

        # Get userId from path parameters
        path_params = event.get("pathParameters", {})
        if not path_params or "userId" not in path_params:
            raise NotFoundError(resource="User", resource_id="unknown")

        user_id = path_params["userId"]

        # Check if trying to change your own role
        if user_id == current_user.get("sub"):
            logger.warning(
                "User attempted to change their own role",
                user_id=user_id
            )
            raise AuthorizationError(
                message="Cannot change your own role"
            )

        # Parse and validate input
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        Validator.validate_required_fields(body, ["role"])

        # Validate role
        new_role = Validator.validate_enum(body["role"], "role", VALID_ROLES)

        # Get environment variables
        user_pool_id = os.environ['USER_POOL_ID']

        # Check if user exists in DynamoDB
        try:
            user_profile = db.get_item(
                pk=f"USER#{user_id}",
                sk="PROFILE"
            )
        except NotFoundError:
            logger.warning("User not found in DynamoDB", user_id=user_id)
            raise NotFoundError(resource="User", resource_id=user_id)

        email = user_profile.get("email")
        old_role = user_profile.get("role")

        # Check if role is actually changing
        if old_role == new_role:
            logger.info(
                "Role unchanged, returning current user",
                user_id=user_id,
                role=old_role
            )
            # Return current user data
            user_data = {
                "user_id": user_profile.get("user_id"),
                "email": user_profile.get("email"),
                "given_name": user_profile.get("given_name"),
                "family_name": user_profile.get("family_name"),
                "role": user_profile.get("role"),
                "enabled": user_profile.get("enabled", True),
                "created_at": user_profile.get("created_at"),
                "updated_at": user_profile.get("updated_at"),
            }
            if user_profile.get("phone"):
                user_data["phone"] = user_profile["phone"]
            return success_response(user_data)

        # Update role in Cognito
        try:
            # Remove from old group
            if old_role:
                try:
                    cognito_client.admin_remove_user_from_group(
                        UserPoolId=user_pool_id,
                        Username=email,
                        GroupName=old_role
                    )
                    logger.info(
                        "User removed from old Cognito group",
                        user_id=user_id,
                        old_group=old_role
                    )
                except ClientError as e:
                    # Continue even if removal fails (user might not be in group)
                    logger.warning(
                        "Failed to remove user from old group",
                        user_id=user_id,
                        old_group=old_role,
                        error=str(e)
                    )

            # Add to new group
            cognito_client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=email,
                GroupName=new_role
            )
            logger.info(
                "User added to new Cognito group",
                user_id=user_id,
                new_group=new_role
            )

            # Update custom:role attribute
            cognito_client.admin_update_user_attributes(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'custom:role', 'Value': new_role}
                ]
            )
            logger.info(
                "User role attribute updated in Cognito",
                user_id=user_id,
                new_role=new_role
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                logger.warning("User not found in Cognito", user_id=user_id)
                raise NotFoundError(resource="User", resource_id=user_id)
            else:
                logger.error("Cognito update user role failed", error=e)
                raise SavingGraceError(
                    message=f"Failed to update user role in Cognito: {str(e)}",
                    status_code=500
                )

        # Update role in DynamoDB
        try:
            updated_profile = db.update_item(
                pk=f"USER#{user_id}",
                sk="PROFILE",
                updates={"role": new_role}
            )

            logger.info(
                "User role updated in DynamoDB",
                user_id=user_id,
                old_role=old_role,
                new_role=new_role
            )

        except NotFoundError:
            logger.warning("User profile not found in DynamoDB", user_id=user_id)
            raise NotFoundError(resource="User", resource_id=user_id)

        # Build response object
        user_data = {
            "user_id": updated_profile.get("user_id"),
            "email": updated_profile.get("email"),
            "given_name": updated_profile.get("given_name"),
            "family_name": updated_profile.get("family_name"),
            "role": updated_profile.get("role"),
            "enabled": updated_profile.get("enabled", True),
            "created_at": updated_profile.get("created_at"),
            "updated_at": updated_profile.get("updated_at"),
        }

        if updated_profile.get("phone"):
            user_data["phone"] = updated_profile["phone"]

        if updated_profile.get("last_login"):
            user_data["last_login"] = updated_profile["last_login"]

        logger.info(
            "User role updated successfully",
            user_id=user_id,
            old_role=old_role,
            new_role=new_role
        )

        return success_response(user_data)

    except (ValidationError, AuthorizationError, NotFoundError, SavingGraceError) as e:
        logger.warning(f"User role update failed: {e.message}", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error updating user role", error=e)
        return error_response(
            message="An unexpected error occurred",
            status_code=500,
        )
