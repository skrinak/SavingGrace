"""
Lambda function: POST /reports/export
Export report to S3 and generate pre-signed download URL
"""
import json
import os
import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import Key, Attr

from lib.auth import require_role
from lib.dynamodb import DynamoDBHelper
from lib.errors import SavingGraceError, ValidationError
from lib.logger import get_logger
from lib.responses import success_response, error_response
from lib.validation import validate_input

# Initialize logger
logger = get_logger(__name__)

# Initialize S3 client
s3_client = boto3.client("s3", region_name="us-west-2")


def generate_donations_export(
    db: DynamoDBHelper, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Generate donations export data

    Args:
        db: DynamoDB helper
        start_date: Start date
        end_date: End date

    Returns:
        List of donation records
    """
    response = db.scan(
        filter_expression=Attr("PK").begins_with("DONATION#")
        & Attr("SK").eq("METADATA")
        & Attr("created_at").between(start_date, end_date)
    )

    donations = []
    for item in response["items"]:
        donations.append(
            {
                "donation_id": item.get("PK", "").replace("DONATION#", ""),
                "donor_id": item.get("donor_id", ""),
                "donor_name": item.get("donor_name", ""),
                "created_at": item.get("created_at", ""),
                "total_items": item.get("total_items", 0),
                "total_weight_lbs": item.get("total_weight_lbs", 0),
                "status": item.get("status", ""),
                "notes": item.get("notes", ""),
            }
        )

    return donations


def generate_distributions_export(
    db: DynamoDBHelper, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Generate distributions export data

    Args:
        db: DynamoDB helper
        start_date: Start date
        end_date: End date

    Returns:
        List of distribution records
    """
    response = db.scan(
        filter_expression=Attr("PK").begins_with("DISTRIBUTION#")
        & Attr("SK").eq("METADATA")
        & Attr("created_at").between(start_date, end_date)
    )

    distributions = []
    for item in response["items"]:
        distributions.append(
            {
                "distribution_id": item.get("PK", "").replace("DISTRIBUTION#", ""),
                "recipient_id": item.get("recipient_id", ""),
                "recipient_name": item.get("recipient_name", ""),
                "scheduled_date": item.get("scheduled_date", ""),
                "completed_at": item.get("completed_at", ""),
                "total_items": item.get("total_items", 0),
                "status": item.get("status", ""),
                "notes": item.get("notes", ""),
            }
        )

    return distributions


def generate_inventory_export(db: DynamoDBHelper) -> List[Dict[str, Any]]:
    """
    Generate inventory export data

    Args:
        db: DynamoDB helper

    Returns:
        List of inventory records
    """
    response = db.scan(
        filter_expression=Attr("PK").begins_with("INVENTORY#")
        & Attr("SK").eq("METADATA")
    )

    inventory = []
    for item in response["items"]:
        inventory.append(
            {
                "inventory_id": item.get("PK", "").replace("INVENTORY#", ""),
                "category": item.get("category", ""),
                "item_name": item.get("item_name", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "reorder_point": item.get("reorder_point", 0),
                "location": item.get("location", ""),
                "updated_at": item.get("updated_at", ""),
            }
        )

    return inventory


def generate_impact_export(
    db: DynamoDBHelper, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Generate impact export data

    Args:
        db: DynamoDB helper
        start_date: Start date
        end_date: End date

    Returns:
        List of impact metrics
    """
    # Get donations
    donations_response = db.scan(
        filter_expression=Attr("PK").begins_with("DONATION#")
        & Attr("SK").eq("METADATA")
        & Attr("created_at").between(start_date, end_date)
    )

    # Get distributions
    distributions_response = db.scan(
        filter_expression=Attr("PK").begins_with("DISTRIBUTION#")
        & Attr("SK").eq("METADATA")
        & Attr("status").eq("completed")
        & Attr("created_at").between(start_date, end_date)
    )

    # Aggregate by month
    from collections import defaultdict

    monthly_impact = defaultdict(
        lambda: {
            "month": "",
            "total_donations": 0,
            "total_distributions": 0,
            "total_weight_lbs": 0,
        }
    )

    for donation in donations_response["items"]:
        created_at = donation.get("created_at", "")
        month = created_at[:7] if created_at else "unknown"  # YYYY-MM
        monthly_impact[month]["month"] = month
        monthly_impact[month]["total_donations"] += 1
        monthly_impact[month]["total_weight_lbs"] += float(
            donation.get("total_weight_lbs", 0)
        )

    for distribution in distributions_response["items"]:
        created_at = distribution.get("created_at", "")
        month = created_at[:7] if created_at else "unknown"  # YYYY-MM
        monthly_impact[month]["month"] = month
        monthly_impact[month]["total_distributions"] += 1

    return list(monthly_impact.values())


def export_to_csv(data: List[Dict[str, Any]]) -> str:
    """
    Convert data to CSV format

    Args:
        data: List of records

    Returns:
        CSV string
    """
    if not data:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def export_to_json(data: List[Dict[str, Any]]) -> str:
    """
    Convert data to JSON format

    Args:
        data: List of records

    Returns:
        JSON string
    """
    return json.dumps(data, indent=2, default=str)


@require_role("Admin")
@validate_input(
    {
        "report_type": {
            "type": "enum",
            "required": True,
            "allowed_values": ["donations", "distributions", "inventory", "impact"],
        },
        "format": {
            "type": "enum",
            "required": True,
            "allowed_values": ["csv", "json"],
        },
        "start_date": {"type": "date", "required": False},
        "end_date": {"type": "date", "required": False},
    }
)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Export report to S3 and generate pre-signed download URL

    Request Body:
        - report_type: Type of report (donations, distributions, inventory, impact)
        - format: Export format (csv, json)
        - start_date (optional): Start date in ISO format
        - end_date (optional): End date in ISO format

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with pre-signed URL and expiration
    """
    try:
        # Get validated body
        data = event.get("validated_body", {})

        report_type = data["report_type"]
        export_format = data["format"]

        # Get date range (default to last 30 days for time-based reports)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)

        start_date = data.get("start_date", thirty_days_ago.isoformat())
        end_date = data.get("end_date", now.isoformat())

        logger.info(
            "Generating export",
            report_type=report_type,
            format=export_format,
            start_date=start_date,
            end_date=end_date,
        )

        # Initialize DynamoDB helper
        db = DynamoDBHelper()

        # Generate export data based on report type
        if report_type == "donations":
            export_data = generate_donations_export(db, start_date, end_date)
        elif report_type == "distributions":
            export_data = generate_distributions_export(db, start_date, end_date)
        elif report_type == "inventory":
            export_data = generate_inventory_export(db)
        elif report_type == "impact":
            export_data = generate_impact_export(db, start_date, end_date)
        else:
            raise ValidationError(message=f"Invalid report type: {report_type}")

        logger.info(f"Generated {len(export_data)} records for export")

        # Convert to requested format
        if export_format == "csv":
            export_content = export_to_csv(export_data)
            content_type = "text/csv"
        else:  # json
            export_content = export_to_json(export_data)
            content_type = "application/json"

        # Upload to S3
        bucket_name = os.environ.get("EXPORTS_BUCKET_NAME")
        if not bucket_name:
            raise ValidationError(message="EXPORTS_BUCKET_NAME not configured")

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"exports/{report_type}_{timestamp}.{export_format}"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=export_content.encode("utf-8"),
            ContentType=content_type,
            Metadata={
                "report_type": report_type,
                "start_date": start_date,
                "end_date": end_date,
                "generated_at": now.isoformat(),
            },
        )

        logger.info(f"Uploaded export to S3: {filename}")

        # Generate pre-signed URL (expires in 1 hour)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": filename},
            ExpiresIn=3600,
        )

        # Calculate expiration time
        expires_at = (now + timedelta(hours=1)).isoformat()

        result = {
            "export_url": presigned_url,
            "expires_at": expires_at,
            "format": export_format,
            "report_type": report_type,
            "record_count": len(export_data),
            "filename": filename,
        }

        logger.info("Export generated successfully", result=result)

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
