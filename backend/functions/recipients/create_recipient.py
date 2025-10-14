"""
Create Recipient Lambda Function
POST /recipients
Creates a new recipient in the system
"""
import json
import os
import uuid
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
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
    Create new recipient

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with created recipient
    """
    try:
        # Log request
        logger.log_api_request(
            method=event.get("httpMethod"),
            path=event.get("path"),
            user_id=get_user_from_event(event).get("sub"),
        )

        # Parse and validate input
        body = json.loads(event.get("body", "{}"))

        # Validate required fields
        Validator.validate_required_fields(
            body,
            ["name", "contact_name", "contact_phone", "address", "household_size"]
        )

        # Validate name
        name = Validator.validate_string(
            body.get("name"),
            "name",
            min_length=2,
            max_length=100
        )

        # Validate contact_name
        contact_name = Validator.validate_string(
            body.get("contact_name"),
            "contact_name",
            min_length=2,
            max_length=100
        )

        # Validate contact_phone
        contact_phone = Validator.validate_phone(body.get("contact_phone"))

        # Validate contact_email (optional)
        contact_email = None
        if body.get("contact_email"):
            contact_email = Validator.validate_email(body.get("contact_email"))

        # Validate address
        address = Validator.validate_string(
            body.get("address"),
            "address",
            min_length=5,
            max_length=500
        )

        # Validate household_size
        household_size = Validator.validate_number(
            body.get("household_size"),
            "household_size",
            min_value=1
        )

        # Validate needs (optional list)
        needs = []
        if body.get("needs"):
            needs = Validator.validate_list(body.get("needs"), "needs")

        # Validate notes (optional)
        notes = None
        if body.get("notes"):
            notes = Validator.validate_string(
                body.get("notes"),
                "notes",
                max_length=1000
            )

        # Generate recipient ID
        recipient_id = str(uuid.uuid4())

        # Create recipient item
        recipient = {
            "PK": f"RECIPIENT#{recipient_id}",
            "SK": "PROFILE",
            "recipient_id": recipient_id,
            "name": name,
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "address": address,
            "household_size": int(household_size),
            "needs": needs,
            # GSI1 for searching recipients by name
            "GSI1PK": "RECIPIENTS",
            "GSI1SK": name.lower(),
        }

        # Add optional fields
        if contact_email:
            recipient["contact_email"] = contact_email
        if notes:
            recipient["notes"] = notes

        # Save to DynamoDB
        db.put_item(recipient)

        logger.info(
            "Recipient created successfully",
            recipient_id=recipient_id,
            name=name,
        )

        # Return response (remove DynamoDB keys)
        response_data = {k: v for k, v in recipient.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]}

        return success_response(response_data, status_code=201)

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
