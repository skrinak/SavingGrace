"""
Create Donor Lambda Function
POST /donors - Create a new donor
"""
import json
import os
from typing import Any, Dict
from uuid import uuid4
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
)

logger = get_logger(__name__)


@require_role("DonorCoordinator")
@validate_input(
    {
        "name": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
        "email": {"type": "email", "required": True},
        "phone": {"type": "string", "required": False, "min_length": 10, "max_length": 20},
        "address": {"type": "string", "required": False, "max_length": 500},
        "organization": {"type": "string", "required": False, "max_length": 200},
        "notes": {"type": "string", "required": False, "max_length": 1000},
    }
)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Create a new donor

    Args:
        event: Lambda event with validated_body containing donor data
        context: Lambda context

    Returns:
        API Gateway response with created donor
    """
    start_time = datetime.utcnow()

    try:
        # Get user info
        user = get_user_from_event(event)
        logger.log_api_request("POST", "/donors", user_id=user.get("sub"))

        # Get validated data
        data = event["validated_body"]

        # Initialize DynamoDB helper
        db = DynamoDBHelper(os.environ["TABLE_NAME"])

        # Generate donor ID
        donor_id = str(uuid4())

        # Create donor item
        donor = {
            "PK": f"DONOR#{donor_id}",
            "SK": "PROFILE",
            "donor_id": donor_id,
            "name": data["name"],
            "email": data["email"],
            "phone": data.get("phone"),
            "address": data.get("address"),
            "organization": data.get("organization"),
            "notes": data.get("notes"),
            # GSI1 for querying donors by name
            "GSI1PK": "DONORS",
            "GSI1SK": data["name"],
        }

        # Store in DynamoDB
        db_start = datetime.utcnow()
        created_donor = db.put_item(donor)
        db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000

        logger.log_database_operation(
            "put_item", os.environ["TABLE_NAME"], db_duration, donor_id=donor_id
        )

        # Remove internal fields from response
        response_donor = {
            k: v for k, v in created_donor.items() if k not in ["PK", "SK", "GSI1PK", "GSI1SK"]
        }

        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_api_response(201, duration, donor_id=donor_id)

        return success_response(response_donor, status_code=201)

    except SavingGraceError as e:
        logger.error(f"Error creating donor: {e.message}", error=e)
        return error_response(e.message, e.status_code, e.error_code, e.details)
    except Exception as e:
        logger.error("Unexpected error creating donor", error=e)
        return error_response("Internal server error", 500)
