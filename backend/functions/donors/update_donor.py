"""
Update Donor Lambda Function
PUT /donors/{donorId} - Update an existing donor
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
    validate_input,
    SavingGraceError,
    NotFoundError,
)

logger = get_logger(__name__)


@require_role("DonorCoordinator")
@validate_input(
    {
        "name": {"type": "string", "required": False, "min_length": 2, "max_length": 100},
        "email": {"type": "email", "required": False},
        "phone": {"type": "string", "required": False, "min_length": 10, "max_length": 20},
        "address": {"type": "string", "required": False, "max_length": 500},
        "organization": {"type": "string", "required": False, "max_length": 200},
        "notes": {"type": "string", "required": False, "max_length": 1000},
    }
)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Update an existing donor

    Args:
        event: Lambda event with donorId in pathParameters and validated_body
        context: Lambda context

    Returns:
        API Gateway response with updated donor
    """
    start_time = datetime.utcnow()

    try:
        # Get user info
        user = get_user_from_event(event)
        donor_id = event.get("pathParameters", {}).get("donorId")

        logger.log_api_request("PUT", f"/donors/{donor_id}", user_id=user.get("sub"))

        # Validate donor_id
        if not donor_id:
            raise NotFoundError(resource="Donor", resource_id=donor_id)

        # Get validated data
        data = event["validated_body"]

        # Check if there are fields to update
        if not data:
            raise SavingGraceError(
                message="No fields provided to update",
                status_code=400,
                error_code="VALIDATION_ERROR",
            )

        # Initialize DynamoDB helper
        db = DynamoDBHelper(os.environ["TABLE_NAME"])

        # Build updates dictionary (only include provided fields)
        updates = {}
        if "name" in data:
            updates["name"] = data["name"]
            # Update GSI1SK for name-based queries
            updates["GSI1SK"] = data["name"]
        if "email" in data:
            updates["email"] = data["email"]
        if "phone" in data:
            updates["phone"] = data["phone"]
        if "address" in data:
            updates["address"] = data["address"]
        if "organization" in data:
            updates["organization"] = data["organization"]
        if "notes" in data:
            updates["notes"] = data["notes"]

        # Update donor in DynamoDB
        db_start = datetime.utcnow()
        updated_donor = db.update_item(pk=f"DONOR#{donor_id}", sk="PROFILE", updates=updates)
        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000

        logger.log_database_operation(
            "update_item", os.environ["TABLE_NAME"], db_duration, donor_id=donor_id
        )

        # Remove internal fields from response
        response_donor = {
            k: v for k, v in updated_donor.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]
        }

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_api_response(200, duration, donor_id=donor_id)

        return success_response(response_donor)

    except SavingGraceError as e:
        logger.error(f"Error updating donor: {e.message}", error=e)
        return error_response(e.message, e.status_code, e.error_code, e.details)
    except Exception as e:
        logger.error("Unexpected error updating donor", error=e)
        return error_response("Internal server error", 500)
