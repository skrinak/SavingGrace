"""
Get Donor Lambda Function
GET /donors/{donorId} - Retrieve a specific donor
"""
import os
from typing import Any, Dict
from datetime import datetime

from lib import (
    success_response,
    error_response,
    get_logger,
    DynamoDBHelper,
    get_user_from_event,
    require_role,
    SavingGraceError,
    NotFoundError,
)

logger = get_logger(__name__)


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get a specific donor by ID

    Args:
        event: Lambda event with donorId in pathParameters
        context: Lambda context

    Returns:
        API Gateway response with donor data
    """
    start_time = datetime.utcnow()

    try:
        # Get user info
        user = get_user_from_event(event)
        donor_id = event.get("pathParameters", {}).get("donorId")

        logger.log_api_request(
            "GET",
            f"/donors/{donor_id}",
            user_id=user.get("sub")
        )

        # Validate donor_id
        if not donor_id:
            raise NotFoundError(resource="Donor", resource_id=donor_id)

        # Initialize DynamoDB helper
        db = DynamoDBHelper(os.environ["TABLE_NAME"])

        # Get donor from DynamoDB
        db_start = datetime.utcnow()
        donor = db.get_item(
            pk=f"DONOR#{donor_id}",
            sk="PROFILE"
        )
        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000

        logger.log_database_operation(
            "get_item",
            os.environ["TABLE_NAME"],
            db_duration,
            donor_id=donor_id
        )

        # Remove internal fields from response
        response_donor = {k: v for k, v in donor.items()
                         if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]}

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_api_response(200, duration, donor_id=donor_id)

        return success_response(response_donor)

    except SavingGraceError as e:
        logger.error(f"Error getting donor: {e.message}", error=e)
        return error_response(e.message, e.status_code, e.error_code, e.details)
    except Exception as e:
        logger.error("Unexpected error getting donor", error=e)
        return error_response("Internal server error", 500)
