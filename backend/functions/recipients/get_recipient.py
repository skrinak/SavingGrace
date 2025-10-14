"""
Get Recipient Lambda Function
GET /recipients/{recipientId}
Retrieves a specific recipient by ID
"""
import os
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, NotFoundError
from lib.logger import get_logger
from lib.responses import success_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Get recipient by ID

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with recipient data
    """
    try:
        # Get recipient ID from path parameters
        recipient_id = event.get("pathParameters", {}).get("recipientId")

        if not recipient_id:
            return error_response(
                message="Recipient ID is required",
                status_code=400,
            )

        # Log request
        logger.log_api_request(
            method=event.get("httpMethod"),
            path=event.get("path"),
            user_id=get_user_from_event(event).get("sub"),
            recipient_id=recipient_id,
        )

        # Get recipient from DynamoDB
        recipient = db.get_item(pk=f"RECIPIENT#{recipient_id}", sk="PROFILE")

        logger.info(
            "Recipient retrieved successfully",
            recipient_id=recipient_id,
        )

        # Return response (remove DynamoDB keys)
        response_data = {
            k: v for k, v in recipient.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]
        }

        return success_response(response_data)

    except NotFoundError as e:
        logger.warning("Recipient not found", recipient_id=recipient_id)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
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
