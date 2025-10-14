"""
Get User Lambda Function
GET /users/{userId} - Retrieve user from Cognito and DynamoDB
"""
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import NotFoundError, SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()
cognito_client = boto3.client("cognito-idp", region_name="us-west-2")


@require_role("Admin")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get user by ID

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with user object
    """
    try:
        # Log request
        current_user = get_user_from_event(event)
        logger.info(
            "Get user request",
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
        )

        # Get userId from path parameters
        path_params = event.get("pathParameters", {})
        if not path_params or "userId" not in path_params:
            raise NotFoundError(resource="User", resource_id="unknown")

        user_id = path_params["userId"]

        # Get environment variables
        user_pool_id = os.environ["USER_POOL_ID"]

        # Get user profile from DynamoDB
        try:
            user_profile = db.get_item(pk=f"USER#{user_id}", sk="PROFILE")

            logger.info("User profile retrieved from DynamoDB", user_id=user_id)

        except NotFoundError:
            logger.warning("User not found in DynamoDB", user_id=user_id)
            raise NotFoundError(resource="User", resource_id=user_id)

        # Get user from Cognito for additional details
        cognito_user_data = {}
        try:
            cognito_response = cognito_client.admin_get_user(
                UserPoolId=user_pool_id, Username=user_profile.get("email")
            )

            # Parse Cognito attributes
            for attr in cognito_response.get("UserAttributes", []):
                attr_name = attr["Name"]
                attr_value = attr["Value"]

                if attr_name == "email_verified":
                    cognito_user_data["email_verified"] = attr_value == "true"
                elif attr_name == "phone_number":
                    cognito_user_data["phone"] = attr_value
                elif attr_name == "phone_number_verified":
                    cognito_user_data["phone_verified"] = attr_value == "true"

            # Get user status
            cognito_user_data["user_status"] = cognito_response.get("UserStatus")
            cognito_user_data["enabled"] = cognito_response.get("Enabled", True)

            # Get last login if available
            if "UserLastModifiedDate" in cognito_response:
                cognito_user_data["last_modified"] = cognito_response[
                    "UserLastModifiedDate"
                ].isoformat()

            logger.info("User details retrieved from Cognito", user_id=user_id)

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "UserNotFoundException":
                logger.warning("User not found in Cognito", user_id=user_id)
                # User exists in DynamoDB but not in Cognito (data inconsistency)
                # Return DynamoDB data only
                cognito_user_data["enabled"] = user_profile.get("enabled", True)
            else:
                logger.error("Cognito get user failed", error=e)
                raise SavingGraceError(
                    message=f"Failed to retrieve user from Cognito: {str(e)}", status_code=500
                )

        # Combine DynamoDB and Cognito data
        user_data = {
            "user_id": user_profile.get("user_id"),
            "email": user_profile.get("email"),
            "given_name": user_profile.get("given_name"),
            "family_name": user_profile.get("family_name"),
            "role": user_profile.get("role"),
            "enabled": cognito_user_data.get("enabled", user_profile.get("enabled", True)),
            "created_at": user_profile.get("created_at"),
            "updated_at": user_profile.get("updated_at"),
        }

        # Add optional fields from DynamoDB
        if "phone" in user_profile:
            user_data["phone"] = user_profile["phone"]
        elif "phone" in cognito_user_data:
            user_data["phone"] = cognito_user_data["phone"]

        if "last_login" in user_profile:
            user_data["last_login"] = user_profile["last_login"]

        # Add Cognito-specific fields
        if "email_verified" in cognito_user_data:
            user_data["email_verified"] = cognito_user_data["email_verified"]

        if "phone_verified" in cognito_user_data:
            user_data["phone_verified"] = cognito_user_data["phone_verified"]

        if "user_status" in cognito_user_data:
            user_data["user_status"] = cognito_user_data["user_status"]

        logger.info("User retrieved successfully", user_id=user_id)

        return success_response(user_data)

    except (NotFoundError, SavingGraceError) as e:
        logger.warning(f"Get user failed: {e.message}", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error getting user", error=e)
        return error_response(
            message="An unexpected error occurred",
            status_code=500,
        )
