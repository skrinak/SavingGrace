"""
Get Inventory by Category Lambda Function
GET /inventory/{category}

Retrieves all inventory items for a specific category.
Requires Volunteer role (read-only access).
"""
import json
import os
from typing import Any, Dict

from lib.auth import require_permission, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
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
    "other"
]


@require_permission("inventory:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for getting inventory by category

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        user = get_user_from_event(event)
        logger.info(
            "Get inventory by category request",
            user_id=user.get("sub"),
            user_role=user.get("role")
        )

        # Extract category from path parameters
        path_params = event.get("pathParameters", {})
        category = path_params.get("category")

        if not category:
            raise ValidationError(
                message="Category is required",
                details={"field": "category"}
            )

        # Validate category
        category = Validator.validate_enum(
            category,
            "category",
            VALID_CATEGORIES
        )

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Query items for this category
        # PK = INVENTORY#{category}
        from boto3.dynamodb.conditions import Key

        result = db.query(
            key_condition=Key("PK").eq(f"INVENTORY#{category}")
        )

        items = result.get("items", [])

        logger.info(
            "Retrieved inventory items",
            category=category,
            item_count=len(items)
        )

        # Return items for this category
        return success_response({
            "category": category,
            "items": items,
            "count": len(items)
        })

    except SavingGraceError as e:
        logger.error(
            "SavingGrace error in get inventory by category",
            error=e,
            error_code=e.error_code
        )
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        logger.error(
            "Unexpected error in get inventory by category",
            error=e
        )
        return error_response(
            message="Internal server error",
            status_code=500
        )
