"""
Lambda function: Create Distribution
POST /distributions - Create a new distribution record
"""
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()


def validate_distribution_input(data: Dict[str, Any]) -> None:
    """
    Validate distribution creation input

    Args:
        data: Request body data

    Raises:
        ValidationError: If validation fails
    """
    # Validate required fields
    Validator.validate_required_fields(data, ["recipient_id", "items", "distribution_date"])

    # Validate recipient_id
    Validator.validate_string(data["recipient_id"], "recipient_id", min_length=1)

    # Validate distribution_date (ISO format)
    Validator.validate_date(data["distribution_date"], "distribution_date")

    # Validate items (must be list with at least one item)
    items = Validator.validate_list(data["items"], "items", min_items=1)

    # Validate each item in the list
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError(
                message=f"Item at index {idx} must be an object", details={"index": idx}
            )

        # Validate required item fields
        if "donation_id" not in item:
            raise ValidationError(
                message=f"Item at index {idx} missing donation_id", details={"index": idx}
            )
        if "item_index" not in item:
            raise ValidationError(
                message=f"Item at index {idx} missing item_index", details={"index": idx}
            )
        if "quantity" not in item:
            raise ValidationError(
                message=f"Item at index {idx} missing quantity", details={"index": idx}
            )

        # Validate item fields
        Validator.validate_string(item["donation_id"], f"items[{idx}].donation_id", min_length=1)
        Validator.validate_number(item["item_index"], f"items[{idx}].item_index", min_value=0)
        Validator.validate_number(item["quantity"], f"items[{idx}].quantity", min_value=1)

    # Validate notes (optional)
    if "notes" in data and data["notes"]:
        Validator.validate_string(data["notes"], "notes", max_length=1000)


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for creating a new distribution

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Creating new distribution", path=event.get("path"))

        # Get user context
        user = get_user_from_event(event)
        logger.set_context(user_id=user.get("sub"), user_role=user.get("role"))

        # Parse and validate input
        body = event.get("body", "{}")
        data = json.loads(body) if isinstance(body, str) else body

        validate_distribution_input(data)

        # Generate distribution ID
        distribution_id = str(uuid.uuid4())

        # Prepare distribution items
        now = datetime.utcnow().isoformat()

        # Create METADATA item
        distribution_metadata = {
            "PK": f"DISTRIBUTION#{distribution_id}",
            "SK": "METADATA",
            "distribution_id": distribution_id,
            "recipient_id": data["recipient_id"],
            "items": data["items"],
            "distribution_date": data["distribution_date"],
            "status": "scheduled",
            "notes": data.get("notes", ""),
            "completed_at": None,
            "created_by": user.get("sub"),
            "created_at": now,
            "updated_at": now,
        }

        # Create RECIPIENT index item for GSI2
        distribution_recipient = {
            "PK": f"DISTRIBUTION#{distribution_id}",
            "SK": f"RECIPIENT#{data['recipient_id']}",
            "distribution_id": distribution_id,
            "recipient_id": data["recipient_id"],
            "distribution_date": data["distribution_date"],
            "status": "scheduled",
            # GSI1: ByDate
            "GSI1PK": "DISTRIBUTIONS",
            "GSI1SK": data["distribution_date"],
            # GSI2: ByRecipient
            "GSI2PK": f"RECIPIENT#{data['recipient_id']}",
            "GSI2SK": data["distribution_date"],
            "created_at": now,
            "updated_at": now,
        }

        # Store both items in DynamoDB
        db.put_item(distribution_metadata)
        db.put_item(distribution_recipient)

        logger.info(
            "Distribution created successfully",
            distribution_id=distribution_id,
            recipient_id=data["recipient_id"],
            items_count=len(data["items"]),
        )

        # Return response
        return success_response(
            data={
                "distribution_id": distribution_id,
                "recipient_id": data["recipient_id"],
                "items": data["items"],
                "distribution_date": data["distribution_date"],
                "status": "scheduled",
                "notes": data.get("notes", ""),
                "completed_at": None,
                "created_at": now,
                "updated_at": now,
            },
            status_code=201,
        )

    except SavingGraceError as e:
        logger.error("Distribution creation failed", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error creating distribution", error=e)
        return error_response(message="Internal server error", status_code=500)
