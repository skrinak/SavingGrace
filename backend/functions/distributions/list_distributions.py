"""
Lambda function: List Distributions
GET /distributions - List distributions with filtering and pagination
"""
import json
import os
from typing import Any, Dict, Optional
from boto3.dynamodb.conditions import Key, Attr

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import paginated_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()


def parse_query_params(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate query parameters

    Args:
        event: API Gateway event

    Returns:
        Parsed query parameters

    Raises:
        ValidationError: If validation fails
    """
    query_params = event.get("queryStringParameters") or {}

    params = {
        "page": 1,
        "page_size": 50,
        "recipient_id": None,
        "status": None,
        "start_date": None,
        "end_date": None,
    }

    # Parse page
    if "page" in query_params:
        try:
            params["page"] = int(query_params["page"])
            if params["page"] < 1:
                raise ValidationError(
                    message="page must be >= 1",
                    details={"parameter": "page"}
                )
        except ValueError:
            raise ValidationError(
                message="page must be a number",
                details={"parameter": "page"}
            )

    # Parse page_size
    if "page_size" in query_params:
        try:
            params["page_size"] = int(query_params["page_size"])
            if params["page_size"] < 1 or params["page_size"] > 100:
                raise ValidationError(
                    message="page_size must be between 1 and 100",
                    details={"parameter": "page_size"}
                )
        except ValueError:
            raise ValidationError(
                message="page_size must be a number",
                details={"parameter": "page_size"}
            )

    # Parse recipient_id (optional filter)
    if "recipient_id" in query_params and query_params["recipient_id"]:
        params["recipient_id"] = query_params["recipient_id"].strip()

    # Parse status (optional filter)
    if "status" in query_params and query_params["status"]:
        params["status"] = query_params["status"].strip()

    # Parse start_date (optional filter)
    if "start_date" in query_params and query_params["start_date"]:
        Validator.validate_date(query_params["start_date"], "start_date")
        params["start_date"] = query_params["start_date"]

    # Parse end_date (optional filter)
    if "end_date" in query_params and query_params["end_date"]:
        Validator.validate_date(query_params["end_date"], "end_date")
        params["end_date"] = query_params["end_date"]

    return params


def query_distributions(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query distributions based on filters

    Args:
        params: Query parameters

    Returns:
        Query results with items and count
    """
    # Determine which GSI to use based on filters
    if params["recipient_id"]:
        # Use GSI2: ByRecipient (GSI2PK = RECIPIENT#{recipient_id}, GSI2SK = distribution_date)
        key_condition = Key("GSI2PK").eq(f"RECIPIENT#{params['recipient_id']}")

        # Add date range to key condition if provided
        if params["start_date"] and params["end_date"]:
            key_condition &= Key("GSI2SK").between(params["start_date"], params["end_date"])
        elif params["start_date"]:
            key_condition &= Key("GSI2SK").gte(params["start_date"])
        elif params["end_date"]:
            key_condition &= Key("GSI2SK").lte(params["end_date"])

        index_name = "GSI2"
    else:
        # Use GSI1: ByDate (GSI1PK = DISTRIBUTIONS, GSI1SK = distribution_date)
        key_condition = Key("GSI1PK").eq("DISTRIBUTIONS")

        # Add date range to key condition if provided
        if params["start_date"] and params["end_date"]:
            key_condition &= Key("GSI1SK").between(params["start_date"], params["end_date"])
        elif params["start_date"]:
            key_condition &= Key("GSI1SK").gte(params["start_date"])
        elif params["end_date"]:
            key_condition &= Key("GSI1SK").lte(params["end_date"])

        index_name = "GSI1"

    # Build filter expression for status if provided
    filter_expression = None
    if params["status"]:
        filter_expression = Attr("status").eq(params["status"])

    # Query DynamoDB
    result = db.query(
        key_condition=key_condition,
        filter_expression=filter_expression,
        index_name=index_name,
        scan_forward=False  # Most recent first
    )

    return result


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for listing distributions

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Listing distributions", path=event.get("path"))

        # Get user context
        user = get_user_from_event(event)
        logger.set_context(user_id=user.get("sub"), user_role=user.get("role"))

        # Parse and validate query parameters
        params = parse_query_params(event)

        logger.info(
            "Querying distributions",
            recipient_id=params["recipient_id"],
            status=params["status"],
            start_date=params["start_date"],
            end_date=params["end_date"],
            page=params["page"],
            page_size=params["page_size"]
        )

        # Query distributions
        result = query_distributions(params)
        items = result["items"]
        total_count = result["count"]

        # Apply pagination (in-memory for simplicity)
        start_idx = (params["page"] - 1) * params["page_size"]
        end_idx = start_idx + params["page_size"]
        paginated_items = items[start_idx:end_idx]

        # Format items for response
        formatted_items = []
        for item in paginated_items:
            formatted_items.append({
                "distribution_id": item.get("distribution_id"),
                "recipient_id": item.get("recipient_id"),
                "distribution_date": item.get("distribution_date"),
                "status": item.get("status"),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at"),
            })

        logger.info(
            "Distributions listed successfully",
            total_count=total_count,
            returned_count=len(formatted_items)
        )

        return paginated_response(
            items=formatted_items,
            total_count=total_count,
            page=params["page"],
            page_size=params["page_size"]
        )

    except SavingGraceError as e:
        logger.error("Failed to list distributions", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error listing distributions", error=e)
        return error_response(
            message="Internal server error",
            status_code=500
        )
