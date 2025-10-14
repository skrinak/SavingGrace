"""
Lambda function: GET /reports/distributions
Get distributions report with aggregation by recipient, date, or status
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List
from collections import defaultdict
from decimal import Decimal

from lib.auth import require_permission
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator
from boto3.dynamodb.conditions import Key, Attr

# Initialize logger
logger = get_logger(__name__)


def aggregate_by_recipient(distributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate distributions by recipient

    Args:
        distributions: List of distribution items

    Returns:
        List of aggregated results by recipient
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "recipient_id": None,
            "recipient_name": None,
            "total_distributions": 0,
            "total_items": 0,
            "completed_distributions": 0,
            "pending_distributions": 0,
        }
    )

    for distribution in distributions:
        recipient_id = distribution.get("recipient_id")
        if not recipient_id:
            continue

        agg = aggregated[recipient_id]
        agg["recipient_id"] = recipient_id
        agg["recipient_name"] = distribution.get("recipient_name", "Unknown")
        agg["total_distributions"] += 1
        agg["total_items"] += distribution.get("total_items", 0)

        status = distribution.get("status", "")
        if status == "completed":
            agg["completed_distributions"] += 1
        elif status in ["pending", "scheduled"]:
            agg["pending_distributions"] += 1

    return list(aggregated.values())


def aggregate_by_date(distributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate distributions by date

    Args:
        distributions: List of distribution items

    Returns:
        List of aggregated results by date
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "date": None,
            "total_distributions": 0,
            "total_items": 0,
            "completed_distributions": 0,
            "pending_distributions": 0,
        }
    )

    for distribution in distributions:
        # Extract date from scheduled_date or created_at timestamp
        scheduled_date = distribution.get("scheduled_date", "")
        if scheduled_date:
            date = scheduled_date.split("T")[0]  # Get YYYY-MM-DD
        else:
            created_at = distribution.get("created_at", "")
            date = created_at.split("T")[0] if created_at else "unknown"

        agg = aggregated[date]
        agg["date"] = date
        agg["total_distributions"] += 1
        agg["total_items"] += distribution.get("total_items", 0)

        status = distribution.get("status", "")
        if status == "completed":
            agg["completed_distributions"] += 1
        elif status in ["pending", "scheduled"]:
            agg["pending_distributions"] += 1

    # Sort by date
    result = list(aggregated.values())
    result.sort(key=lambda x: x["date"], reverse=True)
    return result


def aggregate_by_status(distributions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate distributions by status

    Args:
        distributions: List of distribution items

    Returns:
        List of aggregated results by status
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "status": None,
            "total_distributions": 0,
            "total_items": 0,
            "total_recipients": set(),
        }
    )

    for distribution in distributions:
        status = distribution.get("status", "unknown")

        agg = aggregated[status]
        agg["status"] = status
        agg["total_distributions"] += 1
        agg["total_items"] += distribution.get("total_items", 0)

        recipient_id = distribution.get("recipient_id")
        if recipient_id:
            agg["total_recipients"].add(recipient_id)

    # Convert sets to counts
    result = []
    for item in aggregated.values():
        item["total_recipients"] = len(item["total_recipients"])
        result.append(item)

    return result


@require_permission("reports:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get distributions report with aggregation

    Query Parameters:
        - start_date (optional): Start date in ISO format (default: 30 days ago)
        - end_date (optional): End date in ISO format (default: now)
        - group_by (optional): Group by recipient, date, or status (default: date)

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with aggregated distribution report
    """
    try:
        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}

        # Get date range (default to last 30 days)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        start_date_str = query_params.get("start_date")
        end_date_str = query_params.get("end_date")

        if start_date_str:
            start_date = Validator.validate_date(start_date_str, "start_date")
        else:
            start_date = thirty_days_ago.isoformat()

        if end_date_str:
            end_date = Validator.validate_date(end_date_str, "end_date")
        else:
            end_date = now.isoformat()

        # Get group_by parameter
        group_by = query_params.get("group_by", "date")
        group_by = Validator.validate_enum(group_by, "group_by", ["recipient", "date", "status"])

        logger.info(
            "Fetching distributions report",
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Query distributions within date range
        # Using scan with filter for date range (in production, consider GSI)
        response = db.scan(
            filter_expression=Attr("PK").begins_with("DISTRIBUTION#")
            & Attr("SK").eq("METADATA")
            & Attr("created_at").between(start_date, end_date)
        )

        distributions = response["items"]

        logger.info(f"Found {len(distributions)} distributions in date range")

        # Aggregate based on group_by parameter
        if group_by == "recipient":
            aggregated_data = aggregate_by_recipient(distributions)
        elif group_by == "status":
            aggregated_data = aggregate_by_status(distributions)
        else:  # date
            aggregated_data = aggregate_by_date(distributions)

        result = {
            "report_type": "distributions",
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "total_distributions": len(distributions),
            "data": aggregated_data,
        }

        logger.info("Distributions report generated successfully")

        return success_response(result)

    except SavingGraceError as e:
        logger.error("SavingGrace error occurred", error=e)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error occurred", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
