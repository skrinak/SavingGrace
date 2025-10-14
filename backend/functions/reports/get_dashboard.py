"""
Lambda function: GET /reports/dashboard
Get dashboard metrics with aggregate statistics
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict

from lib.auth import require_permission
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from boto3.dynamodb.conditions import Key, Attr

# Initialize logger
logger = get_logger(__name__)


@require_permission("reports:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get dashboard metrics with aggregate statistics

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with dashboard metrics
    """
    try:
        logger.info("Fetching dashboard metrics")

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Get current date for time-based queries
        now = datetime.utcnow()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()
        seven_days_from_now = (now + timedelta(days=7)).isoformat()

        # Initialize metrics
        metrics = {
            "total_donors": 0,
            "total_donations": 0,
            "total_distributions": 0,
            "active_recipients": 0,
            "current_inventory_items": 0,
            "low_stock_count": 0,
            "expiring_soon_count": 0,
        }

        # Count total donors (PK starts with DONOR#)
        try:
            donor_response = db.scan(
                filter_expression=Attr("PK").begins_with("DONOR#") & Attr("SK").eq("METADATA")
            )
            metrics["total_donors"] = donor_response["count"]
        except Exception as e:
            logger.error("Failed to count donors", error=e)

        # Count total donations (PK starts with DONATION#)
        try:
            donation_response = db.scan(
                filter_expression=Attr("PK").begins_with("DONATION#") & Attr("SK").eq("METADATA")
            )
            metrics["total_donations"] = donation_response["count"]
        except Exception as e:
            logger.error("Failed to count donations", error=e)

        # Count total distributions (PK starts with DISTRIBUTION#)
        try:
            distribution_response = db.scan(
                filter_expression=Attr("PK").begins_with("DISTRIBUTION#") & Attr("SK").eq("METADATA")
            )
            metrics["total_distributions"] = distribution_response["count"]
        except Exception as e:
            logger.error("Failed to count distributions", error=e)

        # Count active recipients (status = active)
        try:
            recipient_response = db.scan(
                filter_expression=Attr("PK").begins_with("RECIPIENT#") &
                                Attr("SK").eq("METADATA") &
                                Attr("status").eq("active")
            )
            metrics["active_recipients"] = recipient_response["count"]
        except Exception as e:
            logger.error("Failed to count active recipients", error=e)

        # Count current inventory items (PK starts with INVENTORY#)
        try:
            inventory_response = db.scan(
                filter_expression=Attr("PK").begins_with("INVENTORY#") &
                                Attr("SK").eq("METADATA") &
                                Attr("quantity").gt(0)
            )
            metrics["current_inventory_items"] = inventory_response["count"]
        except Exception as e:
            logger.error("Failed to count inventory items", error=e)

        # Count low stock items (quantity <= reorder_point)
        try:
            low_stock_response = db.scan(
                filter_expression=Attr("PK").begins_with("INVENTORY#") &
                                Attr("SK").eq("METADATA") &
                                Attr("quantity").lte(Attr("reorder_point"))
            )
            metrics["low_stock_count"] = low_stock_response["count"]
        except Exception as e:
            logger.error("Failed to count low stock items", error=e)

        # Count expiring soon items (expiration_date within next 7 days)
        try:
            expiring_response = db.scan(
                filter_expression=Attr("PK").begins_with("DONATION#") &
                                Attr("SK").begins_with("ITEM#") &
                                Attr("expiration_date").lte(seven_days_from_now) &
                                Attr("expiration_date").gte(now.isoformat()) &
                                Attr("status").eq("available")
            )
            metrics["expiring_soon_count"] = expiring_response["count"]
        except Exception as e:
            logger.error("Failed to count expiring items", error=e)

        logger.info("Dashboard metrics retrieved successfully", metrics=metrics)

        return success_response(metrics)

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
