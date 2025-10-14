"""
Delete User Lambda Function
DELETE /users/{userId} - Delete user from Cognito and DynamoDB
"""
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import AuthorizationError, NotFoundError, SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()
cognito_client = boto3.client('cognito-idp', region_name='us-west-2')


@require_role("Admin")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Delete user

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with success message
    """
    try:
        # Log request
        current_user = get_user_from_event(event)
        logger.info(
            "Delete user request",
            user_id=current_user.get("sub"),
            user_email=current_user.get("email")
        )

        # Get userId from path parameters
        path_params = event.get("pathParameters", {})
        if not path_params or "userId" not in path_params:
            raise NotFoundError(resource="User", resource_id="unknown")

        user_id = path_params["userId"]

        # Check if trying to delete yourself
        if user_id == current_user.get("sub"):
            logger.warning(
                "User attempted to delete themselves",
                user_id=user_id
            )
            raise AuthorizationError(
                message="Cannot delete your own user account"
            )

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

        # Delete user from Cognito
        try:
            cognito_client.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=email
            )

            logger.info(
                "User deleted from Cognito",
                user_id=user_id,
                email=email
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                logger.warning(
                    "User not found in Cognito (continuing with DynamoDB deletion)",
                    user_id=user_id
                )
                # Continue to delete from DynamoDB even if not in Cognito
            else:
                logger.error("Cognito delete user failed", error=e)
                raise SavingGraceError(
                    message=f"Failed to delete user from Cognito: {str(e)}",
                    status_code=500
                )

        # Delete user profile from DynamoDB
        try:
            db.delete_item(
                pk=f"USER#{user_id}",
                sk="PROFILE"
            )

            logger.info(
                "User profile deleted from DynamoDB",
                user_id=user_id
            )

        except Exception as e:
            logger.error("Failed to delete user profile from DynamoDB", error=e)
            raise SavingGraceError(
                message=f"Failed to delete user profile: {str(e)}",
                status_code=500
            )

        logger.info("User deleted successfully", user_id=user_id)

        return success_response({
            "message": "User deleted successfully",
            "user_id": user_id
        })

    except (AuthorizationError, NotFoundError, SavingGraceError) as e:
        logger.warning(f"User deletion failed: {e.message}", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error deleting user", error=e)
        return error_response(
            message="An unexpected error occurred",
            status_code=500,
        )
