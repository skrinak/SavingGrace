"""
List Donors Lambda Function
GET /donors - List all donors with pagination and search
"""
import os
import json
import base64
from typing import Any, Dict, Optional
from datetime import datetime

from lib import (
    paginated_response,
    error_response,
    get_logger,
    DynamoDBHelper,
    get_user_from_event,
    require_role,
    SavingGraceError,
)
from boto3.dynamodb.conditions import Key, Attr

logger = get_logger(__name__)


def encode_pagination_token(last_key: Dict[str, Any]) -> str:
    """
    Encode DynamoDB LastEvaluatedKey to base64 token

    Args:
        last_key: DynamoDB LastEvaluatedKey

    Returns:
        Base64 encoded token
    """
    json_str = json.dumps(last_key)
    return base64.b64encode(json_str.encode()).decode()


def decode_pagination_token(token: str) -> Dict[str, Any]:
    """
    Decode base64 token to DynamoDB key

    Args:
        token: Base64 encoded pagination token

    Returns:
        DynamoDB key dict
    """
    try:
        json_str = base64.b64decode(token.encode()).decode()
        return json.loads(json_str)
    except Exception:
        return None


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    List donors with pagination and optional search

    Args:
        event: Lambda event with query parameters
        context: Lambda context

    Returns:
        API Gateway response with paginated donors list
    """
    start_time = datetime.utcnow()

    try:
        # Get user info
        user = get_user_from_event(event)
        logger.log_api_request("GET", "/donors", user_id=user.get("sub"))

        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("page_size", "50"))
        search = query_params.get("search")
        next_token = query_params.get("next_token")

        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        # Initialize DynamoDB helper
        db = DynamoDBHelper(os.environ["TABLE_NAME"])

        # Decode pagination token if provided
        exclusive_start_key = None
        if next_token:
            exclusive_start_key = decode_pagination_token(next_token)
            if exclusive_start_key is None:
                raise SavingGraceError(
                    message="Invalid pagination token",
                    status_code=400,
                    error_code="VALIDATION_ERROR"
                )

        # Query using GSI1 (DonorsByName) for efficient listing
        db_start = datetime.utcnow()

        if search:
            # Use scan with filter if search provided
            filter_expr = Attr("name").contains(search) | Attr("email").contains(search)
            if "organization" in query_params:
                filter_expr = filter_expr | Attr("organization").contains(search)

            result = db.scan(
                filter_expression=filter_expr,
                limit=page_size,
                exclusive_start_key=exclusive_start_key
            )
        else:
            # Use GSI query for efficient listing without search
            result = db.query(
                key_condition=Key("GSI1PK").eq("DONORS"),
                index_name="GSI1",
                limit=page_size,
                exclusive_start_key=exclusive_start_key
            )

        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000

        logger.log_database_operation(
            "query" if not search else "scan",
            os.environ["TABLE_NAME"],
            db_duration,
            item_count=result["count"]
        )

        # Remove internal fields from response
        donors = []
        for donor in result["items"]:
            clean_donor = {k: v for k, v in donor.items()
                          if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]}
            donors.append(clean_donor)

        # Encode next token if pagination continues
        encoded_next_token = None
        if result.get("last_evaluated_key"):
            encoded_next_token = encode_pagination_token(result["last_evaluated_key"])

        # For scan operations, we can't determine total count efficiently
        # Use the count from this page as total for now
        total_count = result["count"]

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_api_response(
            200,
            duration,
            donor_count=len(donors)
        )

        return paginated_response(
            items=donors,
            total_count=total_count,
            page=page,
            page_size=page_size,
            next_token=encoded_next_token
        )

    except SavingGraceError as e:
        logger.error(f"Error listing donors: {e.message}", error=e)
        return error_response(e.message, e.status_code, e.error_code, e.details)
    except Exception as e:
        logger.error("Unexpected error listing donors", error=e)
        return error_response("Internal server error", 500)
