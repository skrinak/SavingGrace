"""
Get Inventory Alerts Lambda Function
GET /inventory/alerts

Retrieves inventory alerts for low stock, expiring soon, and expired items.
Requires DonorCoordinator role.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

from lib.auth import require_permission, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize logger
logger = get_logger(__name__)

# Valid alert types
VALID_ALERT_TYPES = ["low_stock", "expiring_soon", "expired"]

# Default thresholds
LOW_STOCK_THRESHOLD = 10
EXPIRING_SOON_DAYS = 7


@require_permission("inventory:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for getting inventory alerts

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with alerts
    """
    try:
        # Log request
        user = get_user_from_event(event)
        logger.info(
            "Get inventory alerts request", user_id=user.get("sub"), user_role=user.get("role")
        )

        # Extract query parameters
        query_params = event.get("queryStringParameters") or {}
        alert_type = query_params.get("alert_type")

        # Validate alert type if provided
        if alert_type:
            alert_type = Validator.validate_enum(alert_type, "alert_type", VALID_ALERT_TYPES)

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Get current time
        now = datetime.utcnow()
        now_iso = now.isoformat()

        alerts = []

        # If no specific alert type, get all alerts
        alert_types_to_check = [alert_type] if alert_type else VALID_ALERT_TYPES

        for check_type in alert_types_to_check:
            if check_type == "low_stock":
                # Find items with low stock
                low_stock_alerts = get_low_stock_alerts(db, LOW_STOCK_THRESHOLD)
                alerts.extend(low_stock_alerts)

            elif check_type == "expiring_soon":
                # Find items expiring within 7 days
                expiring_soon_alerts = get_expiring_soon_alerts(db, now, EXPIRING_SOON_DAYS)
                alerts.extend(expiring_soon_alerts)

            elif check_type == "expired":
                # Find items already expired
                expired_alerts = get_expired_alerts(db, now_iso)
                alerts.extend(expired_alerts)

        logger.info("Retrieved inventory alerts", alert_type=alert_type, alert_count=len(alerts))

        # Return alerts
        return success_response(
            {
                "alerts": alerts,
                "count": len(alerts),
                "alert_type": alert_type,
                "thresholds": {
                    "low_stock": LOW_STOCK_THRESHOLD,
                    "expiring_soon_days": EXPIRING_SOON_DAYS,
                },
            }
        )

    except SavingGraceError as e:
        logger.error("SavingGrace error in get inventory alerts", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error in get inventory alerts", error=e)
        return error_response(message="Internal server error", status_code=500)


def get_low_stock_alerts(db: DynamoDBHelper, threshold: int) -> List[Dict[str, Any]]:
    """
    Get low stock alerts

    Args:
        db: DynamoDB helper instance
        threshold: Quantity threshold for low stock

    Returns:
        List of low stock alerts
    """
    from boto3.dynamodb.conditions import Attr

    # Scan for items with quantity below threshold
    result = db.scan(
        filter_expression=(
            Attr("PK").begins_with("INVENTORY#")
            & Attr("quantity").lt(threshold)
            & Attr("quantity").gte(0)
        )
    )

    alerts = []
    for item in result.get("items", []):
        alerts.append(
            {
                "alert_type": "low_stock",
                "severity": "medium",
                "item_id": item.get("item_id"),
                "category": item.get("category"),
                "item_name": item.get("name"),
                "current_quantity": item.get("quantity"),
                "threshold": threshold,
                "unit": item.get("unit", "units"),
                "message": f"{item.get('name')} is low in stock ({item.get('quantity')} {item.get('unit', 'units')} remaining)",
            }
        )

    return alerts


def get_expiring_soon_alerts(
    db: DynamoDBHelper, now: datetime, days_ahead: int
) -> List[Dict[str, Any]]:
    """
    Get expiring soon alerts

    Args:
        db: DynamoDB helper instance
        now: Current datetime
        days_ahead: Number of days to look ahead

    Returns:
        List of expiring soon alerts
    """
    from boto3.dynamodb.conditions import Key, Attr

    # Calculate date range
    future_date = now + timedelta(days=days_ahead)
    now_iso = now.isoformat()
    future_iso = future_date.isoformat()

    # Query GSI ByExpiration for items expiring within the range
    result = db.query(
        key_condition=Key("GSI1PK").eq("INVENTORY"),
        filter_expression=(Attr("GSI1SK").gte(now_iso) & Attr("GSI1SK").lte(future_iso)),
        index_name="GSI1",
    )

    alerts = []
    for item in result.get("items", []):
        expiration_date = item.get("expiration_date")
        if expiration_date:
            # Calculate days until expiration
            try:
                exp_date = datetime.fromisoformat(expiration_date.replace("Z", "+00:00"))
                days_until = (exp_date - now).days

                alerts.append(
                    {
                        "alert_type": "expiring_soon",
                        "severity": "high" if days_until <= 3 else "medium",
                        "item_id": item.get("item_id"),
                        "category": item.get("category"),
                        "item_name": item.get("name"),
                        "quantity": item.get("quantity"),
                        "unit": item.get("unit", "units"),
                        "expiration_date": expiration_date,
                        "days_until_expiration": days_until,
                        "message": f"{item.get('name')} expires in {days_until} days",
                    }
                )
            except (ValueError, AttributeError):
                # Skip items with invalid dates
                pass

    return alerts


def get_expired_alerts(db: DynamoDBHelper, now_iso: str) -> List[Dict[str, Any]]:
    """
    Get expired item alerts

    Args:
        db: DynamoDB helper instance
        now_iso: Current time in ISO format

    Returns:
        List of expired item alerts
    """
    from boto3.dynamodb.conditions import Key, Attr

    # Query GSI ByExpiration for items expired before now
    result = db.query(
        key_condition=Key("GSI1PK").eq("INVENTORY"),
        filter_expression=Attr("GSI1SK").lt(now_iso),
        index_name="GSI1",
    )

    alerts = []
    for item in result.get("items", []):
        expiration_date = item.get("expiration_date")
        if expiration_date:
            alerts.append(
                {
                    "alert_type": "expired",
                    "severity": "critical",
                    "item_id": item.get("item_id"),
                    "category": item.get("category"),
                    "item_name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "unit": item.get("unit", "units"),
                    "expiration_date": expiration_date,
                    "message": f"{item.get('name')} has expired and should be removed",
                }
            )

    return alerts
