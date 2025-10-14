"""
Get Expiring Donations Lambda Function
GET /donations/expiring - List donation items expiring within N days
"""
import json
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from boto3.dynamodb.conditions import Key, Attr

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


def encode_pagination_token(last_key: Dict[str, Any]) -> str:
    """
    Encode DynamoDB LastEvaluatedKey as base64 token

    Args:
        last_key: DynamoDB LastEvaluatedKey

    Returns:
        Base64 encoded token
    """
    json_str = json.dumps(last_key)
    return base64.b64encode(json_str.encode()).decode()


def decode_pagination_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode base64 token to DynamoDB ExclusiveStartKey

    Args:
        token: Base64 encoded token

    Returns:
        Decoded key dict or None if invalid
    """
    try:
        json_str = base64.b64decode(token.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return None


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for getting expiring donation items

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Getting expiring donations", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}

        # Get days parameter (default 7)
        days = int(query_params.get("days", 7))

        # Validate days
        if days < 1 or days > 365:
            raise ValidationError(
                message="days must be between 1 and 365",
                details={"days": days}
            )

        # Pagination parameters
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", 50))
        next_token = query_params.get("next_token")

        # Validate pagination
        if page < 1:
            raise ValidationError(message="page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValidationError(message="page_size must be between 1 and 100")

        # Calculate date range
        now = datetime.utcnow()
        end_date = now + timedelta(days=days)

        # Format dates for comparison (ISO format)
        now_str = now.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        logger.info(
            "Querying expiring items",
            days=days,
            start_date=now_str,
            end_date=end_date_str
        )

        # Decode pagination token if provided
        exclusive_start_key = None
        if next_token:
            exclusive_start_key = decode_pagination_token(next_token)
            if not exclusive_start_key:
                raise ValidationError(message="Invalid next_token")

        # Query items expiring within the date range using GSI3 (ItemsByExpiration)
        key_condition = Key("GSI3PK").eq("ITEMS") & Key("GSI3SK").between(
            now_str, end_date_str
        )

        result = db.query(
            key_condition=key_condition,
            index_name="ItemsByExpiration",
            limit=page_size,
            exclusive_start_key=exclusive_start_key,
            scan_forward=True,  # Earliest expiration first
        )

        # Format response items
        expiring_items = []
        for item in result["items"]:
            expiring_items.append({
                "donation_id": item["donation_id"],
                "item_index": item["item_index"],
                "name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "expiration_date": item["expiration_date"],
            })

        # Prepare pagination token
        pagination_token = None
        if result["last_evaluated_key"]:
            pagination_token = encode_pagination_token(result["last_evaluated_key"])

        logger.info(
            "Retrieved expiring items",
            count=len(expiring_items),
            has_more=pagination_token is not None
        )

        return paginated_response(
            items=expiring_items,
            total_count=result["count"],
            page=page,
            page_size=page_size,
            next_token=pagination_token,
        )

    except SavingGraceError as e:
        logger.error("Failed to get expiring donations", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error getting expiring donations", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
