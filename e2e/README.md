# End-to-End Testing for SavingGrace

This directory contains E2E tests for the SavingGrace application using Playwright and Artillery for performance testing.

## Overview

- **Framework**: Playwright
- **Performance Testing**: Artillery
- **Browsers**: Chromium, Firefox, WebKit (Safari)
- **Test Organization**: Tests are organized by feature area

## Directory Structure

```
e2e/
├── auth/                     # Authentication and authorization tests
│   ├── login.spec.ts
│   └── authorization.spec.ts
├── donors/                   # Donor management tests
├── donations/                # Donation workflow tests
│   └── donation-workflow.spec.ts
├── recipients/               # Recipient management tests
├── distributions/            # Distribution workflow tests
│   └── distribution-workflow.spec.ts
├── inventory/                # Inventory management tests
├── reports/                  # Reports and dashboard tests
└── utils/                    # Shared utilities and helpers
    ├── auth.helper.ts
    ├── api.helper.ts
    └── fixtures.ts
```

## Prerequisites

1. **Backend API deployed**: Ensure the backend API is deployed and accessible
2. **Frontend deployed**: Frontend should be deployed to CloudFront or running locally
3. **Test users created**: Test users for each role should be created in Cognito

## Setup

### Environment Variables

Create a `.env.test` file in the project root:

```bash
# Frontend URL
FRONTEND_URL=https://d1234567890.cloudfront.net
# or for local testing:
# FRONTEND_URL=http://localhost:5173

# Backend API URL
API_URL=https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev

# Test user credentials
TEST_ADMIN_EMAIL=admin@savinggrace.test
TEST_ADMIN_PASSWORD=AdminPassword123!

TEST_COORDINATOR_EMAIL=coordinator@savinggrace.test
TEST_COORDINATOR_PASSWORD=Coordinator123!

TEST_MANAGER_EMAIL=manager@savinggrace.test
TEST_MANAGER_PASSWORD=Manager123!
```

### Install Dependencies

```bash
npm install
```

### Install Playwright Browsers

```bash
npx playwright install
```

## Running Tests

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Specific Test File

```bash
npx playwright test e2e/auth/login.spec.ts
```

### Run Tests in Specific Browser

```bash
# Chromium only
npx playwright test --project=chromium

# Firefox only
npx playwright test --project=firefox

# WebKit only
npx playwright test --project=webkit
```

### Run Tests in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### Run Tests in Debug Mode

```bash
npx playwright test --debug
```

### Run Tests with UI Mode

```bash
npx playwright test --ui
```

## Performance Testing with Artillery

### Run Performance Tests

```bash
# Run against dev environment
npm run test:performance

# Run against specific environment
npx artillery run --environment staging artillery.yml

# Run with custom config
API_URL=https://api.example.com npx artillery run artillery.yml
```

### Performance Test Scenarios

The Artillery configuration includes:

1. **Health Check** (10% weight) - Basic endpoint availability
2. **User Authentication** (20% weight) - Login flow
3. **List Donors** (15% weight) - Read operations
4. **List Donations** (15% weight) - Read with filters
5. **Check Inventory** (20% weight) - Inventory queries
6. **Dashboard Metrics** (15% weight) - Reporting queries
7. **Create Donation** (5% weight) - Write operations

### Performance Targets

- **p95 response time**: < 500ms
- **p99 response time**: < 1000ms
- **Max response time**: < 2000ms
- **Error rate**: < 1%
- **Concurrent users**: 100 users sustained

## Test Users

The tests expect the following test users to exist in Cognito:

| Role                  | Email                        | Password            |
|-----------------------|------------------------------|---------------------|
| Admin                 | admin@savinggrace.test       | AdminPassword123!   |
| Donor Coordinator     | coordinator@savinggrace.test | Coordinator123!     |
| Distribution Manager  | manager@savinggrace.test     | Manager123!         |
| Volunteer             | volunteer@savinggrace.test   | Volunteer123!       |
| Read-Only             | readonly@savinggrace.test    | ReadOnly123!        |

### Creating Test Users

Use the AWS Cognito console or AWS CLI to create test users:

```bash
# Create admin user
aws cognito-idp admin-create-user \
  --user-pool-id us-west-2_XXXXXXXX \
  --username admin@savinggrace.test \
  --user-attributes Name=email,Value=admin@savinggrace.test Name=email_verified,Value=true Name=custom:role,Value=Admin \
  --temporary-password TempPassword123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-west-2_XXXXXXXX \
  --username admin@savinggrace.test \
  --password AdminPassword123! \
  --permanent
```

## Test Reports

### Playwright Reports

After test execution, view the HTML report:

```bash
npx playwright show-report
```

Reports include:
- Test results (pass/fail)
- Screenshots on failure
- Videos on failure
- Traces for debugging

### Artillery Reports

Artillery generates performance reports:

```bash
# View report
open artillery-report.html

# Generate JSON report
npx artillery run --output report.json artillery.yml
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e
        env:
          FRONTEND_URL: ${{ secrets.FRONTEND_URL }}
          API_URL: ${{ secrets.API_URL }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on data from other tests
2. **Data Cleanup**: Tests should clean up any test data they create
3. **Stable Selectors**: Use `data-testid` attributes for reliable element selection
4. **Wait for Elements**: Use Playwright's built-in waiting mechanisms
5. **Realistic Data**: Use fixtures that resemble production data
6. **Performance Budget**: Monitor test execution time and optimize slow tests

## Troubleshooting

### Tests Failing with Timeout

Increase timeout in `playwright.config.ts`:

```typescript
timeout: 60 * 1000, // 60 seconds
```

### Authentication Issues

Verify test users exist and credentials are correct:

```bash
aws cognito-idp admin-get-user \
  --user-pool-id us-west-2_XXXXXXXX \
  --username admin@savinggrace.test
```

### CORS Errors

Ensure CloudFront URL is added to API Gateway CORS allowed origins:

```bash
./scripts/update-api-cors.sh dev
```

### Debugging Failed Tests

1. Run in headed mode: `npx playwright test --headed`
2. Run in debug mode: `npx playwright test --debug`
3. View trace: `npx playwright show-trace trace.zip`
4. Check screenshots in `test-results/`

## Contributing

When adding new E2E tests:

1. Place tests in the appropriate feature directory
2. Use shared utilities from `e2e/utils/`
3. Follow existing test patterns
4. Add test data to fixtures
5. Update this README if adding new test categories

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Artillery Documentation](https://www.artillery.io/docs)
- [AWS Cognito CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/cognito-idp/)
