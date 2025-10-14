# SavingGrace

![Backend CI/CD](https://github.com/skrinak/SavingGrace/actions/workflows/backend-ci.yml/badge.svg)
![Frontend CI/CD](https://github.com/skrinak/SavingGrace/actions/workflows/frontend-ci.yml/badge.svg)
![PR Checks](https://github.com/skrinak/SavingGrace/actions/workflows/pr-checks.yml/badge.svg)

**Food Donation Tracking and Distribution Platform for Non-Profit Organizations**

SavingGrace is a production-ready web application that helps food banks and non-profit organizations track donations, manage inventory, coordinate distributions, and measure impact.

---

## Features

### Core Functionality
- 📦 **Donation Tracking**: Record donations with receipt upload, expiration tracking, and donor management
- 🏪 **Inventory Management**: Real-time inventory tracking with expiration alerts and FIFO recommendations
- 🎁 **Distribution Coordination**: Manage food distributions to recipients with inventory validation
- 📊 **Impact Reporting**: Comprehensive dashboards showing donations, distributions, and waste reduction metrics
- 👥 **User Management**: Role-based access control for Admin, Donor Coordinators, Distribution Managers, Volunteers, and Read-Only users

### Technical Highlights
- ⚡ **Serverless Architecture**: AWS Lambda + API Gateway + DynamoDB for scalable, cost-effective operations
- 🔒 **Enterprise Security**: Cognito authentication, MFA support, encryption at rest and in transit
- 📱 **Modern Frontend**: React 18 with responsive design for desktop and mobile
- 🚀 **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions
- 📈 **Comprehensive Monitoring**: CloudWatch dashboards, alarms, and operational runbooks

---

## Quick Start

### Prerequisites

- **AWS Accounts**:
  - Backend: 921212210452
  - Frontend: 563334150189
- **Tools**:
  - AWS CLI v2
  - AWS CDK v2.100+
  - Python 3.11+
  - Node.js 20+
  - UV package manager

### Installation

#### Backend Setup
```bash
# Clone repository
git clone git@github.com:skrinak/SavingGrace.git
cd SavingGrace/backend

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Deploy infrastructure
cd infrastructure
cdk deploy --all -c env=dev --region us-west-2
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API endpoints and Cognito details

# Start development server
npm run dev

# Build for production
npm run build
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                    S3 + CloudFront (CDN)                         │
│                   Account: 563334150189                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (REST)                          │
│                  Cognito User Pool Authorizer                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Invoke
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lambda Functions (35)                         │
│         Donors | Donations | Recipients | Distributions         │
│              Inventory | Reports | Users                        │
└──────┬──────────────────────────────────────────────┬───────────┘
       │                                              │
       │ Read/Write                                   │ Upload
       ▼                                              ▼
┌──────────────────┐                          ┌─────────────────┐
│    DynamoDB      │                          │   S3 Buckets    │
│   (6 Tables)     │                          │   (Receipts)    │
└──────────────────┘                          └─────────────────┘

                    Backend Account: 921212210452
                    Region: us-west-2 ONLY
```

### Technology Stack

**Frontend**:
- React 18 + Vite
- TypeScript
- Tailwind CSS
- AWS Amplify (Cognito SDK)

**Backend**:
- AWS CDK (Infrastructure as Code)
- Python 3.11 Lambda Functions
- API Gateway REST API
- DynamoDB (6 tables with GSIs)
- Cognito User Pools
- S3 (receipt storage)
- CloudWatch (monitoring & logging)

---

## Project Structure

```
SavingGrace/
├── backend/
│   ├── functions/              # Lambda functions (35)
│   │   ├── donors/
│   │   ├── donations/
│   │   ├── recipients/
│   │   ├── distributions/
│   │   ├── inventory/
│   │   ├── reports/
│   │   └── users/
│   ├── lambda_layer/           # Shared utilities
│   ├── infrastructure/         # AWS CDK stacks
│   │   └── stacks/
│   │       ├── database_stack.py
│   │       ├── storage_stack.py
│   │       ├── auth_stack.py
│   │       ├── api_stack.py
│   │       ├── lambda_layer_stack.py
│   │       ├── lambda_stack.py
│   │       └── monitoring_stack.py
│   └── tests/                  # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API client, auth
│   │   ├── hooks/              # Custom hooks
│   │   └── context/            # React Context
│   └── tests/                  # Frontend tests
├── .github/
│   └── workflows/              # CI/CD pipelines
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       └── pr-checks.yml
├── docs/                       # Documentation
│   ├── DEPLOYMENT.md
│   └── API.md
├── scripts/                    # Deployment scripts
├── PRD.md                      # Product Requirements
├── CLAUDE.md                   # Developer Guide
├── TASKS.md                    # Task Tracking
├── RUNBOOK.md                  # Operations Guide
└── SECURITY.md                 # Security Documentation
```

---

## Deployment

### Environments

| Environment | Backend API | Frontend URL | Purpose |
|-------------|-------------|--------------|---------|
| **Dev** | https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev | TBD | Active development |
| **Staging** | https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging | TBD | Pre-production testing |
| **Production** | https://api.savinggrace.org | https://app.savinggrace.org | Live customer-facing |

### CI/CD Pipeline

**Automatic Deployment** (on push to `main`):
1. Run tests (Black, Pylint, Mypy, pytest, ESLint, Jest)
2. Deploy to Dev → Run smoke tests
3. Deploy to Staging → Run smoke tests

**Production Deployment** (manual approval required):
1. Go to GitHub Actions
2. Select workflow (Backend or Frontend CI/CD)
3. Click "Run workflow"
4. Choose environment: `prod`
5. Approve deployment
6. Monitor CloudWatch for 15 minutes

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment guide.

---

## Testing

### Backend Tests
```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=functions --cov=lambda_layer --cov-report=html

# Run specific test
pytest tests/test_donors.py -v
```

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e
```

### Integration Tests
```bash
# Run E2E integration tests
cd backend
pytest tests/integration/ -v

# Performance tests
npm run test:performance
```

---

## Monitoring

### CloudWatch Dashboards

- **Dev**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-dev)
- **Staging**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-staging)
- **Production**: [CloudWatch Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-prod)

### Key Metrics

| Metric | Threshold | Alarm |
|--------|-----------|-------|
| Lambda Errors | > 1% | Critical |
| API 5XX Errors | > 0.5% | Critical |
| API Latency (p99) | > 1s | Warning |
| DynamoDB Throttles | > 0 | Critical |

### Alarm Notifications

Subscribe to SNS topics for alerts:
```bash
# Critical alerts (errors, outages)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:921212210452:savinggrace-critical-alerts-prod \
  --protocol email \
  --notification-endpoint ops@savinggrace.org

# Warning alerts (performance degradation)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:921212210452:savinggrace-warning-alerts-prod \
  --protocol email \
  --notification-endpoint ops@savinggrace.org
```

---

## Security

### Authentication & Authorization

- **Cognito User Pools**: JWT token-based authentication
- **MFA**: Required for admin users, optional for others
- **Role-Based Access Control (RBAC)**: 5 roles with granular permissions
  - Admin
  - Donor Coordinator
  - Distribution Manager
  - Volunteer
  - Read-Only

### Data Protection

- **Encryption at Rest**: DynamoDB and S3 with AWS KMS
- **Encryption in Transit**: TLS 1.2+ for all communication
- **PII Protection**: Masked in logs, audit trails for all access
- **GDPR Compliance**: Data portability and right to deletion implemented

### Security Audits

```bash
# Run security audit
cd backend
./scripts/security-audit.sh

# Check for secrets in code
cd ..
./scripts/check-secrets.sh
```

See [SECURITY.md](SECURITY.md) for full security documentation.

---

## API Documentation

### Base URLs

- Dev: `https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev`
- Staging: `https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging`
- Production: `https://api.savinggrace.org/prod`

### Authentication

All endpoints require Cognito JWT token in `Authorization` header:
```
Authorization: Bearer <token>
```

### Example API Calls

#### Health Check
```bash
curl https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/health
```

#### List Donors
```bash
curl -H "Authorization: Bearer <token>" \
  https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/donors
```

#### Create Donation
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"donorId": "abc123", "items": [...]}' \
  https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/donations
```

See [API.md](docs/API.md) for full API documentation.

---

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and write tests
3. Run linting and tests: `npm run lint && npm test`
4. Commit changes: `git commit -m "feat: add my feature"`
5. Push branch: `git push origin feature/my-feature`
6. Create Pull Request
7. PR checks must pass (tests, security, CDK synth)
8. Require at least 1 approval
9. Merge to `main`

### Code Quality

**Backend**:
- Black formatter (line length: 100)
- Pylint (score ≥ 8.0)
- Mypy type checking
- pytest (coverage ≥ 80%)

**Frontend**:
- ESLint (Airbnb config)
- Prettier
- TypeScript strict mode
- Jest (coverage ≥ 80%)

---

## Troubleshooting

### Common Issues

**Issue**: CDK deploy fails with "Stack already exists"
```bash
# Solution: Force update
cdk deploy --all -c env=dev --force --region us-west-2
```

**Issue**: Lambda deployment fails with "Code size too large"
```bash
# Solution: Reduce dependencies or use Lambda layers
cd backend/lambda_layer
du -sh python/
```

**Issue**: Frontend shows "Network Error"
```bash
# Solution: Check CORS configuration in API Gateway
# Verify .env file has correct API_BASE_URL
```

See [RUNBOOK.md](RUNBOOK.md) for comprehensive troubleshooting guide.

---

## Documentation

- [Product Requirements (PRD.md)](PRD.md) - Product requirements and user personas
- [Developer Guide (CLAUDE.md)](CLAUDE.md) - Architecture patterns and best practices
- [Task Tracking (TASKS.md)](TASKS.md) - Development task list (27/30 complete, 90%)
- [Deployment Guide (docs/DEPLOYMENT.md)](docs/DEPLOYMENT.md) - CI/CD and deployment procedures
- [Operations Runbook (RUNBOOK.md)](RUNBOOK.md) - Incident response and routine operations
- [Security Guide (SECURITY.md)](SECURITY.md) - Security audit and compliance

---

## License

Copyright © 2025 SavingGrace. All rights reserved.

---

## Support

For technical support or questions:

- **DevOps**: ops@savinggrace.org
- **Development**: dev@savinggrace.org
- **Security**: security@savinggrace.org

For urgent production issues, see [Emergency Contacts](RUNBOOK.md#emergency-contacts).

---

## Acknowledgments

Built with:
- [AWS CDK](https://aws.amazon.com/cdk/)
- [React](https://react.dev/)
- [Python](https://www.python.org/)
- [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

**Project Status**: 90% Complete (27/30 tasks)
**Last Updated**: 2025-10-14
**Version**: 1.0.0
