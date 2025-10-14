"""
List Inventory Lambda Function
GET /inventory

Lists all inventory items with pagination and optional filtering.
Requires Volunteer role (read-only access).
"""
import json
import os
from typing import Any, Dict, Optional

from lib.auth import require_permission, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response
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


@require_permission("inventory:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing inventory items

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with paginated items
    """
    try:
        # Log request
        user = get_user_from_event(event)
        logger.info("List inventory request", user_id=user.get("sub"), user_role=user.get("role"))

        # Extract query parameters
        query_params = event.get("queryStringParameters") or {}

        # Parse pagination parameters
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("page_size", "50"))

        # Validate pagination
        if page < 1:
            raise ValidationError(
                message="page must be at least 1", details={"field": "page", "value": page}
            )
        if page_size < 1 or page_size > 100:
            raise ValidationError(
                message="page_size must be between 1 and 100",
                details={"field": "page_size", "value": page_size},
            )

        # Parse filter parameters
        category_filter = query_params.get("category")
        min_quantity = query_params.get("min_quantity")

        # Validate category filter if provided
        if category_filter:
            category_filter = Validator.validate_enum(category_filter, "category", VALID_CATEGORIES)

        # Validate min_quantity if provided
        if min_quantity:
            min_quantity = Validator.validate_number(min_quantity, "min_quantity", min_value=0)

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Build filter expression
        from boto3.dynamodb.conditions import Key, Attr

        filter_expression = None
        if min_quantity is not None:
            filter_expression = Attr("quantity").gte(min_quantity)

        # Query or scan based on filters
        if category_filter:
            # Use query with category filter
            result = db.query(
                key_condition=Key("PK").eq(f"INVENTORY#{category_filter}"),
                filter_expression=filter_expression,
                limit=page_size * page,  # Get all items up to current page
            )
        else:
            # Scan all inventory items
            # Note: In production, consider using GSI for better performance
            filter_expr = Attr("PK").begins_with("INVENTORY#")
            if filter_expression:
                filter_expr = filter_expr & filter_expression

            result = db.scan(
                filter_expression=filter_expr,
                limit=page_size * page,  # Get all items up to current page
            )

        all_items = result.get("items", [])
        total_count = len(all_items)

        # Handle pagination manually
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_items[start_idx:end_idx]

        # Handle DynamoDB pagination for next page
        next_token = None
        if result.get("last_evaluated_key"):
            # Encode the last evaluated key as base64 for next page
            import base64

            next_token = base64.b64encode(
                json.dumps(result["last_evaluated_key"]).encode()
            ).decode()

        logger.info(
            "Listed inventory items",
            page=page,
            page_size=page_size,
            total_count=total_count,
            returned_count=len(paginated_items),
            category_filter=category_filter,
            min_quantity=min_quantity,
        )

        # Return paginated response
        return paginated_response(
            items=paginated_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            next_token=next_token,
        )

    except ValueError as e:
        logger.error("Invalid parameter value", error=e)
        return error_response(
            message="Invalid parameter value", status_code=400, details={"error": str(e)}
        )
    except SavingGraceError as e:
        logger.error("SavingGrace error in list inventory", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error in list inventory", error=e)
        return error_response(message="Internal server error", status_code=500)
