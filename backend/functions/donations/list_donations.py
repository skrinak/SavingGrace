"""
List Donations Lambda Function
GET /donations - List donations with filtering and pagination
"""
import json
import base64
from typing import Any, Dict, Optional

from boto3.dynamodb.conditions import Key, Attr

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response
from lib.validation import Validator

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()

# Valid donation statuses
VALID_STATUSES = ["pending", "received", "distributed"]


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
    Lambda handler for listing donations

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Listing donations", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}

        # Pagination parameters
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", 50))

        # Validate pagination
        if page < 1:
            raise ValidationError(message="page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValidationError(message="page_size must be between 1 and 100")

        # Filter parameters
        donor_id = query_params.get("donor_id")
        status = query_params.get("status")
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        next_token = query_params.get("next_token")

        # Validate status if provided
        if status and status not in VALID_STATUSES:
            raise ValidationError(
                message=f"status must be one of: {', '.join(VALID_STATUSES)}",
                details={"status": status}
            )

        # Validate dates if provided
        if start_date:
            Validator.validate_date(start_date, "start_date")
        if end_date:
            Validator.validate_date(end_date, "end_date")

        # Determine query strategy
        filter_expression = None
        exclusive_start_key = None

        if next_token:
            exclusive_start_key = decode_pagination_token(next_token)
            if not exclusive_start_key:
                raise ValidationError(message="Invalid next_token")

        if donor_id:
            # Query by donor using GSI1 (ByDonor)
            logger.info("Querying by donor", donor_id=donor_id)
            key_condition = Key("GSI1PK").eq(f"DONOR#{donor_id}")

            # Add date range to key condition if provided
            if start_date and end_date:
                key_condition = key_condition & Key("GSI1SK").between(start_date, end_date)
            elif start_date:
                key_condition = key_condition & Key("GSI1SK").gte(start_date)
            elif end_date:
                key_condition = key_condition & Key("GSI1SK").lte(end_date)

            # Add status filter
            if status:
                filter_expression = Attr("status").eq(status)

            result = db.query(
                key_condition=key_condition,
                filter_expression=filter_expression,
                index_name="ByDonor",
                limit=page_size,
                exclusive_start_key=exclusive_start_key,
                scan_forward=False,  # Most recent first
            )
        else:
            # Query all donations using GSI2 (ByDate)
            logger.info("Querying all donations")
            key_condition = Key("GSI2PK").eq("DONATIONS")

            # Add date range to key condition if provided
            if start_date and end_date:
                key_condition = key_condition & Key("GSI2SK").between(start_date, end_date)
            elif start_date:
                key_condition = key_condition & Key("GSI2SK").gte(start_date)
            elif end_date:
                key_condition = key_condition & Key("GSI2SK").lte(end_date)

            # Build filter expression for status and/or donor_id
            filters = []
            if status:
                filters.append(Attr("status").eq(status))

            if filters:
                filter_expression = filters[0]
                for f in filters[1:]:
                    filter_expression = filter_expression & f

            result = db.query(
                key_condition=key_condition,
                filter_expression=filter_expression,
                index_name="ByDate",
                limit=page_size,
                exclusive_start_key=exclusive_start_key,
                scan_forward=False,  # Most recent first
            )

        # Format response items
        donations = []
        for item in result["items"]:
            donations.append({
                "donation_id": item["donation_id"],
                "donor_id": item["donor_id"],
                "status": item["status"],
                "notes": item.get("notes"),
                "receipt_url": item.get("receipt_url"),
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
            })

        # Prepare pagination token
        pagination_token = None
        if result["last_evaluated_key"]:
            pagination_token = encode_pagination_token(result["last_evaluated_key"])

        logger.info(
            "Listed donations",
            count=len(donations),
            has_more=pagination_token is not None
        )

        # Note: total_count is approximate since we can't efficiently count with filters
        # For now, return the current count
        return paginated_response(
            items=donations,
            total_count=result["count"],
            page=page,
            page_size=page_size,
            next_token=pagination_token,
        )

    except SavingGraceError as e:
        logger.error("Failed to list donations", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error listing donations", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
