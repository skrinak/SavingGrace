"""
Input Validation Utilities
Schema validation and sanitization
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from .errors import ValidationError


class Validator:
    """Input validation helper"""

    # Regex patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PHONE_PATTERN = re.compile(r"^\+?1?\d{10,15}$")
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> None:
        """
        Validate that all required fields are present

        Args:
            data: Input data
            required_fields: List of required field names

        Raises:
            ValidationError: If any required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(
                message="Missing required fields",
                details={"missing_fields": missing_fields},
            )

    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email format

        Args:
            email: Email address

        Returns:
            Validated email (lowercased)

        Raises:
            ValidationError: If email is invalid
        """
        if not email or not Validator.EMAIL_PATTERN.match(email):
            raise ValidationError(
                message="Invalid email format", details={"email": email}
            )
        return email.lower()

    @staticmethod
    def validate_phone(phone: str) -> str:
        """
        Validate phone number format

        Args:
            phone: Phone number

        Returns:
            Validated phone number

        Raises:
            ValidationError: If phone is invalid
        """
        # Remove common formatting characters
        cleaned = re.sub(r"[\s\-\(\)]", "", phone)
        if not Validator.PHONE_PATTERN.match(cleaned):
            raise ValidationError(
                message="Invalid phone format", details={"phone": phone}
            )
        return cleaned

    @staticmethod
    def validate_string(
        value: Any,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[re.Pattern] = None,
    ) -> str:
        """
        Validate string value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_length: Minimum length
            max_length: Maximum length
            pattern: Optional regex pattern

        Returns:
            Validated string

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(
                message=f"{field_name} must be a string",
                details={"field": field_name, "type": type(value).__name__},
            )

        if min_length and len(value) < min_length:
            raise ValidationError(
                message=f"{field_name} must be at least {min_length} characters",
                details={"field": field_name, "min_length": min_length},
            )

        if max_length and len(value) > max_length:
            raise ValidationError(
                message=f"{field_name} must be at most {max_length} characters",
                details={"field": field_name, "max_length": max_length},
            )

        if pattern and not pattern.match(value):
            raise ValidationError(
                message=f"{field_name} has invalid format",
                details={"field": field_name},
            )

        return value.strip()

    @staticmethod
    def validate_number(
        value: Any,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> float:
        """
        Validate numeric value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_value: Minimum value
            max_value: Maximum value

        Returns:
            Validated number

        Raises:
            ValidationError: If validation fails
        """
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise ValidationError(
                message=f"{field_name} must be a number",
                details={"field": field_name, "value": value},
            )

        if min_value is not None and num_value < min_value:
            raise ValidationError(
                message=f"{field_name} must be at least {min_value}",
                details={"field": field_name, "min_value": min_value},
            )

        if max_value is not None and num_value > max_value:
            raise ValidationError(
                message=f"{field_name} must be at most {max_value}",
                details={"field": field_name, "max_value": max_value},
            )

        return num_value

    @staticmethod
    def validate_date(value: str, field_name: str) -> str:
        """
        Validate ISO date format

        Args:
            value: Date string
            field_name: Field name for error messages

        Returns:
            Validated date string

        Raises:
            ValidationError: If date is invalid
        """
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        except (ValueError, AttributeError):
            raise ValidationError(
                message=f"{field_name} must be a valid ISO date",
                details={"field": field_name, "value": value},
            )

    @staticmethod
    def validate_enum(
        value: Any, field_name: str, allowed_values: List[str]
    ) -> str:
        """
        Validate enum value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            allowed_values: List of allowed values

        Returns:
            Validated value

        Raises:
            ValidationError: If value not in allowed values
        """
        if value not in allowed_values:
            raise ValidationError(
                message=f"{field_name} must be one of: {', '.join(allowed_values)}",
                details={
                    "field": field_name,
                    "value": value,
                    "allowed_values": allowed_values,
                },
            )
        return value

    @staticmethod
    def validate_list(
        value: Any,
        field_name: str,
        min_items: Optional[int] = None,
        max_items: Optional[int] = None,
    ) -> List[Any]:
        """
        Validate list value

        Args:
            value: Value to validate
            field_name: Field name for error messages
            min_items: Minimum number of items
            max_items: Maximum number of items

        Returns:
            Validated list

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, list):
            raise ValidationError(
                message=f"{field_name} must be a list",
                details={"field": field_name, "type": type(value).__name__},
            )

        if min_items and len(value) < min_items:
            raise ValidationError(
                message=f"{field_name} must have at least {min_items} items",
                details={"field": field_name, "min_items": min_items},
            )

        if max_items and len(value) > max_items:
            raise ValidationError(
                message=f"{field_name} must have at most {max_items} items",
                details={"field": field_name, "max_items": max_items},
            )

        return value


def validate_input(schema: Dict[str, Any]) -> callable:
    """
    Decorator for input validation using schema

    Args:
        schema: Validation schema

    Schema format:
        {
            "field_name": {
                "type": "string|number|date|email|phone|enum|list",
                "required": bool,
                "min_length": int (for strings),
                "max_length": int (for strings),
                "min_value": float (for numbers),
                "max_value": float (for numbers),
                "allowed_values": list (for enums),
                "min_items": int (for lists),
                "max_items": int (for lists),
            }
        }

    Usage:
        @validate_input({
            "name": {"type": "string", "required": True, "min_length": 2},
            "email": {"type": "email", "required": True},
            "age": {"type": "number", "min_value": 0, "max_value": 120},
        })
        def lambda_handler(event, context):
            data = json.loads(event["body"])
            ...
    """

    def decorator(func):
        def wrapper(event, context):
            import json

            # Parse body
            try:
                body = event.get("body", "{}")
                data = json.loads(body) if isinstance(body, str) else body
            except json.JSONDecodeError:
                raise ValidationError(message="Invalid JSON in request body")

            # Validate required fields
            required_fields = [
                field for field, rules in schema.items() if rules.get("required")
            ]
            Validator.validate_required_fields(data, required_fields)

            # Validate each field
            for field_name, rules in schema.items():
                if field_name not in data:
                    continue

                value = data[field_name]
                field_type = rules.get("type", "string")

                if field_type == "string":
                    data[field_name] = Validator.validate_string(
                        value,
                        field_name,
                        min_length=rules.get("min_length"),
                        max_length=rules.get("max_length"),
                    )
                elif field_type == "email":
                    data[field_name] = Validator.validate_email(value)
                elif field_type == "phone":
                    data[field_name] = Validator.validate_phone(value)
                elif field_type == "number":
                    data[field_name] = Validator.validate_number(
                        value,
                        field_name,
                        min_value=rules.get("min_value"),
                        max_value=rules.get("max_value"),
                    )
                elif field_type == "date":
                    data[field_name] = Validator.validate_date(value, field_name)
                elif field_type == "enum":
                    data[field_name] = Validator.validate_enum(
                        value, field_name, rules.get("allowed_values", [])
                    )
                elif field_type == "list":
                    data[field_name] = Validator.validate_list(
                        value,
                        field_name,
                        min_items=rules.get("min_items"),
                        max_items=rules.get("max_items"),
                    )

            # Update event with validated data
            event["validated_body"] = data

            return func(event, context)

        return wrapper

    return decorator
