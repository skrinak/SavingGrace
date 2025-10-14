"""
Create Donation Lambda Function
POST /donations - Create a new donation record
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

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


def validate_donation_items(items: list) -> None:
    """
    Validate donation items structure

    Args:
        items: List of donation items

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(items, list):
        raise ValidationError(
            message="items must be a list",
            details={"type": type(items).__name__}
        )

    if len(items) == 0:
        raise ValidationError(
            message="items list cannot be empty",
            details={"min_items": 1}
        )

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError(
                message=f"Item at index {idx} must be a dictionary",
                details={"index": idx}
            )

        # Validate required fields
        required_fields = ["name", "category", "quantity", "unit"]
        for field in required_fields:
            if field not in item:
                raise ValidationError(
                    message=f"Item at index {idx} missing required field: {field}",
                    details={"index": idx, "missing_field": field}
                )

        # Validate field types and values
        Validator.validate_string(item["name"], f"items[{idx}].name", min_length=1, max_length=200)
        Validator.validate_string(item["category"], f"items[{idx}].category", min_length=1, max_length=100)
        Validator.validate_number(item["quantity"], f"items[{idx}].quantity", min_value=0)
        Validator.validate_string(item["unit"], f"items[{idx}].unit", min_length=1, max_length=50)

        # Validate expiration_date if provided
        if "expiration_date" in item:
            Validator.validate_date(item["expiration_date"], f"items[{idx}].expiration_date")


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for creating a donation

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Creating donation", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Parse and validate request body
        body = event.get("body", "{}")
        data = json.loads(body) if isinstance(body, str) else body

        # Validate required fields
        Validator.validate_required_fields(data, ["donor_id", "items"])

        # Validate fields
        donor_id = Validator.validate_string(data["donor_id"], "donor_id", min_length=1)
        items = data["items"]
        validate_donation_items(items)

        # Optional fields
        notes = None
        if "notes" in data:
            notes = Validator.validate_string(data["notes"], "notes", max_length=2000)

        receipt_url = None
        if "receipt_url" in data:
            receipt_url = Validator.validate_string(data["receipt_url"], "receipt_url", max_length=500)

        # Generate donation ID
        donation_id = str(uuid.uuid4())

        # Prepare timestamp
        now = datetime.utcnow().isoformat()

        # Create metadata item
        metadata_item = {
            "PK": f"DONATION#{donation_id}",
            "SK": "METADATA",
            "donation_id": donation_id,
            "donor_id": donor_id,
            "status": "pending",
            "notes": notes,
            "receipt_url": receipt_url,
            "created_by": user["sub"],
            "created_at": now,
            "updated_at": now,
            # GSI attributes
            "GSI1PK": f"DONOR#{donor_id}",
            "GSI1SK": now,
            "GSI2PK": "DONATIONS",
            "GSI2SK": now,
        }

        # Store metadata
        db.put_item(metadata_item)
        logger.info("Created donation metadata", donation_id=donation_id)

        # Store each item
        donation_items = []
        for idx, item in enumerate(items):
            item_record = {
                "PK": f"DONATION#{donation_id}",
                "SK": f"ITEM#{idx:04d}",
                "donation_id": donation_id,
                "item_index": idx,
                "name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "expiration_date": item.get("expiration_date"),
                "created_at": now,
                "updated_at": now,
            }

            # Add to GSI3 if expiration_date exists
            if item.get("expiration_date"):
                item_record["GSI3PK"] = "ITEMS"
                item_record["GSI3SK"] = item["expiration_date"]

            db.put_item(item_record)
            donation_items.append({
                "name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "expiration_date": item.get("expiration_date"),
            })

        logger.info("Created donation items", donation_id=donation_id, item_count=len(items))

        # Build response
        donation = {
            "donation_id": donation_id,
            "donor_id": donor_id,
            "status": "pending",
            "notes": notes,
            "receipt_url": receipt_url,
            "items": donation_items,
            "created_at": now,
            "updated_at": now,
        }

        return success_response(donation, status_code=201)

    except SavingGraceError as e:
        logger.error("Donation creation failed", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error creating donation", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
