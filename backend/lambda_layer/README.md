# SavingGrace Lambda Shared Layer

Shared utilities for all SavingGrace Lambda functions.

## Contents

- **responses.py**: HTTP response formatters (success, error, paginated)
- **errors.py**: Custom exception classes
- **dynamodb.py**: DynamoDB helper utilities
- **auth.py**: Authentication and authorization utilities
- **validation.py**: Input validation utilities
- **logger.py**: Structured logging for CloudWatch

## Usage

All Lambda functions have access to this layer. Import utilities as:

```python
from lib import (
    success_response,
    error_response,
    get_logger,
    DynamoDBHelper,
    AuthHelper,
    require_role,
    validate_input,
)

logger = get_logger(__name__)
```

## Examples

### Response Formatting

```python
# Success response
return success_response({"id": "123", "name": "John Doe"})

# Error response
return error_response("Resource not found", status_code=404)

# Paginated response
return paginated_response(
    items=donors,
    total_count=100,
    page=1,
    page_size=50
)
```

### Error Handling

```python
from lib import NotFoundError, ValidationError

# Raise custom errors
raise NotFoundError("Donor", donor_id)
raise ValidationError("Invalid email format", details={"email": email})

# Handle errors in Lambda
try:
    # Your code
except SavingGraceError as e:
    return error_response(
        message=e.message,
        status_code=e.status_code,
        error_code=e.error_code,
        details=e.details
    )
```

### DynamoDB Operations

```python
from lib import DynamoDBHelper

db = DynamoDBHelper("SavingGrace-Donors-dev")

# Put item
donor = db.put_item({
    "PK": f"DONOR#{donor_id}",
    "SK": "PROFILE",
    "name": "John Doe",
    "email": "john@example.com"
})

# Get item
donor = db.get_item(f"DONOR#{donor_id}", "PROFILE")

# Query with GSI
result = db.query(
    key_condition=Key("GSI1PK").eq(f"DONOR#{donor_id}"),
    index_name="DonorsByName"
)

# Update item
updated = db.update_item(
    pk=f"DONOR#{donor_id}",
    sk="PROFILE",
    updates={"name": "Jane Doe"}
)
```

### Authentication & Authorization

```python
from lib import get_user_from_event, require_role, AuthHelper

# Get user from event
def lambda_handler(event, context):
    user = get_user_from_event(event)
    logger.info("User", user_id=user["sub"], role=user["role"])

# Require specific role (decorator)
@require_role("DonorCoordinator")
def lambda_handler(event, context):
    # Only DonorCoordinator or higher can access

# Check permissions
AuthHelper.check_resource_access(
    user=user,
    resource_type="donors",
    action="create"
)
```

### Input Validation

```python
from lib import validate_input

@validate_input({
    "name": {"type": "string", "required": True, "min_length": 2, "max_length": 100},
    "email": {"type": "email", "required": True},
    "phone": {"type": "phone", "required": False},
    "age": {"type": "number", "min_value": 0, "max_value": 120},
    "status": {"type": "enum", "allowed_values": ["active", "inactive"]},
})
def lambda_handler(event, context):
    # Validated data available in event["validated_body"]
    data = event["validated_body"]
```

### Logging

```python
from lib import get_logger

logger = get_logger(__name__)

# Structured logging
logger.info("Processing donation", donation_id=donation_id, amount=100.50)
logger.error("Failed to save donor", error=e, donor_id=donor_id)

# Log API request/response
logger.log_api_request("POST", "/donors", user_id=user["sub"])
logger.log_api_response(201, duration_ms=123.45)

# Log database operations
logger.log_database_operation("put_item", "Donors", duration_ms=45.67)

# Set context for all logs
logger.set_context(request_id=context.request_id)
```

## Building the Layer

The layer is automatically built and deployed by CDK. To manually build:

```bash
cd backend/lambda_layer
uv pip install -r requirements.txt -t python/
zip -r layer.zip python/
```

## Deployment

The layer is deployed as part of the infrastructure stack and automatically attached to all Lambda functions.
