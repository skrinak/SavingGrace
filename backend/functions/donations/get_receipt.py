"""
Get Receipt Lambda Function
GET /donations/{donationId}/receipt - Generate pre-signed URL for receipt
"""
import os
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from lib.auth import require_role, get_user_from_event
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, NotFoundError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response

# Initialize logger
logger = get_logger(__name__)

# Initialize DynamoDB helper
db = DynamoDBHelper()

# Initialize S3 client
s3_client = boto3.client("s3", region_name="us-west-2")


def extract_s3_key_from_url(url: str, bucket_name: str) -> str:
    """
    Extract S3 key from receipt URL

    Args:
        url: Receipt URL (could be S3 URL or key)
        bucket_name: S3 bucket name

    Returns:
        S3 object key
    """
    # If it's already just a key (no protocol), return it
    if not url.startswith("http") and not url.startswith("s3://"):
        return url

    # Handle s3:// URLs
    if url.startswith("s3://"):
        # Format: s3://bucket-name/key
        parts = url.replace("s3://", "").split("/", 1)
        if len(parts) == 2:
            return parts[1]
        return parts[0]

    # Handle https:// URLs
    if url.startswith("https://"):
        # Format: https://bucket-name.s3.region.amazonaws.com/key
        # or https://s3.region.amazonaws.com/bucket-name/key
        if ".s3." in url or ".s3-" in url:
            # Extract key from S3 URL
            if f"{bucket_name}.s3." in url:
                # Virtual-hosted-style URL
                key_start = url.find(".amazonaws.com/")
                if key_start != -1:
                    return url[key_start + 15 :]
            elif "/s3." in url or "/s3-" in url:
                # Path-style URL
                bucket_start = url.find(f"/{bucket_name}/")
                if bucket_start != -1:
                    return url[bucket_start + len(bucket_name) + 2 :]

    # If we can't parse it, assume it's a key
    return url


@require_role("DonorCoordinator")
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for getting receipt pre-signed URL

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    try:
        # Log request
        logger.info("Getting receipt", event=event)

        # Get user from event
        user = get_user_from_event(event)

        # Get donation ID from path parameters
        path_params = event.get("pathParameters", {})
        donation_id = path_params.get("donationId")

        if not donation_id:
            raise NotFoundError(resource="Donation", resource_id="")

        # Get donation metadata
        pk = f"DONATION#{donation_id}"
        sk = "METADATA"

        try:
            donation = db.get_item(pk, sk)
        except NotFoundError:
            raise NotFoundError(resource="Donation", resource_id=donation_id)

        # Check if receipt_url exists
        receipt_url = donation.get("receipt_url")
        if not receipt_url:
            raise ValidationError(
                message="No receipt available for this donation",
                details={"donation_id": donation_id},
            )

        # Get bucket name from environment
        bucket_name = os.environ.get("RECEIPTS_BUCKET_NAME")
        if not bucket_name:
            logger.error("RECEIPTS_BUCKET_NAME environment variable not set")
            raise SavingGraceError(message="Receipt storage not configured", status_code=500)

        # Extract S3 key from receipt URL
        s3_key = extract_s3_key_from_url(receipt_url, bucket_name)

        logger.info(
            "Generating pre-signed URL", donation_id=donation_id, bucket=bucket_name, key=s3_key
        )

        # Generate pre-signed URL (expires in 1 hour)
        try:
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": s3_key},
                ExpiresIn=3600,  # 1 hour
            )
        except ClientError as e:
            logger.error(
                "Failed to generate pre-signed URL", error=e, bucket=bucket_name, key=s3_key
            )
            raise SavingGraceError(
                message="Failed to generate receipt URL", status_code=500, details={"error": str(e)}
            )

        # Calculate expiration time
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        response_data = {
            "receipt_url": presigned_url,
            "expires_at": expires_at,
        }

        logger.info("Generated pre-signed URL", donation_id=donation_id)

        return success_response(response_data)

    except SavingGraceError as e:
        logger.error("Failed to get receipt", error=e, error_code=e.error_code)
        return error_response(
            message=e.message,
            status_code=e.status_code,
            error_code=e.error_code,
            details=e.details,
        )
    except Exception as e:
        logger.error("Unexpected error getting receipt", error=e)
        return error_response(
            message="Internal server error",
            status_code=500,
        )
