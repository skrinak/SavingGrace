# SavingGrace Backend

Python 3.11+ serverless backend for SavingGrace food donation tracking platform.

## Prerequisites

- Python 3.11+
- UV (fast Python package manager)
- AWS CLI configured for account 921212210452
- AWS CDK CLI

## Installation

### Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Dependencies
```bash
# Install backend dependencies
uv pip install -r requirements.txt

# Install CDK dependencies (in infrastructure/)
cd infrastructure
uv pip install -r requirements.txt
```

## Development

### Run Tests
```bash
make test                # Run all tests
make test-unit          # Run unit tests only
make test-integration   # Run integration tests only
make test-coverage      # Run with coverage report
```

### Code Quality
```bash
make lint               # Run pylint
make format             # Format with black
make typecheck          # Type check with mypy
make quality            # Run all quality checks
```

### Package Lambda Functions
```bash
make package-<function-name>   # Package specific function
# Example: make package-listDonors
```

## Deployment

### Deploy Infrastructure
```bash
# Deploy to dev
make deploy-dev

# Deploy to staging
make deploy-staging

# Deploy to production
make deploy-prod

# Preview changes
make diff

# Generate CloudFormation template
make synth
```

### Deploy Single Lambda
```bash
aws lambda update-function-code \
  --function-name <function-name> \
  --zip-file fileb://functions/<function-name>/function.zip \
  --region us-west-2
```

## Project Structure

```
backend/
├── functions/          # Lambda function code
│   ├── donors/        # Donor management functions
│   ├── donations/     # Donation tracking functions
│   ├── recipients/    # Recipient management functions
│   ├── distributions/ # Distribution management functions
│   ├── inventory/     # Inventory management functions
│   ├── reports/       # Reporting functions
│   └── users/         # User management functions
├── layers/            # Lambda layers (shared code)
│   └── shared/       # Shared utilities
├── tests/             # Integration tests
├── infrastructure/    # AWS CDK code
├── requirements.txt   # Python dependencies
├── pytest.ini        # Pytest configuration
├── pyproject.toml    # Black, mypy configuration
├── .pylintrc         # Pylint configuration
└── Makefile          # Common tasks
```

## Architecture

- **Runtime**: Python 3.11+
- **Region**: us-west-2 ONLY
- **API Gateway**: REST API (no proxies)
- **Database**: DynamoDB with GSIs
- **Storage**: S3 with pre-signed URLs
- **Auth**: Cognito User Pools
- **Monitoring**: CloudWatch + X-Ray

## Environment Variables

Environment variables are loaded from AWS Systems Manager Parameter Store in production.

For local development, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key variables:
- `AWS_REGION=us-west-2`
- `DYNAMODB_*_TABLE` - Table names
- `S3_RECEIPTS_BUCKET` - S3 bucket for receipts
- `COGNITO_USER_POOL_ID` - Cognito User Pool ID

## Testing

### Unit Tests
```bash
pytest -m unit
```

### Integration Tests
```bash
pytest -m integration
```

### Coverage
```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

## Common Tasks

```bash
# Install dependencies
make install

# Run all quality checks
make quality

# Clean build artifacts
make clean

# Deploy to dev
make deploy-dev
```

## Troubleshooting

### UV not found
Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### AWS credentials
Ensure AWS CLI is configured for account 921212210452 with us-west-2 region.

### Import errors
Run `make install` to ensure all dependencies are installed.

## Contributing

1. Read CLAUDE.md for development guidelines
2. Use UV for package management (not pip/conda)
3. Run `make quality` before committing
4. Ensure 80%+ test coverage
5. Follow Python style guide (black + pylint)
