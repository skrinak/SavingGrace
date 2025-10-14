"""
Adjust Inventory Lambda Function
POST /inventory/adjust

Adjusts inventory quantities (increment or decrement).
Requires DonorCoordinator or DistributionManager role.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict

from lib.auth import get_user_from_event, AuthHelper
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError, AuthorizationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize logger
logger = get_logger(__name__)

# Valid inventory categories
VALID_CATEGORIES = [
    "produce",
    "dairy",
    "protein",
    "grains",
    "canned",
    "frozen",
    "beverages",
    "other",
]

# Valid adjustment reasons
VALID_REASONS = ["donation", "distribution", "expired", "damaged", "other"]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for adjusting inventory

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Get user and check permissions
        user = get_user_from_event(event)
        user_role = user.get("role", "ReadOnly")

        # Check if user has DonorCoordinator OR DistributionManager permission
        has_donor_coord = AuthHelper.has_permission(user_role, "inventory:adjust")
        if not has_donor_coord:
            raise AuthorizationError(
                message="DonorCoordinator or DistributionManager role required",
                required_role="DonorCoordinator",
            )

        logger.info("Adjust inventory request", user_id=user.get("sub"), user_role=user_role)

        # Parse request body
        try:
            body = event.get("body", "{}")
            data = json.loads(body) if isinstance(body, str) else body
        except json.JSONDecodeError:
            raise ValidationError(message="Invalid JSON in request body")

        # Validate required fields
        required_fields = ["category", "item_name", "quantity_change", "reason"]
        Validator.validate_required_fields(data, required_fields)

        # Validate and extract fields
        category = Validator.validate_enum(data["category"], "category", VALID_CATEGORIES)

        item_name = Validator.validate_string(
            data["item_name"], "item_name", min_length=1, max_length=200
        )

        quantity_change = Validator.validate_number(data["quantity_change"], "quantity_change")

        reason = Validator.validate_enum(data["reason"], "reason", VALID_REASONS)

        # Optional fields
        notes = data.get("notes", "")
        if notes:
            notes = Validator.validate_string(notes, "notes", max_length=500)

        unit = data.get("unit", "units")
        if unit:
            unit = Validator.validate_string(unit, "unit", max_length=50)

        expiration_date = data.get("expiration_date")
        if expiration_date:
            expiration_date = Validator.validate_date(expiration_date, "expiration_date")

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Try to find existing item by category and name
        # We need to query for items with this category and name
        from boto3.dynamodb.conditions import Key, Attr

        query_result = db.query(
            key_condition=Key("PK").eq(f"INVENTORY#{category}"),
            filter_expression=Attr("name").eq(item_name),
        )

        existing_items = query_result.get("items", [])

        now = datetime.utcnow().isoformat()

        if existing_items:
            # Update existing item
            existing_item = existing_items[0]
            item_id = existing_item["item_id"]
            current_quantity = existing_item.get("quantity", 0)
            new_quantity = current_quantity + quantity_change

            # Don't allow negative quantities
            if new_quantity < 0:
                new_quantity = 0

            # Update the item
            updated_item = db.update_item(
                pk=f"INVENTORY#{category}",
                sk=f"ITEM#{item_id}",
                updates={
                    "quantity": new_quantity,
                    "unit": unit,
                    "last_adjusted": now,
                },
            )

            # Update expiration date if provided
            if expiration_date:
                updated_item = db.update_item(
                    pk=f"INVENTORY#{category}",
                    sk=f"ITEM#{item_id}",
                    updates={
                        "expiration_date": expiration_date,
                        "GSI1PK": "INVENTORY",
                        "GSI1SK": expiration_date,
                    },
                )

            logger.info(
                "Updated existing inventory item",
                item_id=item_id,
                category=category,
                item_name=item_name,
                old_quantity=current_quantity,
                new_quantity=new_quantity,
                quantity_change=quantity_change,
                reason=reason,
            )

        else:
            # Create new item
            item_id = str(uuid.uuid4())
            new_quantity = max(0, quantity_change)  # Don't allow negative initial quantity

            new_item = {
                "PK": f"INVENTORY#{category}",
                "SK": f"ITEM#{item_id}",
                "item_id": item_id,
                "category": category,
                "name": item_name,
                "quantity": new_quantity,
                "unit": unit,
                "last_adjusted": now,
                "created_at": now,
                "updated_at": now,
            }

            # Add GSI attributes for ByCategory
            new_item["GSI2PK"] = f"CATEGORY#{category}"
            new_item["GSI2SK"] = item_name

            # Add GSI attributes for ByExpiration if expiration date provided
            if expiration_date:
                new_item["expiration_date"] = expiration_date
                new_item["GSI1PK"] = "INVENTORY"
                new_item["GSI1SK"] = expiration_date

            updated_item = db.put_item(new_item)

            logger.info(
                "Created new inventory item",
                item_id=item_id,
                category=category,
                item_name=item_name,
                quantity=new_quantity,
                reason=reason,
            )

        # Log the adjustment for audit trail
        audit_log_entry = {
            "PK": f"AUDIT#INVENTORY#{updated_item['item_id']}",
            "SK": f"ADJUSTMENT#{now}",
            "item_id": updated_item["item_id"],
            "category": category,
            "item_name": item_name,
            "quantity_change": quantity_change,
            "reason": reason,
            "notes": notes,
            "adjusted_by": user.get("sub"),
            "adjusted_by_email": user.get("email"),
            "timestamp": now,
        }
        db.put_item(audit_log_entry)

        logger.info(
            "Logged inventory adjustment",
            item_id=updated_item["item_id"],
            adjusted_by=user.get("email"),
        )

        # Return updated item
        return success_response(
            {
                "item": updated_item,
                "adjustment": {
                    "quantity_change": quantity_change,
                    "reason": reason,
                    "notes": notes,
                    "adjusted_by": user.get("email"),
                    "timestamp": now,
                },
            }
        )

    except SavingGraceError as e:
        logger.error("SavingGrace error in adjust inventory", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error in adjust inventory", error=e)
        return error_response(message="Internal server error", status_code=500)
