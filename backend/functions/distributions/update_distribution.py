"""
Lambda function: Update Distribution
PUT /distributions/{distributionId} - Update a distribution
"""
import json
import os
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

# Valid distribution statuses
VALID_STATUSES = ["scheduled", "in_progress", "completed", "cancelled"]


def validate_update_input(data: Dict[str, Any]) -> None:
    """
    Validate distribution update input

    Args:
        data: Request body data

    Raises:
        ValidationError: If validation fails
    """
    # At least one field must be provided
    if not any(key in data for key in ["status", "distribution_date", "notes"]):
        raise ValidationError(
            message="At least one field to update must be provided",
            details={"allowed_fields": ["status", "distribution_date", "notes"]},
        )

    # Validate status (optional)
    if "status" in data:
        Validator.validate_enum(data["status"], "status", VALID_STATUSES)

    # Validate distribution_date (optional)
    if "distribution_date" in data:
        Validator.validate_date(data["distribution_date"], "distribution_date")

    # Validate notes (optional)
    if "notes" in data and data["notes"]:
        Validator.validate_string(data["notes"], "notes", max_length=1000)


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating a distribution

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Updating distribution", path=event.get("path"))

        # Get user context
        user = get_user_from_event(event)
        logger.set_context(user_id=user.get("sub"), user_role=user.get("role"))

        # Get distribution ID from path parameters
        path_params = event.get("pathParameters", {})
        distribution_id = path_params.get("distributionId")

        if not distribution_id:
            raise ValidationError(
                message="Missing distributionId in path", details={"parameter": "distributionId"}
            )

        # Validate distribution_id format
        Validator.validate_string(distribution_id, "distributionId", min_length=1)

        # Parse and validate input
        body = event.get("body", "{}")
        data = json.loads(body) if isinstance(body, str) else body

        validate_update_input(data)

        logger.info(
            "Updating distribution", distribution_id=distribution_id, updates=list(data.keys())
        )

        # Prepare updates
        pk = f"DISTRIBUTION#{distribution_id}"
        sk = "METADATA"

        updates = {}

        # Add fields to update
        if "status" in data:
            updates["status"] = data["status"]
        if "distribution_date" in data:
            updates["distribution_date"] = data["distribution_date"]
        if "notes" in data:
            updates["notes"] = data["notes"]

        # Update METADATA item
        updated_distribution = db.update_item(pk, sk, updates)

        # Also update the RECIPIENT index item if distribution_date or status changed
        if "distribution_date" in data or "status" in data:
            recipient_id = updated_distribution.get("recipient_id")
            sk_recipient = f"RECIPIENT#{recipient_id}"

            recipient_updates = {}
            if "distribution_date" in data:
                recipient_updates["distribution_date"] = data["distribution_date"]
                recipient_updates["GSI1SK"] = data["distribution_date"]
                recipient_updates["GSI2SK"] = data["distribution_date"]
            if "status" in data:
                recipient_updates["status"] = data["status"]

            if recipient_updates:
                db.update_item(pk, sk_recipient, recipient_updates)

        logger.info(
            "Distribution updated successfully",
            distribution_id=distribution_id,
            status=updated_distribution.get("status"),
        )

        # Prepare response
        response_data = {
            "distribution_id": updated_distribution.get("distribution_id"),
            "recipient_id": updated_distribution.get("recipient_id"),
            "items": updated_distribution.get("items", []),
            "distribution_date": updated_distribution.get("distribution_date"),
            "status": updated_distribution.get("status"),
            "notes": updated_distribution.get("notes", ""),
            "completed_at": updated_distribution.get("completed_at"),
            "created_at": updated_distribution.get("created_at"),
            "updated_at": updated_distribution.get("updated_at"),
        }

        return success_response(data=response_data)

    except SavingGraceError as e:
        logger.error("Failed to update distribution", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error updating distribution", error=e)
        return error_response(message="Internal server error", status_code=500)
