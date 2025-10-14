"""
Update User Lambda Function
PUT /users/{userId} - Update user in Cognito and DynamoDB
"""
import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import NotFoundError, ValidationError, SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()
cognito_client = boto3.client('cognito-idp', region_name='us-west-2')


@require_role("Admin")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update user

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
            "Update user request",
            user_id=current_user.get("sub"),
            user_email=current_user.get("email")
        )

        # Get userId from path parameters
        path_params = event.get("pathParameters", {})
        if not path_params or "userId" not in path_params:
            raise NotFoundError(resource="User", resource_id="unknown")

        user_id = path_params["userId"]

        # Parse and validate input
        body = json.loads(event.get("body", "{}"))

        # Validate at least one field is provided
        allowed_fields = ["given_name", "family_name", "phone", "enabled"]
        if not any(field in body for field in allowed_fields):
            raise ValidationError(
                message="At least one field must be provided for update",
                details={"allowed_fields": allowed_fields}
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
            logger.warning("User not found", user_id=user_id)
            raise NotFoundError(resource="User", resource_id=user_id)

        email = user_profile.get("email")

        # Prepare Cognito updates
        cognito_attributes = []
        dynamodb_updates = {}

        # Validate and prepare given_name
        if "given_name" in body:
            given_name = Validator.validate_string(
                body["given_name"],
                "given_name",
                min_length=1,
                max_length=100
            )
            cognito_attributes.append({'Name': 'given_name', 'Value': given_name})
            dynamodb_updates["given_name"] = given_name

        # Validate and prepare family_name
        if "family_name" in body:
            family_name = Validator.validate_string(
                body["family_name"],
                "family_name",
                min_length=1,
                max_length=100
            )
            cognito_attributes.append({'Name': 'family_name', 'Value': family_name})
            dynamodb_updates["family_name"] = family_name

        # Validate and prepare phone
        if "phone" in body:
            if body["phone"]:
                phone = Validator.validate_phone(body["phone"])
                cognito_attributes.append({'Name': 'phone_number', 'Value': phone})
                dynamodb_updates["phone"] = phone
            else:
                # Remove phone number
                dynamodb_updates["phone"] = None

        # Handle enabled status
        if "enabled" in body:
            if not isinstance(body["enabled"], bool):
                raise ValidationError(
                    message="enabled must be a boolean",
                    details={"field": "enabled"}
                )
            enabled = body["enabled"]
            dynamodb_updates["enabled"] = enabled

        # Update user in Cognito
        try:
            # Update attributes
            if cognito_attributes:
                cognito_client.admin_update_user_attributes(
                    UserPoolId=user_pool_id,
                    Username=email,
                    UserAttributes=cognito_attributes
                )

                logger.info(
                    "User attributes updated in Cognito",
                    user_id=user_id,
                    attributes_count=len(cognito_attributes)
                )

            # Enable or disable user
            if "enabled" in body:
                if enabled:
                    cognito_client.admin_enable_user(
                        UserPoolId=user_pool_id,
                        Username=email
                    )
                    logger.info("User enabled in Cognito", user_id=user_id)
                else:
                    cognito_client.admin_disable_user(
                        UserPoolId=user_pool_id,
                        Username=email
                    )
                    logger.info("User disabled in Cognito", user_id=user_id)

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UserNotFoundException':
                logger.warning("User not found in Cognito", user_id=user_id)
                raise NotFoundError(resource="User", resource_id=user_id)
            else:
                logger.error("Cognito update user failed", error=e)
                raise SavingGraceError(
                    message=f"Failed to update user in Cognito: {str(e)}",
                    status_code=500
                )

        # Update user profile in DynamoDB
        try:
            updated_profile = db.update_item(
                pk=f"USER#{user_id}",
                sk="PROFILE",
                updates=dynamodb_updates
            )

            logger.info(
                "User profile updated in DynamoDB",
                user_id=user_id
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

        logger.info("User updated successfully", user_id=user_id)

        return success_response(user_data)

    except (ValidationError, NotFoundError, SavingGraceError) as e:
        logger.warning(f"User update failed: {e.message}", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error updating user", error=e)
        return error_response(
            message="An unexpected error occurred",
            status_code=500,
        )
