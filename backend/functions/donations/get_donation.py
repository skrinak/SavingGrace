"""
Get Donation Lambda Function
GET /donations/{donationId} - Retrieve a donation by ID
"""
import os
from typing import Any, Dict

from boto3.dynamodb.conditions import Key

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, NotFoundError
from lib.logger import get_logger
from lib.responses import success_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for retrieving a donation

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Getting donation", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Get donation ID from path parameters
        path_params = event.get("pathParameters", {})
        donation_id = path_params.get("donationId")

        if not donation_id:
            raise NotFoundError(resource="Donation", resource_id="")

        # Query for all items with this donation ID
        pk = f"DONATION#{donation_id}"
        result = db.query(
            key_condition=Key("PK").eq(pk)
        )

        if not result["items"]:
            raise NotFoundError(resource="Donation", resource_id=donation_id)

        # Separate metadata and items
        metadata = None
        items = []

        for record in result["items"]:
            if record["SK"] == "METADATA":
                metadata = record
            elif record["SK"].startswith("ITEM#"):
                items.append(record)

        if not metadata:
            raise NotFoundError(resource="Donation", resource_id=donation_id)

        # Sort items by item_index
        items.sort(key=lambda x: x.get("item_index", 0))

        # Build response
        donation = {
            "donation_id": metadata["donation_id"],
            "donor_id": metadata["donor_id"],
            "status": metadata["status"],
            "notes": metadata.get("notes"),
            "receipt_url": metadata.get("receipt_url"),
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"],
            "items": [
                {
                    "name": item["name"],
                    "category": item["category"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "expiration_date": item.get("expiration_date"),
                }
                for item in items
            ],
        }

        logger.info("Retrieved donation", donation_id=donation_id, item_count=len(items))

        return success_response(donation)

    except SavingGraceError as e:
        logger.error("Failed to get donation", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error getting donation", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
