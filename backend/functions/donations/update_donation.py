"""
Update Donation Lambda Function
PUT /donations/{donationId} - Update donation metadata
"""
import json
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, NotFoundError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()

# Valid donation statuses
VALID_STATUSES = ["pending", "received", "distributed"]


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for updating a donation

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Updating donation", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Get donation ID from path parameters
        path_params = event.get("pathParameters", {})
        donation_id = path_params.get("donationId")

        if not donation_id:
            raise NotFoundError(resource="Donation", resource_id="")

        # Parse and validate request body
        body = event.get("body", "{}")
        data = json.loads(body) if isinstance(body, str) else body

        # Check if donation exists
        pk = f"DONATION#{donation_id}"
        sk = "METADATA"

        try:
            existing = db.get_item(pk, sk)
        except NotFoundError:
            raise NotFoundError(resource="Donation", resource_id=donation_id)

        # Build updates dictionary
        updates = {}

        # Validate and update status if provided
        if "status" in data:
            status = Validator.validate_enum(data["status"], "status", VALID_STATUSES)
            updates["status"] = status

        # Validate and update notes if provided
        if "notes" in data:
            if data["notes"] is None:
                updates["notes"] = None
            else:
                notes = Validator.validate_string(data["notes"], "notes", max_length=2000)
                updates["notes"] = notes

        # Ensure at least one field is being updated
        if not updates:
            return error_response(
                message="No valid fields to update",
                status_code=400,
            )

        # Update the item in DynamoDB
        updated_item = db.update_item(pk, sk, updates)

        # Build response
        donation = {
            "donation_id": updated_item["donation_id"],
            "donor_id": updated_item["donor_id"],
            "status": updated_item["status"],
            "notes": updated_item.get("notes"),
            "receipt_url": updated_item.get("receipt_url"),
            "created_at": updated_item["created_at"],
            "updated_at": updated_item["updated_at"],
        }

        logger.info(
            "Updated donation",
            donation_id=donation_id,
            updated_fields=list(updates.keys())
        )

        return success_response(donation)

    except SavingGraceError as e:
        logger.error("Failed to update donation", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error updating donation", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
