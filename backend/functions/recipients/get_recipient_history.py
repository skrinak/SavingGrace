"""
Get Recipient History Lambda Function
GET /recipients/{recipientId}/history
Retrieves distribution history for a specific recipient
"""
import os
from typing import Any, Dict
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, NotFoundError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get distribution history for a recipient

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with paginated distribution history
    """
    try:
        # Get recipient ID from path parameters
        recipient_id = event.get("pathParameters", {}).get("recipientId")

        if not recipient_id:
            return error_response(
                message="Recipient ID is required",
                status_code=400,
            )

        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("page_size", "50"))
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")

        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        # Log request
        logger.log_api_request(
            method=event.get("httpMethod"),
            path=event.get("path"),
            user_id=get_user_from_event(event).get("sub"),
            recipient_id=recipient_id,
            page=page,
            page_size=page_size,
        )

        # Check if recipient exists
        try:
            db.get_item(pk=f"RECIPIENT#{recipient_id}", sk="PROFILE")
        except NotFoundError:
            return error_response(
                message=f"Recipient with ID '{recipient_id}' not found",
                status_code=404,
                error_code="NOT_FOUND",
            )

        # Query distributions using GSI2 (ByRecipient)
        # GSI2PK = RECIPIENT#{recipient_id}, GSI2SK = distribution_date
        key_condition = Key("GSI2PK").eq(f"RECIPIENT#{recipient_id}")

        # Add date range filter if provided
        filter_expr = None
        if start_date and end_date:
            # Filter by date range on GSI2SK (distribution_date)
            key_condition = key_condition & Key("GSI2SK").between(start_date, end_date)
        elif start_date:
            # Filter from start_date onwards
            key_condition = key_condition & Key("GSI2SK").gte(start_date)
        elif end_date:
            # Filter up to end_date
            key_condition = key_condition & Key("GSI2SK").lte(end_date)

        # Query with pagination
        result = db.query(
            key_condition=key_condition,
            filter_expression=filter_expr,
            index_name="GSI2",
            limit=page_size * page,  # Get enough items for pagination
            scan_forward=False,  # Most recent first
        )

        all_items = result["items"]

        # Manual pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = all_items[start_idx:end_idx]
        total_count = len(all_items)

        # Clean up response data (remove DynamoDB keys)
        distributions = [
            {
                k: v
                for k, v in item.items()
                if k not in ["PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK"]
            }
            for item in items
        ]

        logger.info(
            "Recipient history retrieved successfully",
            recipient_id=recipient_id,
            count=len(distributions),
            total_count=total_count,
        )

        return paginated_response(
            items=distributions,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except SavingGraceError as e:
        logger.error("Application error", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
