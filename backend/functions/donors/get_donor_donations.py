"""
Get Donor Donations Lambda Function
GET /donors/{donorId}/donations - Get all donations for a specific donor
"""
import os
import json
import base64
from typing import Any, Dict
from datetime import datetime

from lib import (
    paginated_response,
    error_response,
    get_logger,
    DynamoDBHelper,
    get_user_from_event,
    require_role,
    SavingGraceError,
    NotFoundError,
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
    Get all donations for a specific donor with pagination and date filtering

    Args:
        event: Lambda event with donorId in pathParameters and query parameters
        context: Lambda context

    Returns:
        API Gateway response with paginated donations list
    """
    start_time = datetime.utcnow()

    try:
        # Get user info
        user = get_user_from_event(event)
        donor_id = event.get("pathParameters", {}).get("donorId")

        logger.log_api_request("GET", f"/donors/{donor_id}/donations", user_id=user.get("sub"))

        # Validate donor_id
        if not donor_id:
            raise NotFoundError(resource="Donor", resource_id=donor_id)

        # Get query parameters
        query_params = event.get("queryStringParameters") or {}
        page = int(query_params.get("page", "1"))
        page_size = int(query_params.get("page_size", "50"))
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        next_token = query_params.get("next_token")

        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        # Initialize DynamoDB helper
        db = DynamoDBHelper(os.environ["TABLE_NAME"])

        # First, verify donor exists
        try:
            db_verify_start = datetime.utcnow()
            db.get_item(pk=f"DONOR#{donor_id}", sk="PROFILE")
            db_verify_duration = (datetime.utcnow() - db_verify_start).total_seconds() * 1000
            logger.log_database_operation(
                "get_item",
                os.environ["TABLE_NAME"],
                db_verify_duration,
                operation="verify_donor",
                donor_id=donor_id,
            )
        except NotFoundError:
            raise NotFoundError(resource="Donor", resource_id=donor_id)

        # Decode pagination token if provided
        exclusive_start_key = None
        if next_token:
            exclusive_start_key = decode_pagination_token(next_token)
            if exclusive_start_key is None:
                raise SavingGraceError(
                    message="Invalid pagination token",
                    status_code=400,
                    error_code="VALIDATION_ERROR",
                )

        # Query donations using GSI ByDonor
        # GSI structure: GSI2PK = DONOR#{donor_id}, GSI2SK = donation_date
        db_start = datetime.utcnow()

        key_condition = Key("GSI2PK").eq(f"DONOR#{donor_id}")

        # Add date range filter if provided
        filter_expression = None
        if start_date and end_date:
            filter_expression = Attr("donation_date").between(start_date, end_date)
        elif start_date:
            filter_expression = Attr("donation_date").gte(start_date)
        elif end_date:
            filter_expression = Attr("donation_date").lte(end_date)

        result = db.query(
            key_condition=key_condition,
            filter_expression=filter_expression,
            index_name="GSI2",
            limit=page_size,
            exclusive_start_key=exclusive_start_key,
            scan_forward=False,  # Most recent donations first
        )

        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000

        logger.log_database_operation(
            "query",
            os.environ["TABLE_NAME"],
            db_duration,
            donor_id=donor_id,
            donation_count=result["count"],
        )

        # Remove internal fields from response
        donations = []
        for donation in result["items"]:
            clean_donation = {
                k: v
                for k, v in donation.items()
                if k not in ["PK", "SK", "GSI1PK", "GSI1SK", "GSI2PK", "GSI2SK"]
            }
            donations.append(clean_donation)

        # Encode next token if pagination continues
        encoded_next_token = None
        if result.get("last_evaluated_key"):
            encoded_next_token = encode_pagination_token(result["last_evaluated_key"])

        # Use count from query result
        total_count = result["count"]

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_api_response(200, duration, donor_id=donor_id, donation_count=len(donations))

        return paginated_response(
            items=donations,
            total_count=total_count,
            page=page,
            page_size=page_size,
            next_token=encoded_next_token,
        )

    except SavingGraceError as e:
        logger.error(f"Error getting donor donations: {e.message}", error=e)
        return error_response(e.message, e.status_code, e.error_code, e.details)
    except Exception as e:
        logger.error("Unexpected error getting donor donations", error=e)
        return error_response("Internal server error", 500)
