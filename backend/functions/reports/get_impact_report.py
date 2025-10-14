"""
Lambda function: GET /reports/impact
Get impact report with social and environmental metrics
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List
from collections import defaultdict
from decimal import Decimal

from lib.auth import require_permission
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator
from boto3.dynamodb.conditions import Key, Attr

# Initialize logger
logger = get_logger(__name__)

# Weight conversion factors (approximate)
CATEGORY_WEIGHT_FACTORS = {
    "produce": 0.5,  # lbs per item
    "dairy": 1.0,
    "meat": 1.5,
    "bakery": 0.75,
    "canned_goods": 1.0,
    "dry_goods": 2.0,
    "frozen": 2.0,
    "beverages": 1.5,
    "prepared_foods": 1.25,
    "other": 1.0,
}

# Meals calculation: 1 meal = ~1.5 lbs of food
POUNDS_PER_MEAL = 1.5


def calculate_meals_from_items(items: List[Dict[str, Any]]) -> int:
    """
    Calculate estimated meals provided from donation items

    Args:
        items: List of donation items

    Returns:
        Estimated number of meals
    """
    total_pounds = Decimal("0")

    for item in items:
        category = item.get("category", "other")
        quantity = Decimal(str(item.get("quantity", 0)))

        # Check if weight_lbs is directly provided
        if "weight_lbs" in item:
            total_pounds += Decimal(str(item["weight_lbs"]))
        else:
            # Estimate weight based on category
            weight_factor = CATEGORY_WEIGHT_FACTORS.get(category, 1.0)
            total_pounds += quantity * Decimal(str(weight_factor))

    # Calculate meals (1 meal = 1.5 lbs)
    meals = int(total_pounds / Decimal(str(POUNDS_PER_MEAL)))
    return meals


def aggregate_by_category(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate items distributed by category

    Args:
        items: List of distributed items

    Returns:
        Dictionary of category -> quantity
    """
    category_totals = defaultdict(int)

    for item in items:
        category = item.get("category", "other")
        quantity = item.get("quantity", 0)
        category_totals[category] += quantity

    return dict(category_totals)


@require_permission("reports:read")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get impact report with social and environmental metrics

    Query Parameters:
        - start_date (optional): Start date in ISO format (default: all time)
        - end_date (optional): End date in ISO format (default: now)

    Calculates:
        - total_meals_provided: Estimated meals based on food weight
        - households_served: Unique recipients served
        - items_distributed_by_category: Breakdown by category
        - waste_prevented_lbs: Total weight of food diverted from waste

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with impact metrics
    """
    try:
        # Parse query parameters
        query_params = event.get("queryStringParameters") or {}

        # Get date range (default to all time)
        now = datetime.utcnow()
        end_date_str = query_params.get("end_date")
        start_date_str = query_params.get("start_date")

        if end_date_str:
            end_date = Validator.validate_date(end_date_str, "end_date")
        else:
            end_date = now.isoformat()

        # Default to all time (beginning of 2020)
        if start_date_str:
            start_date = Validator.validate_date(start_date_str, "start_date")
        else:
            start_date = "2020-01-01T00:00:00"

        logger.info(
            "Fetching impact report",
            start_date=start_date,
            end_date=end_date
        )

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Initialize metrics
        total_meals_provided = 0
        households_served = set()
        items_distributed_by_category = defaultdict(int)
        total_weight_lbs = Decimal("0")

        # Query all donations in date range to calculate waste prevented
        donations_response = db.scan(
            filter_expression=Attr("PK").begins_with("DONATION#") &
                            Attr("SK").eq("METADATA") &
                            Attr("created_at").between(start_date, end_date)
        )

        donations = donations_response["items"]
        logger.info(f"Found {len(donations)} donations in date range")

        # Calculate total donated weight (waste prevented)
        all_donation_items = []
        for donation in donations:
            items = donation.get("items", [])
            all_donation_items.extend(items)

            # Accumulate weight
            if "total_weight_lbs" in donation:
                total_weight_lbs += Decimal(str(donation["total_weight_lbs"]))
            else:
                # Calculate from items
                for item in items:
                    category = item.get("category", "other")
                    quantity = Decimal(str(item.get("quantity", 0)))

                    if "weight_lbs" in item:
                        total_weight_lbs += Decimal(str(item["weight_lbs"]))
                    else:
                        weight_factor = CATEGORY_WEIGHT_FACTORS.get(category, 1.0)
                        total_weight_lbs += quantity * Decimal(str(weight_factor))

        # Query all completed distributions in date range
        distributions_response = db.scan(
            filter_expression=Attr("PK").begins_with("DISTRIBUTION#") &
                            Attr("SK").eq("METADATA") &
                            Attr("status").eq("completed") &
                            Attr("created_at").between(start_date, end_date)
        )

        distributions = distributions_response["items"]
        logger.info(f"Found {len(distributions)} completed distributions in date range")

        # Calculate metrics from distributions
        all_distributed_items = []
        for distribution in distributions:
            # Track unique recipients
            recipient_id = distribution.get("recipient_id")
            if recipient_id:
                households_served.add(recipient_id)

            # Collect distributed items
            items = distribution.get("items", [])
            all_distributed_items.extend(items)

            # Aggregate by category
            for item in items:
                category = item.get("category", "other")
                quantity = item.get("quantity", 0)
                items_distributed_by_category[category] += quantity

        # Calculate total meals provided
        total_meals_provided = calculate_meals_from_items(all_distributed_items)

        # Build result
        result = {
            "report_type": "impact",
            "start_date": start_date,
            "end_date": end_date,
            "metrics": {
                "total_meals_provided": total_meals_provided,
                "households_served": len(households_served),
                "total_distributions": len(distributions),
                "total_donations": len(donations),
                "waste_prevented_lbs": float(total_weight_lbs),
                "items_distributed_by_category": dict(items_distributed_by_category),
            },
        }

        logger.info("Impact report generated successfully", metrics=result["metrics"])

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
