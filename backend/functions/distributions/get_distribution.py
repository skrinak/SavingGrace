"""
Lambda function: Get Distribution
GET /distributions/{distributionId} - Retrieve a specific distribution
"""
import os
from typing import Any, Dict

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import Validator

# Initialize
logger = get_logger(__name__)
db = DynamoDBHelper()


@require_role("DistributionManager")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for retrieving a distribution

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Getting distribution", path=event.get("path"))

        # Get user context
        user = get_user_from_event(event)
        logger.set_context(user_id=user.get("sub"), user_role=user.get("role"))

        # Get distribution ID from path parameters
        path_params = event.get("pathParameters", {})
        distribution_id = path_params.get("distributionId")

        if not distribution_id:
            raise ValidationError(
                message="Missing distributionId in path", details={"parameter": "distributionId"}
            )

        # Validate distribution_id format
        Validator.validate_string(distribution_id, "distributionId", min_length=1)

        logger.info("Retrieving distribution", distribution_id=distribution_id)

        # Get distribution from DynamoDB
        pk = f"DISTRIBUTION#{distribution_id}"
        sk = "METADATA"

        distribution = db.get_item(pk, sk)

        logger.info(
            "Distribution retrieved successfully",
            distribution_id=distribution_id,
            status=distribution.get("status"),
        )

        # Prepare response (exclude internal fields)
        response_data = {
            "distribution_id": distribution.get("distribution_id"),
            "recipient_id": distribution.get("recipient_id"),
            "items": distribution.get("items", []),
            "distribution_date": distribution.get("distribution_date"),
            "status": distribution.get("status"),
            "notes": distribution.get("notes", ""),
            "completed_at": distribution.get("completed_at"),
            "created_at": distribution.get("created_at"),
            "updated_at": distribution.get("updated_at"),
        }

        return success_response(data=response_data)

    except SavingGraceError as e:
        logger.error("Failed to retrieve distribution", error=e, error_code=e.error_code)
        return error_response(
            message=e.message, status_code=e.status_code, error_code=e.error_code, details=e.details
        )
    except Exception as e:
        logger.error("Unexpected error retrieving distribution", error=e)
        return error_response(message="Internal server error", status_code=500)
