# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SavingGrace is a production-ready food donation tracking and distribution web application for non-profit organizations. The system consists of a React frontend and AWS serverless backend.

**Critical Architecture Rule**: API Gateway is the SOLE entry point for all backend requests. NO proxies (Express, HTTP proxies), NO FastAPI, NO intermediate servers. All Lambda functions integrate directly with API Gateway.

## Technology Stack

### Frontend
- React 18+ with Vite or Create React App
- State management via Context API or Redux Toolkit
- AWS Cognito SDK for authentication
- Deployed to S3 + CloudFront

### Backend (AWS Serverless)
- **API Gateway**: REST API (sole interface, regional mode)
- **Lambda**: Python 3.11+ ONLY, one function per endpoint
- **DynamoDB**: Primary database with GSIs for query patterns
- **Cognito**: User authentication and authorization
- **S3**: Document and receipt storage
- **CloudWatch**: Logging and monitoring
- **IAM**: Role-based access control
- **Region**: us-west-2 ONLY (all AWS resources)

### Infrastructure
- CloudFormation or CDK for IaC
- Separate stacks: dev, staging, production
- ALL resources deployed to us-west-2

## Development Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

### Backend Development
```bash
# Install Lambda dependencies (Python only)
cd functions/<function-name>
pip install -r requirements.txt -t .

# Run unit tests
pytest

# Package Lambda function
zip -r function.zip .
```

### Infrastructure Deployment
```bash
# Deploy entire stack (CloudFormation)
aws cloudformation deploy --template-file template.yaml --stack-name savinggrace-dev

# Deploy with CDK
cdk deploy --profile dev

# Deploy single Lambda function
aws lambda update-function-code --function-name <function-name> --zip-file fileb://function.zip
```

### Testing
```bash
# Run all tests
npm run test:all

# Run unit tests only
npm run test:unit

# Run integration tests
npm run test:integration

# Run e2e tests
npm run test:e2e

# Load testing
npm run test:load
```

## Architecture Principles

### AWS accounts
- All frontend react code must use the 563334150189 AWS account
- All backend infrastructure must use the 921212210452 AWS account
- Secrets are managed in .env
- **ALL AWS resources MUST be deployed to us-west-2 region ONLY**

### Backend Architecture Rules

1. **Direct Lambda Integration**: Every API Gateway endpoint maps directly to a Lambda function. No proxy resources, no catch-all routes.

2. **Function Organization**: One Lambda function per endpoint/operation:
   - `listDonors`, `getDonor`, `createDonor`, `updateDonor`, `deleteDonor`
   - Each function has its own IAM role with least-privilege permissions

3. **API Gateway Configuration**:
   - Use REST API (not HTTP API)
   - Cognito User Pool Authorizer on all endpoints
   - Request/response validation with JSON schemas
   - Enable CORS for frontend domain
   - Enable CloudWatch logging
   - Enable request caching for GET endpoints (5-min TTL)

4. **Lambda Best Practices** (Python 3.11+ ONLY):
   - Use Lambda Layers for shared code (boto3 clients, utilities)
   - Environment variables from Systems Manager Parameter Store
   - Structured JSON logging (use Python logging module)
   - AWS X-Ray tracing enabled
   - Input validation on every request (use pydantic or cerberus)
   - Proper error handling with HTTP status codes (200, 400, 401, 403, 404, 500)
   - Timeout: 30s max, Memory: 512-1024MB
   - Runtime: python3.11 or python3.12

5. **DynamoDB Patterns**:
   - Single-table design with composite keys (PK, SK)
   - GSIs for alternative access patterns
   - Use batch operations where possible
   - Query over Scan
   - Pagination for list operations (50 items per page)
   - Optimistic locking with version attributes

6. **S3 Usage**:
   - Pre-signed URLs for uploads/downloads (no streaming through Lambda)
   - Time-limited URLs (15 minutes)
   - Server-side encryption enabled
   - Versioning enabled
   - No public access

### Frontend Architecture

1. **Component Structure**:
   ```
   /src
     /components      # Reusable components
     /pages          # Route components
     /services       # API client, auth
     /hooks          # Custom React hooks
     /context        # React Context providers
     /utils          # Helper functions
     /types          # TypeScript types
   ```

2. **Authentication Flow**:
   - Cognito JWT tokens stored in memory or httpOnly cookies
   - Refresh token rotation
   - Automatic token refresh before expiry
   - Protected routes via React Router
   - Role-based component rendering

3. **API Client**:
   - Centralized Axios instance with interceptors
   - Automatic auth header injection
   - Error handling and retry logic
   - Request/response logging in dev mode

4. **State Management**:
   - Local state for component-specific data
   - Context for global state (auth, theme, notifications)
   - Fetch data on component mount, cache appropriately
   - Optimistic updates for better UX

## Key Data Models

### DynamoDB Table Structure

**Users**: `PK: USER#<userId>`, `SK: PROFILE`
**Donors**: `PK: DONOR#<donorId>`, `SK: PROFILE`
**Donations**: `PK: DONATION#<donationId>`, `SK: METADATA|ITEM#<itemId>`
**Recipients**: `PK: RECIPIENT#<recipientId>`, `SK: PROFILE`
**Distributions**: `PK: DISTRIBUTION#<distributionId>`, `SK: METADATA|RECIPIENT#<recipientId>`
**Inventory**: `PK: INVENTORY#<category>`, `SK: ITEM#<itemId>` (materialized view)

### Key GSIs
- `DonationsByDonor`: donorId + receivedDate
- `DonationsByDate`: receivedDate (for reports)
- `ItemsByExpiration`: expirationDate (for alerts)
- `DistributionsByDate`: distributionDate
- `DistributionsByRecipient`: recipientId + distributionDate

## API Patterns

### Standard Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "pagination": {
    "nextToken": "...",
    "hasMore": true
  }
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error message",
  "errorCode": "ERROR_CODE",
  "details": { ... }
}
```

### Common HTTP Status Codes
- 200: Success
- 201: Created
- 204: No Content (deletes)
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid/expired token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 409: Conflict (duplicate resource)
- 500: Internal Server Error

## Security Implementation

### Authentication
- All endpoints require Cognito JWT token except auth endpoints
- Token in `Authorization: Bearer <token>` header
- API Gateway validates token via Cognito Authorizer
- User claims available in Lambda event: `event.requestContext.authorizer.claims`

### Authorization (RBAC)
- User role stored in Cognito custom attribute: `custom:role`
- Roles: Admin, Donor Coordinator, Distribution Manager, Volunteer, Read-Only
- Check role in Lambda before processing:
  ```python
  import json

  user_role = event['requestContext']['authorizer']['claims']['custom:role']
  if user_role not in ['Admin', 'DonorCoordinator']:
      return {
          'statusCode': 403,
          'body': json.dumps({'success': False, 'error': 'Forbidden'})
      }
  ```

### Data Protection
- All PII encrypted at rest (DynamoDB, S3)
- TLS 1.2+ for all communication
- No sensitive data in logs or error messages
- Audit trail for all data modifications (createdBy, updatedBy, timestamp)

## Critical Workflows

### Record Donation Workflow
1. Frontend: Select donor from dropdown
2. Frontend: Add food items (name, category, quantity, expiration)
3. Frontend: Upload receipt image (get pre-signed URL from `/donations/upload-url`, POST directly to S3)
4. Frontend: Submit donation via `POST /donations`
5. Lambda: Validate input, insert into Donations table, update Inventory table
6. Lambda: Return donation ID and confirmation

### Create Distribution Workflow
1. Frontend: Select distribution date and location
2. Frontend: Add recipients from list
3. Frontend: Assign inventory items to each recipient (check availability)
4. Frontend: Submit via `POST /distributions`
5. Lambda: Validate inventory availability, reserve items, create distribution record
6. Lambda: Update inventory status to "reserved"
7. Mark complete: `POST /distributions/{id}/complete` updates inventory to "distributed"

### Expiration Alert System
1. Scheduled EventBridge rule triggers Lambda daily
2. Lambda queries `ItemsByExpiration` GSI
3. Find items expiring in 7 days, 3 days, or expired
4. Send notifications via SNS to admins
5. Update dashboard alerts

## Production Readiness Checklist

### Before Deployment
- [ ] All environment variables in Systems Manager
- [ ] IAM roles follow least privilege
- [ ] API Gateway has request validation
- [ ] Lambda functions have X-Ray enabled
- [ ] DynamoDB has point-in-time recovery enabled
- [ ] S3 buckets have encryption and versioning
- [ ] CloudWatch alarms configured (errors, throttling)
- [ ] Cognito has MFA enabled for admins
- [ ] CloudFront has WAF attached
- [ ] All secrets in Secrets Manager (no hardcoded values)

### Deployment Process
1. Deploy infrastructure (CloudFormation/CDK) to staging
2. Run smoke tests against staging
3. Deploy infrastructure to production
4. Build and deploy frontend to S3
5. Invalidate CloudFront cache
6. Monitor CloudWatch for 15 minutes
7. Run post-deployment verification

### Monitoring
- Lambda error rates > 1%: Alert
- API Gateway 5xx > 0.5%: Alert
- DynamoDB throttling: Alert
- Any unauthorized access attempts: Alert
- CloudWatch dashboard with key metrics

## Common Pitfalls to Avoid

1. **DO NOT** create proxy endpoints in API Gateway (no `/{proxy+}`)
2. **DO NOT** use Express or any HTTP framework in Lambda
3. **DO NOT** stream files through Lambda (use pre-signed URLs)
4. **DO NOT** store sensitive data in environment variables (use Secrets Manager)
5. **DO NOT** use overly broad IAM policies (grant only what's needed)
6. **DO NOT** skip input validation (validate in Lambda even if API Gateway validates)
7. **DO NOT** log sensitive data (PII, tokens, passwords)
8. **DO NOT** use Scan on DynamoDB (use Query with proper indexes)
9. **DO NOT** forget pagination on list endpoints (prevent large response payloads)
10. **DO NOT** deploy without testing against staging first

## Performance Optimization

### Frontend
- Code splitting by route
- Lazy load images
- Debounce search inputs
- Cache API responses (React Query or SWR)
- Minimize bundle size (tree shaking, no unused deps)

### Backend
- Lambda provisioned concurrency for critical functions (optional)
- DynamoDB auto-scaling or on-demand mode
- API Gateway response caching (5-min TTL for GET)
- Batch DynamoDB operations where possible
- Use DynamoDB streams for async processing (inventory updates)
- CloudFront caching for frontend assets

## Environment Variables

### Frontend (.env)
```
VITE_API_BASE_URL=https://api.savinggrace.org/dev
VITE_COGNITO_USER_POOL_ID=us-west-2_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_AWS_REGION=us-west-2
```

### Lambda (from Systems Manager)
```
DYNAMODB_TABLE=SavingGrace-Dev
S3_BUCKET=savinggrace-receipts-dev
COGNITO_USER_POOL_ID=us-west-2_xxxxx
AWS_REGION=us-west-2
LOG_LEVEL=INFO
```

## Testing Patterns

### Lambda Unit Test Example (Python with pytest)
```python
import json
import pytest
from unittest.mock import Mock, patch

@patch('boto3.resource')
def test_create_donor_returns_201_on_success(mock_dynamodb):
    # Mock DynamoDB table
    mock_table = Mock()
    mock_dynamodb.return_value.Table.return_value = mock_table
    mock_table.put_item.return_value = {}

    # Create test event
    event = {
        'body': json.dumps({'name': 'Test Donor', 'email': 'test@example.com'})
    }

    # Call handler
    response = handler(event, None)

    # Assert
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['success'] is True
```

### Frontend Component Test
```javascript
// Test with React Testing Library
test('DonorForm submits data correctly', async () => {
  const mockSubmit = jest.fn();
  render(<DonorForm onSubmit={mockSubmit} />);
  fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Test' } });
  fireEvent.click(screen.getByText('Submit'));
  await waitFor(() => {
    expect(mockSubmit).toHaveBeenCalledWith({ name: 'Test' });
  });
});
```

## Debugging

### Frontend Debugging
- React DevTools for component inspection
- Network tab for API request/response
- Console logs in development mode
- Redux DevTools (if using Redux)

### Backend Debugging
- CloudWatch Logs for Lambda execution logs
- X-Ray traces for request flow and bottlenecks
- API Gateway execution logs (enable in settings)
- DynamoDB capacity metrics (throttling)
- Test Lambda locally with SAM CLI: `sam local invoke`
- Use Python debugger (pdb) for local development
- Run pytest with verbose output: `pytest -v`

### Common Issues
- **401 Unauthorized**: Check token expiry, verify Cognito Authorizer config
- **403 Forbidden**: Check user role/permissions in Lambda
- **500 Error**: Check Lambda logs in CloudWatch, look for exceptions
- **Timeout**: Lambda taking > 30s, optimize query or increase timeout
- **Throttling**: DynamoDB read/write capacity exceeded, enable auto-scaling

## Helpful AWS CLI Commands (us-west-2 only)

```bash
# View Lambda logs
aws logs tail /aws/lambda/<function-name> --follow --region us-west-2

# Invoke Lambda function directly
aws lambda invoke --function-name <function-name> --payload '{"test": "data"}' response.json --region us-west-2

# Get API Gateway endpoint
aws apigateway get-rest-apis --query 'items[?name==`SavingGrace`].id' --region us-west-2

# Update Lambda environment variable
aws lambda update-function-configuration --function-name <function-name> --environment Variables={KEY=VALUE} --region us-west-2

# Create DynamoDB backup
aws dynamodb create-backup --table-name <table-name> --backup-name <backup-name> --region us-west-2

# Get CloudWatch metrics
aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=<function-name> --start-time 2024-01-01T00:00:00Z --end-time 2024-01-02T00:00:00Z --period 3600 --statistics Sum --region us-west-2
```

## Project Structure

```
/
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Route pages
│   │   ├── services/      # API client, auth
│   │   ├── hooks/         # Custom hooks
│   │   ├── context/       # Context providers
│   │   ├── utils/         # Helpers
│   │   └── types/         # TypeScript types
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── functions/         # Lambda functions
│   │   ├── donors/
│   │   ├── donations/
│   │   ├── recipients/
│   │   ├── distributions/
│   │   ├── inventory/
│   │   └── reports/
│   ├── layers/            # Lambda layers (shared code)
│   ├── tests/             # Integration tests
│   └── infrastructure/    # CloudFormation/CDK
│
├── docs/                  # Documentation
├── scripts/               # Deployment scripts
├── PRD.md                 # Product requirements
├── CLAUDE.md              # This file
└── README.md              # Project overview
```

## Additional Resources

- AWS Lambda Best Practices: https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- DynamoDB Best Practices: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html
- API Gateway REST API: https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-rest-api.html
- Cognito User Pools: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html


## ❌ NEVER DO THIS

1.  **Create proxy servers** or use FastAPI
2.  **Use Node.js for Lambda functions** - Python 3.11+ ONLY
3.  **Deploy outside us-west-2** - ALL AWS resources must be in us-west-2
4.  **Use any region other than us-west-2** - No exceptions
5.  **Add mock data** except for debugging (delete immediately)
6.  **Create documentation** unless explicitly requested
7.  **Commit code** unless explicitly asked
8.  **Add comments** unless requested
9.  **Use different app names** (only "SavingGrace")
10. **Remove code without dependency analysis** - Always check for helper functions, imports, and cross-references before deletion
11. **Assume property names in API responses** - Always verify actual API structure vs frontend expectations
12. **Create documentation in root directory** - All new .md files must go to /docs/ directory
13. **No shortcuts** - When debugging discover root causes, never insert mock data or create tech debt.
14. **Never create tech debt** - when you see lint issues in the codebase, fix them now. When there's a UI or back end error, fix it now.
15. **NEVER claim functionality works until tested and verified** - Making code changes does NOT mean the system is working. Always test and verify actual behavior before claiming success.
16. **MANDATORY VERIFICATION PROTOCOL** - Before stating "working", "functional", "success", or "complete": (1) Run actual tests, (2) Check actual data exists, (3) Verify end-to-end functionality. NO EXCEPTIONS. 

## ✅ ALWAYS DO THIS

1. **Search before creating** new code
2. **Read files directly** without asking permission
3. **Fix root causes** not symptoms
4. **Test your changes** with existing test suites
5. **Use Python 3.11+ for ALL Lambda functions** - No Node.js
6. **Deploy ALL AWS resources to us-west-2** - No other regions
7. **Follow existing patterns** in the codebase
8. **Run lint/typecheck** before marking complete (pylint, black, mypy for Python)
9. **Use CloudFormation/CDK** for all infrastructure changes (backend/infrastructure/templates/)
10. **Ensure infrastructure is rebuildable** - templates must be complete and error-free
11. **Analyze dependencies before removing code** - Check for helper functions, imports, type definitions
12. **Verify API response structure** - Use print statements or debugger to check actual vs expected property names
13. **Test after any code removal** - Even small deletions can cause cascading failures
14. **BEFORE CLAIMING SUCCESS: Verify actual data exists in database/system** - Never trust API success messages, always check the actual end result
15. **Use pytest for all Python backend tests** - Not unittest or nose
16. **Use boto3 for ALL AWS service interactions** - Direct SDK usage only

