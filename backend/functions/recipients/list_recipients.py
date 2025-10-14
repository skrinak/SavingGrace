"""
List Recipients Lambda Function
GET /recipients
Lists all recipients with pagination and optional search
"""
import os
from typing import Any, Dict
from boto3.dynamodb.conditions import Attr

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List recipients with pagination

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with paginated recipients list
    """
    try:
        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("page_size", "50"))
        search = query_params.get("search", "").strip()

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
            page=page,
            page_size=page_size,
            search=search,
        )

        # If search provided, use scan with filter
        if search:
            # Build filter expression for searching in name or contact_name
            filter_expr = (
                Attr("name").contains(search)
                | Attr("contact_name").contains(search)
                | Attr("contact_phone").contains(search)
            )
            # Also filter to only get recipient profiles
            filter_expr = filter_expr & Attr("SK").eq("PROFILE")

            # Scan with filter
            result = db.scan(
                filter_expression=filter_expr,
                limit=page_size * page,  # Get enough items for pagination
            )

            all_items = result["items"]

            # Manual pagination for scan results
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            items = all_items[start_idx:end_idx]
            total_count = len(all_items)

        else:
            # Use GSI1 to get all recipients efficiently
            from boto3.dynamodb.conditions import Key

            result = db.query(
                key_condition=Key("GSI1PK").eq("RECIPIENTS"),
                index_name="GSI1",
                limit=page_size * page,  # Get enough items for pagination
            )

            all_items = result["items"]

            # Manual pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            items = all_items[start_idx:end_idx]
            total_count = len(all_items)

        # Clean up response data (remove DynamoDB keys)
        recipients = [
            {k: v for k, v in item.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]}
            for item in items
        ]

        logger.info(
            "Recipients listed successfully",
            count=len(recipients),
            total_count=total_count,
            page=page,
        )

        return paginated_response(
            items=recipients,
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
