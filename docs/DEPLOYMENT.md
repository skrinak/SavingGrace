# SavingGrace Deployment Guide

**Last Updated**: 2025-10-14
**Version**: 1.0

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Manual Deployment](#manual-deployment)
5. [Deployment Environments](#deployment-environments)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)

---

## Overview

SavingGrace uses GitHub Actions for automated CI/CD deployment across three environments:

- **Dev**: Automatic deployment on push to `main` branch
- **Staging**: Automatic deployment after successful dev deployment
- **Production**: Manual approval required, triggered via workflow dispatch

### Architecture

- **Backend**: AWS CDK → Lambda + API Gateway + DynamoDB (Account: 921212210452)
- **Frontend**: React + Vite → S3 + CloudFront (Account: 563334150189)
- **Region**: us-west-2 ONLY

---

## Prerequisites

### GitHub Secrets Configuration

Configure the following secrets in GitHub repository settings:

#### Backend Secrets (Account: 921212210452)
```
AWS_BACKEND_ACCESS_KEY_ID
AWS_BACKEND_SECRET_ACCESS_KEY
```

#### Frontend Secrets (Account: 563334150189)
```
AWS_FRONTEND_ACCESS_KEY_ID
AWS_FRONTEND_SECRET_ACCESS_KEY
```

#### Production Secrets
```
PROD_COGNITO_USER_POOL_ID
PROD_COGNITO_CLIENT_ID
```

### IAM Permissions Required

**Backend IAM User**:
- CloudFormation full access
- Lambda full access
- API Gateway full access
- DynamoDB full access
- S3 full access (for CDK assets)
- IAM role creation/attachment
- CloudWatch Logs full access
- Cognito full access

**Frontend IAM User**:
- S3 full access (specific buckets)
- CloudFront cache invalidation
- CloudFront distribution read access

### Local Development Prerequisites

- AWS CLI v2
- AWS CDK v2.100+
- Python 3.11+
- Node.js 20+
- UV package manager

---

## CI/CD Pipeline

### Pipeline Workflows

SavingGrace has three GitHub Actions workflows:

#### 1. Backend CI/CD (`.github/workflows/backend-ci.yml`)

**Triggers**:
- Push to `main` branch (paths: `backend/**`)
- Manual dispatch with environment selection

**Stages**:
1. **Test**: Runs Black, Pylint, Mypy, pytest with coverage
2. **Deploy Dev**: CDK deploy to dev environment + smoke tests
3. **Deploy Staging**: CDK deploy to staging + smoke tests
4. **Deploy Prod**: Requires manual approval + extended monitoring
5. **Rollback**: Automatic notification on failure

**Example Usage**:
```bash
# Automatic: Push to main triggers dev → staging
git push origin main

# Manual: Deploy to production
# Go to GitHub Actions → Backend CI/CD → Run workflow → Select 'prod'
```

#### 2. Frontend CI/CD (`.github/workflows/frontend-ci.yml`)

**Triggers**:
- Push to `main` branch (paths: `frontend/**`)
- Manual dispatch with environment selection

**Stages**:
1. **Test**: ESLint, TypeScript, Jest unit tests
2. **Build**: Production build with environment-specific config
3. **Deploy Dev**: S3 sync + CloudFront invalidation
4. **Deploy Staging**: S3 sync + CloudFront invalidation
5. **Deploy Prod**: Requires manual approval + verification

**Example Usage**:
```bash
# Automatic: Push to main triggers dev → staging
git push origin main

# Manual: Deploy to production
# Go to GitHub Actions → Frontend CI/CD → Run workflow → Select 'prod'
```

#### 3. PR Checks (`.github/workflows/pr-checks.yml`)

**Triggers**:
- Pull request to `main` or `develop`

**Checks**:
- Backend tests (Black, Pylint, Mypy, pytest)
- Frontend tests (ESLint, TypeScript, Jest, build)
- Security scans (Trivy, TruffleHog)
- Dependency audits (npm audit, safety)
- CDK synth validation (all environments)

---

## Manual Deployment

### Backend Deployment

#### Deploy to Dev
```bash
cd backend/infrastructure
source ../.venv/bin/activate

# Verify AWS account
aws sts get-caller-identity
# Expected: Account 921212210452

# Deploy all stacks
cdk deploy --all -c env=dev --region us-west-2

# Verify deployment
curl https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/health
```

#### Deploy to Staging
```bash
cd backend/infrastructure
source ../.venv/bin/activate

# Deploy all stacks
cdk deploy --all -c env=staging --region us-west-2

# Verify deployment
curl https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging/health
```

#### Deploy to Production
```bash
cd backend/infrastructure
source ../.venv/bin/activate

# IMPORTANT: Always deploy to staging first and verify

# Deploy all stacks
cdk deploy --all -c env=prod --region us-west-2

# Verify deployment
curl https://api.savinggrace.org/prod/health

# Monitor CloudWatch for 15 minutes
# https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-prod
```

### Frontend Deployment

#### Deploy to Dev
```bash
cd frontend

# Build with dev config
VITE_API_BASE_URL=https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev \
VITE_COGNITO_USER_POOL_ID=us-west-2_DeQrm3GHa \
VITE_COGNITO_CLIENT_ID=pn75f7u9cqsunkje417vtqvvf \
VITE_AWS_REGION=us-west-2 \
npm run build

# Verify AWS account
aws sts get-caller-identity
# Expected: Account 563334150189

# Deploy to S3
aws s3 sync dist/ s3://savinggrace-frontend-dev-563334150189 \
  --delete \
  --region us-west-2

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <DEV_DISTRIBUTION_ID> \
  --paths "/*" \
  --region us-east-1
```

#### Deploy to Staging
```bash
cd frontend

# Build with staging config
VITE_API_BASE_URL=https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging \
VITE_COGNITO_USER_POOL_ID=us-west-2_OnYDSY7gU \
VITE_COGNITO_CLIENT_ID=1jq9uia6llqmtpkqqpsecvsskm \
VITE_AWS_REGION=us-west-2 \
npm run build

# Deploy to S3
aws s3 sync dist/ s3://savinggrace-frontend-staging-563334150189 \
  --delete \
  --region us-west-2

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <STAGING_DISTRIBUTION_ID> \
  --paths "/*" \
  --region us-east-1
```

#### Deploy to Production
```bash
cd frontend

# IMPORTANT: Always deploy to staging first and verify

# Build with production config
VITE_API_BASE_URL=https://api.savinggrace.org/prod \
VITE_COGNITO_USER_POOL_ID=<PROD_USER_POOL_ID> \
VITE_COGNITO_CLIENT_ID=<PROD_CLIENT_ID> \
VITE_AWS_REGION=us-west-2 \
npm run build

# Deploy to S3
aws s3 sync dist/ s3://savinggrace-frontend-prod-563334150189 \
  --delete \
  --region us-west-2

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <PROD_DISTRIBUTION_ID> \
  --paths "/*" \
  --region us-east-1

# Verify deployment
curl https://app.savinggrace.org
```

---

## Deployment Environments

### Dev Environment

**Purpose**: Active development and testing

**Backend**:
- API: https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev
- Cognito Pool: us-west-2_DeQrm3GHa
- Account: 921212210452

**Frontend**:
- URL: https://d1234567890abc.cloudfront.net (placeholder)
- S3 Bucket: savinggrace-frontend-dev-563334150189
- Account: 563334150189

**Deployment**: Automatic on push to `main`

**Data**: Test data, frequently reset

---

### Staging Environment

**Purpose**: Pre-production validation, identical to production

**Backend**:
- API: https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging
- Cognito Pool: us-west-2_OnYDSY7gU
- Account: 921212210452

**Frontend**:
- URL: https://staging.savinggrace.org (placeholder)
- S3 Bucket: savinggrace-frontend-staging-563334150189
- Account: 563334150189

**Deployment**: Automatic after successful dev deployment

**Data**: Realistic test data, preserved

**Test Users**:
- admin@staging.test (Admin)
- donor@staging.test (DonorCoordinator)
- distribution@staging.test (DistributionManager)

---

### Production Environment

**Purpose**: Live customer-facing application

**Backend**:
- API: https://api.savinggrace.org (placeholder)
- Cognito Pool: TBD (created during prod deployment)
- Account: 921212210452

**Frontend**:
- URL: https://app.savinggrace.org (placeholder)
- S3 Bucket: savinggrace-frontend-prod-563334150189
- Account: 563334150189

**Deployment**: Manual approval required via GitHub Actions

**Data**: Real customer data, strict change control

**Monitoring**: 24/7 CloudWatch alarms, PagerDuty integration

---

## Rollback Procedures

### Backend Rollback

#### Automatic Rollback
If CDK deployment fails, CloudFormation automatically rolls back to last stable state.

#### Manual Rollback
```bash
cd backend/infrastructure
source ../.venv/bin/activate

# Method 1: Redeploy from last known good commit
git checkout <LAST_GOOD_COMMIT>
cdk deploy --all -c env=<ENVIRONMENT> --region us-west-2

# Method 2: Use CloudFormation stack rollback
aws cloudformation rollback-stack \
  --stack-name SavingGrace-Lambda-<env> \
  --region us-west-2
```

#### Verify Rollback
```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name SavingGrace-Lambda-<env> \
  --query 'Stacks[0].StackStatus' \
  --region us-west-2

# Test health endpoint
curl https://<API_URL>/<env>/health
```

### Frontend Rollback

#### Manual Rollback
```bash
# Method 1: Redeploy from last known good commit
git checkout <LAST_GOOD_COMMIT>
cd frontend
npm run build
aws s3 sync dist/ s3://savinggrace-frontend-<env>-563334150189 --delete

# Method 2: Restore from S3 versioning
aws s3 cp s3://savinggrace-frontend-<env>-563334150189/ \
  s3://savinggrace-frontend-<env>-563334150189/ \
  --recursive \
  --version-id <VERSION_ID>

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --paths "/*"
```

#### Verify Rollback
```bash
# Wait for CloudFront invalidation
sleep 60

# Test frontend
curl https://<FRONTEND_URL>

# Verify in browser
open https://<FRONTEND_URL>
```

---

## Troubleshooting

### Common Deployment Issues

#### Issue 1: CDK Deploy Fails with "Stack already exists"

**Error**:
```
Stack SavingGrace-Lambda-dev already exists in UPDATE_FAILED state
```

**Solution**:
```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name SavingGrace-Lambda-dev \
  --query 'Stacks[0].StackStatus'

# If UPDATE_FAILED or ROLLBACK_COMPLETE, continue update
cdk deploy --all -c env=dev --force --region us-west-2
```

---

#### Issue 2: Lambda Deployment Fails with "Code size too large"

**Error**:
```
InvalidParameterValueException: Unzipped size must be smaller than 262144000 bytes
```

**Solution**:
```bash
# Check Lambda layer size
cd backend/lambda_layer
du -sh python/

# Reduce dependencies or split into multiple layers
# Remove unnecessary packages from requirements.txt
```

---

#### Issue 3: CloudFront Invalidation Takes Too Long

**Issue**: Cache invalidation can take 5-15 minutes

**Solution**:
```bash
# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --id <INVALIDATION_ID>

# For immediate testing, use cache-busting query params
curl https://<FRONTEND_URL>/?v=$(date +%s)
```

---

#### Issue 4: GitHub Actions Fails with "403 Forbidden"

**Error**:
```
An error occurred (AccessDenied) when calling the PutObject operation
```

**Solution**:
```bash
# Verify IAM credentials in GitHub Secrets
# Check IAM policy allows required actions

# Test credentials locally
export AWS_ACCESS_KEY_ID=<KEY_ID>
export AWS_SECRET_ACCESS_KEY=<SECRET_KEY>
aws sts get-caller-identity
```

---

#### Issue 5: Smoke Tests Fail After Deployment

**Error**:
```
ERROR: Health check failed with status 502
```

**Investigation**:
```bash
# Check API Gateway logs
aws logs tail /aws/apigateway/SavingGrace-API-<env> \
  --follow \
  --region us-west-2

# Check Lambda logs
aws logs tail /aws/lambda/SavingGrace-health-<env> \
  --follow \
  --region us-west-2

# Check recent CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name SavingGrace-API-<env> \
  --max-items 20 \
  --region us-west-2
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally (`npm test`, `pytest`)
- [ ] Code reviewed and approved
- [ ] PR checks passed in GitHub Actions
- [ ] Staging environment tested and verified
- [ ] Release notes prepared
- [ ] Stakeholders notified

### During Deployment

- [ ] Verify correct AWS account (dev: 921212210452, frontend: 563334150189)
- [ ] Monitor deployment logs in real-time
- [ ] Watch CloudWatch dashboard for errors
- [ ] Verify health endpoints respond (200 OK)
- [ ] Test critical workflows manually

### Post-Deployment

- [ ] Smoke tests passed
- [ ] Monitor CloudWatch for 15 minutes (prod: 24 hours)
- [ ] Verify no alarms triggered
- [ ] Test critical user workflows
- [ ] Update deployment documentation
- [ ] Notify stakeholders of successful deployment

---

## Monitoring Post-Deployment

### CloudWatch Dashboards

- **Dev**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-dev
- **Staging**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-staging
- **Production**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-prod

### Key Metrics to Monitor

| Metric | Normal Range | Action Threshold |
|--------|--------------|------------------|
| API Gateway 5XX Errors | 0 | > 0.5% |
| Lambda Errors | 0-1% | > 1% |
| Lambda Duration (p99) | < 1s | > 2s |
| DynamoDB Throttles | 0 | > 0 |
| API Latency (p99) | < 500ms | > 1s |

### Alarm Notifications

**Critical Alarms** → SNS Topic → Email/SMS
**Warning Alarms** → SNS Topic → Email
**Expiration Alerts** → SNS Topic → Email

---

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| DevOps Lead | ops@savinggrace.org | 24/7 |
| Backend Developer | backend@savinggrace.org | Business hours |
| Frontend Developer | frontend@savinggrace.org | Business hours |
| AWS Support | AWS Console | 24/7 (Business plan) |

---

## Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SavingGrace Operations Runbook](../RUNBOOK.md)
- [SavingGrace Security Guide](../SECURITY.md)

---

**Document Owner**: DevOps Team
**Last Review**: 2025-10-14
**Next Review**: 2026-01-14
