"""
Lambda function: Complete Distribution
POST /distributions/{distributionId}/complete - Mark distribution as completed and update inventory
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError, DatabaseError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()


def validate_completion_input(data: Dict[str, Any]) -> None:
    """
    Validate distribution completion input

    Args:
        data: Request body data

    Raises:
        ValidationError: If validation fails
    """
    # Validate actual_items (optional)
    if "actual_items" in data and data["actual_items"] is not None:
        items = Validator.validate_list(data["actual_items"], "actual_items")

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
            Validator.validate_string(
                item["donation_id"], f"actual_items[{idx}].donation_id", min_length=1
            )
            Validator.validate_number(
                item["item_index"], f"actual_items[{idx}].item_index", min_value=0
            )
            Validator.validate_number(
                item["quantity"], f"actual_items[{idx}].quantity", min_value=0
            )

    # Validate completion_notes (optional)
    if "completion_notes" in data and data["completion_notes"]:
        Validator.validate_string(data["completion_notes"], "completion_notes", max_length=1000)


def update_inventory(items_to_distribute: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Update inventory by decrementing quantities for distributed items

    Args:
        items_to_distribute: List of items being distributed

    Returns:
        List of inventory adjustments made

    Raises:
        DatabaseError: If inventory update fails
    """
    adjustments = []

    try:
        for item in items_to_distribute:
            donation_id = item["donation_id"]
            item_index = int(item["item_index"])
            quantity = int(item["quantity"])

            logger.info(
                "Updating inventory",
                donation_id=donation_id,
                item_index=item_index,
                quantity_distributed=quantity,
            )

            # Get the donation to access inventory
            pk = f"DONATION#{donation_id}"
            sk = "METADATA"

            try:
                donation = db.get_item(pk, sk)
            except Exception as e:
                logger.warning(
                    "Could not find donation for inventory update",
                    donation_id=donation_id,
                    error=str(e),
                )
                continue

            # Get the items array
            donation_items = donation.get("items", [])

            if item_index >= len(donation_items):
                logger.warning(
                    "Invalid item_index for donation",
                    donation_id=donation_id,
                    item_index=item_index,
                    items_count=len(donation_items),
                )
                continue

            # Update the quantity for the specific item
            current_quantity = donation_items[item_index].get("quantity", 0)
            new_quantity = max(0, current_quantity - quantity)

            # Log the adjustment
            adjustment = {
                "donation_id": donation_id,
                "item_index": item_index,
                "item_name": donation_items[item_index].get("item_name", "Unknown"),
                "previous_quantity": current_quantity,
                "distributed_quantity": quantity,
                "new_quantity": new_quantity,
            }
            adjustments.append(adjustment)

            # Update the item quantity
            donation_items[item_index]["quantity"] = new_quantity

            # Update the donation in DynamoDB
            db.update_item(pk, sk, {"items": donation_items})

            logger.info(
                "Inventory updated",
                donation_id=donation_id,
                item_index=item_index,
                item_name=donation_items[item_index].get("item_name"),
                previous_quantity=current_quantity,
                new_quantity=new_quantity,
            )

    except Exception as e:
        logger.error("Failed to update inventory", error=e)
        raise DatabaseError(message="Failed to update inventory", details={"error": str(e)})

    return adjustments


@require_role("Volunteer")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for completing a distribution

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Completing distribution", path=event.get("path"))

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

        validate_completion_input(data)

        logger.info("Completing distribution", distribution_id=distribution_id)

        # Get the distribution
        pk = f"DISTRIBUTION#{distribution_id}"
        sk = "METADATA"

        distribution = db.get_item(pk, sk)

        # Check if already completed
        if distribution.get("status") == "completed":
            raise ValidationError(
                message="Distribution is already completed",
                details={"distribution_id": distribution_id},
            )

        # Determine which items to use for inventory update
        # Use actual_items if provided, otherwise use the original items
        items_to_distribute = data.get("actual_items") or distribution.get("items", [])

        # Update inventory
        inventory_adjustments = update_inventory(items_to_distribute)

        # Update distribution status
        now = datetime.utcnow().isoformat()
        updates = {
            "status": "completed",
            "completed_at": now,
            "completed_by": user.get("sub"),
        }

        # Add actual_items if provided
        if "actual_items" in data:
            updates["actual_items"] = data["actual_items"]

        # Add completion_notes if provided
        if "completion_notes" in data:
            updates["completion_notes"] = data["completion_notes"]

        # Update METADATA item
        updated_distribution = db.update_item(pk, sk, updates)

        # Also update the RECIPIENT index item
        recipient_id = distribution.get("recipient_id")
        sk_recipient = f"RECIPIENT#{recipient_id}"
        db.update_item(pk, sk_recipient, {"status": "completed"})

        logger.info(
            "Distribution completed successfully",
            distribution_id=distribution_id,
            inventory_adjustments_count=len(inventory_adjustments),
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
            "completed_by": updated_distribution.get("completed_by"),
            "completion_notes": updated_distribution.get("completion_notes", ""),
            "actual_items": updated_distribution.get("actual_items"),
            "inventory_adjustments": inventory_adjustments,
            "created_at": updated_distribution.get("created_at"),
            "updated_at": updated_distribution.get("updated_at"),
        }

        return success_response(data=response_data)

    except SavingGraceError as e:
        logger.error("Failed to complete distribution", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error completing distribution", error=e)
        return error_response(message="Internal server error", status_code=500)
