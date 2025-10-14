"""
HTTP Response Formatters
Standard response structures for API Gateway
"""
import json
from typing import Any, Dict, List, Optional
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for DynamoDB Decimal types"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def success_response(
    data: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Format successful API response

    Args:
        data: Response data
        status_code: HTTP status code (default: 200)
        headers: Additional headers

    Returns:
        API Gateway response object
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Will be restricted in production
        "Access-Control-Allow-Credentials": "true",
    }

    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps({"success": True, "data": data}, cls=DecimalEncoder),
    }


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Format error API response

    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error_code: Application-specific error code
        details: Additional error details
        headers: Additional headers

    Returns:
        API Gateway response object
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",  # Will be restricted in production
        "Access-Control-Allow-Credentials": "true",
    }

    if headers:
        default_headers.update(headers)

    error_body = {
        "success": False,
        "error": {
            "message": message,
            "code": error_code or f"ERROR_{status_code}",
        },
    }

    if details:
        error_body["error"]["details"] = details

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(error_body),
    }


def paginated_response(
    items: List[Any],
    total_count: int,
    page: int = 1,
    page_size: int = 50,
    next_token: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Format paginated API response

    Args:
        items: List of items for current page
        total_count: Total number of items
        page: Current page number
        page_size: Items per page
        next_token: Token for next page (DynamoDB pagination)
        headers: Additional headers

    Returns:
        API Gateway response object
    """
    pagination = {
        "page": page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": (total_count + page_size - 1) // page_size,
    }

    if next_token:
        pagination["next_token"] = next_token

    data = {"items": items, "pagination": pagination}

    return success_response(data, headers=headers)
