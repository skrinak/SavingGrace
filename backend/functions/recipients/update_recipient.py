"""
Update Recipient Lambda Function
PUT /recipients/{recipientId}
Updates an existing recipient
"""
import json
import os
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError, NotFoundError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update recipient

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with updated recipient
    """
    try:
        # Get recipient ID from path parameters
        recipient_id = event.get("pathParameters", {}).get("recipientId")

        if not recipient_id:
            return error_response(
                message="Recipient ID is required",
                status_code=400,
            )

        # Log request
        logger.log_api_request(
            method=event.get("httpMethod"),
            path=event.get("path"),
            user_id=get_user_from_event(event).get("sub"),
            recipient_id=recipient_id,
        )

        # Parse input
        body = json.loads(event.get("body", "{}"))

        # Check if recipient exists
        try:
            db.get_item(pk=f"RECIPIENT#{recipient_id}", sk="PROFILE")
        except NotFoundError:
            return error_response(
                message=f"Recipient with ID '{recipient_id}' not found",
                status_code=404,
                error_code="NOT_FOUND",
            )

        # Build updates dictionary
        updates = {}

        # Validate and add name if provided
        if "name" in body:
            name = Validator.validate_string(body.get("name"), "name", min_length=2, max_length=100)
            updates["name"] = name
            # Update GSI1SK for searching
            updates["GSI1SK"] = name.lower()

        # Validate and add contact_name if provided
        if "contact_name" in body:
            updates["contact_name"] = Validator.validate_string(
                body.get("contact_name"), "contact_name", min_length=2, max_length=100
            )

        # Validate and add contact_phone if provided
        if "contact_phone" in body:
            updates["contact_phone"] = Validator.validate_phone(body.get("contact_phone"))

        # Validate and add contact_email if provided
        if "contact_email" in body:
            if body.get("contact_email"):
                updates["contact_email"] = Validator.validate_email(body.get("contact_email"))
            else:
                updates["contact_email"] = None

        # Validate and add address if provided
        if "address" in body:
            updates["address"] = Validator.validate_string(
                body.get("address"), "address", min_length=5, max_length=500
            )

        # Validate and add household_size if provided
        if "household_size" in body:
            household_size = Validator.validate_number(
                body.get("household_size"), "household_size", min_value=1
            )
            updates["household_size"] = int(household_size)

        # Validate and add needs if provided
        if "needs" in body:
            updates["needs"] = Validator.validate_list(body.get("needs"), "needs")

        # Validate and add notes if provided
        if "notes" in body:
            if body.get("notes"):
                updates["notes"] = Validator.validate_string(
                    body.get("notes"), "notes", max_length=1000
                )
            else:
                updates["notes"] = None

        # Check if there are any updates
        if not updates:
            return error_response(
                message="No valid fields to update",
                status_code=400,
            )

        # Update in DynamoDB
        updated_recipient = db.update_item(
            pk=f"RECIPIENT#{recipient_id}", sk="PROFILE", updates=updates
        )

        logger.info(
            "Recipient updated successfully",
            recipient_id=recipient_id,
            updated_fields=list(updates.keys()),
        )

        # Return response (remove DynamoDB keys)
        response_data = {
            k: v for k, v in updated_recipient.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]
        }

        return success_response(response_data)

    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except SavingGraceError as e:
        logger.error("Application error", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
