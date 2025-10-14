"""
Create User Lambda Function
POST /users - Create new user in Cognito and DynamoDB
"""
import json
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import ConflictError, ValidationError, SavingGraceError
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
    Create new user

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with created user
    """
    try:
        # Log request
        current_user = get_user_from_event(event)
        logger.info(
            "Create user request",
            user_id=current_user.get("sub"),
            user_email=current_user.get("email")
        )

        # Parse and validate input
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        Validator.validate_required_fields(
            body,
            ["email", "given_name", "family_name", "role"]
        )

        # Validate fields
        email = Validator.validate_email(body["email"])
        given_name = Validator.validate_string(
            body["given_name"],
            "given_name",
            min_length=1,
            max_length=100
        )
        family_name = Validator.validate_string(
            body["family_name"],
            "family_name",
            min_length=1,
            max_length=100
        )
        role = Validator.validate_enum(body["role"], "role", VALID_ROLES)

        # Optional phone validation
        phone = None
        if "phone" in body and body["phone"]:
            phone = Validator.validate_phone(body["phone"])

        # Get environment variables
        user_pool_id = os.environ['USER_POOL_ID']

        # Create user in Cognito
        try:
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'given_name', 'Value': given_name},
                {'Name': 'family_name', 'Value': family_name},
                {'Name': 'custom:role', 'Value': role},
            ]

            if phone:
                user_attributes.append({'Name': 'phone_number', 'Value': phone})

            cognito_response = cognito_client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=email,
                UserAttributes=user_attributes,
                DesiredDeliveryMediums=['EMAIL']
            )

            user_sub = cognito_response['User']['Username']

            # Extract sub from attributes if available
            for attr in cognito_response['User']['Attributes']:
                if attr['Name'] == 'sub':
                    user_sub = attr['Value']
                    break

            logger.info(
                "User created in Cognito",
                user_sub=user_sub,
                email=email,
                role=role
            )

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                raise ConflictError(
                    message=f"User with email {email} already exists",
                    details={"email": email}
                )
            else:
                logger.error("Cognito create user failed", error=e)
                raise SavingGraceError(
                    message=f"Failed to create user in Cognito: {str(e)}",
                    status_code=500
                )

        # Add user to Cognito group
        try:
            cognito_client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=email,
                GroupName=role
            )

            logger.info(
                "User added to Cognito group",
                user_sub=user_sub,
                group=role
            )

        except ClientError as e:
            logger.error("Failed to add user to group", error=e)
            # Clean up: delete the user if group assignment fails
            try:
                cognito_client.admin_delete_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
            except Exception as cleanup_error:
                logger.error("Failed to cleanup user after group assignment failure", error=cleanup_error)

            raise SavingGraceError(
                message=f"Failed to assign user to group: {str(e)}",
                status_code=500
            )

        # Store user profile in DynamoDB
        user_profile = {
            "PK": f"USER#{user_sub}",
            "SK": "PROFILE",
            "user_id": user_sub,
            "email": email,
            "given_name": given_name,
            "family_name": family_name,
            "role": role,
            "enabled": True,
        }

        if phone:
            user_profile["phone"] = phone

        try:
            db.put_item(user_profile)

            logger.info(
                "User profile saved to DynamoDB",
                user_id=user_sub
            )

        except Exception as e:
            logger.error("Failed to save user profile to DynamoDB", error=e)
            # Clean up: delete the user from Cognito
            try:
                cognito_client.admin_delete_user(
                    UserPoolId=user_pool_id,
                    Username=email
                )
            except Exception as cleanup_error:
                logger.error("Failed to cleanup user after DynamoDB failure", error=cleanup_error)

            raise SavingGraceError(
                message=f"Failed to save user profile: {str(e)}",
                status_code=500
            )

        # Build response object
        user_data = {
            "user_id": user_sub,
            "email": email,
            "given_name": given_name,
            "family_name": family_name,
            "role": role,
            "enabled": True,
            "created_at": user_profile["created_at"],
            "updated_at": user_profile["updated_at"],
        }

        if phone:
            user_data["phone"] = phone

        logger.info("User created successfully", user_id=user_sub)

        return success_response(user_data, status_code=201)

    except (ValidationError, ConflictError, SavingGraceError) as e:
        logger.warning(f"User creation failed: {e.message}", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error creating user", error=e)
        return error_response(
            message="An unexpected error occurred",
            status_code=500,
        )
