"""
Lambda function: GET /reports/donations
Get donations report with aggregation by donor, category, or date
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


def aggregate_by_donor(donations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate donations by donor

    Args:
        donations: List of donation items

    Returns:
        List of aggregated results by donor
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "donor_id": None,
            "donor_name": None,
            "total_donations": 0,
            "total_items": 0,
            "total_weight_lbs": Decimal("0"),
        }
    )

    for donation in donations:
        donor_id = donation.get("donor_id")
        if not donor_id:
            continue

        agg = aggregated[donor_id]
        agg["donor_id"] = donor_id
        agg["donor_name"] = donation.get("donor_name", "Unknown")
        agg["total_donations"] += 1
        agg["total_items"] += donation.get("total_items", 0)
        agg["total_weight_lbs"] += Decimal(str(donation.get("total_weight_lbs", 0)))

    return list(aggregated.values())


def aggregate_by_category(donations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate donations by category

    Args:
        donations: List of donation items

    Returns:
        List of aggregated results by category
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "category": None,
            "total_donations": 0,
            "total_quantity": 0,
            "total_weight_lbs": Decimal("0"),
        }
    )

    for donation in donations:
        # Get items from donation
        items = donation.get("items", [])
        for item in items:
            category = item.get("category", "uncategorized")
            agg = aggregated[category]
            agg["category"] = category
            agg["total_donations"] += 1
            agg["total_quantity"] += item.get("quantity", 0)
            agg["total_weight_lbs"] += Decimal(str(item.get("weight_lbs", 0)))

    return list(aggregated.values())


def aggregate_by_date(donations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate donations by date

    Args:
        donations: List of donation items

    Returns:
        List of aggregated results by date
    """
    aggregated: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "date": None,
            "total_donations": 0,
            "total_items": 0,
            "total_weight_lbs": Decimal("0"),
        }
    )

    for donation in donations:
        # Extract date from created_at timestamp
        created_at = donation.get("created_at", "")
        if created_at:
            date = created_at.split("T")[0]  # Get YYYY-MM-DD
        else:
            date = "unknown"

        agg = aggregated[date]
        agg["date"] = date
        agg["total_donations"] += 1
        agg["total_items"] += donation.get("total_items", 0)
        agg["total_weight_lbs"] += Decimal(str(donation.get("total_weight_lbs", 0)))

    # Sort by date
    result = list(aggregated.values())
    result.sort(key=lambda x: x["date"], reverse=True)
    return result


@require_permission("reports:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get donations report with aggregation

    Query Parameters:
        - start_date (optional): Start date in ISO format (default: 30 days ago)
        - end_date (optional): End date in ISO format (default: now)
        - group_by (optional): Group by donor, category, or date (default: date)

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with aggregated donation report
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
        group_by = Validator.validate_enum(group_by, "group_by", ["donor", "category", "date"])

        logger.info(
            "Fetching donations report", start_date=start_date, end_date=end_date, group_by=group_by
        )

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Query donations within date range
        # Using scan with filter for date range (in production, consider GSI)
        response = db.scan(
            filter_expression=Attr("PK").begins_with("DONATION#")
            & Attr("SK").eq("METADATA")
            & Attr("created_at").between(start_date, end_date)
        )

        donations = response["items"]

        logger.info(f"Found {len(donations)} donations in date range")

        # Aggregate based on group_by parameter
        if group_by == "donor":
            aggregated_data = aggregate_by_donor(donations)
        elif group_by == "category":
            aggregated_data = aggregate_by_category(donations)
        else:  # date
            aggregated_data = aggregate_by_date(donations)

        result = {
            "report_type": "donations",
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by,
            "total_donations": len(donations),
            "data": aggregated_data,
        }

        logger.info("Donations report generated successfully")

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
