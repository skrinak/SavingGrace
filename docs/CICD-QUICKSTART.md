# CI/CD Quick Start Guide

**Last Updated**: 2025-10-14

## Overview

SavingGrace uses GitHub Actions for automated CI/CD deployment across three environments: **Dev**, **Staging**, and **Production**.

---

## Workflows

### 1. Backend CI/CD
**File**: `.github/workflows/backend-ci.yml`

**Automatic Triggers**:
- Push to `main` branch (changes in `backend/**`)
- Deploys: Dev → Staging (automatic)

**Manual Trigger**:
- Go to: [GitHub Actions → Backend CI/CD](https://github.com/skrinak/SavingGrace/actions/workflows/backend-ci.yml)
- Click: "Run workflow"
- Select environment: `dev`, `staging`, or `prod`
- Click: "Run workflow"

**Stages**:
1. **Test** - Black, Pylint, Mypy, pytest
2. **Deploy Dev** - CDK deploy + smoke tests
3. **Deploy Staging** - CDK deploy + smoke tests
4. **Deploy Prod** - Requires manual approval

---

### 2. Frontend CI/CD
**File**: `.github/workflows/frontend-ci.yml`

**Automatic Triggers**:
- Push to `main` branch (changes in `frontend/**`)
- Deploys: Dev → Staging (automatic)

**Manual Trigger**:
- Go to: [GitHub Actions → Frontend CI/CD](https://github.com/skrinak/SavingGrace/actions/workflows/frontend-ci.yml)
- Click: "Run workflow"
- Select environment: `dev`, `staging`, or `prod`
- Click: "Run workflow"

**Stages**:
1. **Test** - ESLint, TypeScript, Jest
2. **Build** - Production build with environment config
3. **Deploy Dev** - S3 sync + CloudFront invalidation
4. **Deploy Staging** - S3 sync + CloudFront invalidation
5. **Deploy Prod** - Requires manual approval

---

### 3. PR Checks
**File**: `.github/workflows/pr-checks.yml`

**Automatic Triggers**:
- Pull request to `main` or `develop`

**Checks**:
- Backend tests (Black, Pylint, Mypy, pytest)
- Frontend tests (ESLint, TypeScript, Jest)
- Security scans (Trivy, TruffleHog)
- Dependency audits (npm audit, safety)
- CDK synth validation

**Status**: Must pass before PR can be merged

---

## GitHub Secrets Required

### Backend Secrets
```
AWS_BACKEND_ACCESS_KEY_ID       # IAM user for account 921212210452
AWS_BACKEND_SECRET_ACCESS_KEY   # IAM user secret
```

### Frontend Secrets
```
AWS_FRONTEND_ACCESS_KEY_ID      # IAM user for account 563334150189
AWS_FRONTEND_SECRET_ACCESS_KEY  # IAM user secret
```

### Production Secrets
```
PROD_COGNITO_USER_POOL_ID       # Production Cognito User Pool ID
PROD_COGNITO_CLIENT_ID          # Production Cognito Client ID
```

**Configure secrets**:
1. Go to: [Repository Settings → Secrets and variables → Actions](https://github.com/skrinak/SavingGrace/settings/secrets/actions)
2. Click: "New repository secret"
3. Add each secret above

---

## Common Workflows

### Deploy to Dev (Automatic)
```bash
# Make changes
git add .
git commit -m "feat: my feature"
git push origin main

# GitHub Actions automatically:
# 1. Runs tests
# 2. Deploys to dev
# 3. Runs smoke tests
```

### Deploy to Staging (Automatic)
```bash
# After dev deployment succeeds:
# GitHub Actions automatically:
# 1. Deploys to staging
# 2. Runs smoke tests
```

### Deploy to Production (Manual)
```bash
# 1. Ensure staging is tested and verified
# 2. Go to GitHub Actions
# 3. Select "Backend CI/CD" or "Frontend CI/CD"
# 4. Click "Run workflow"
# 5. Select environment: "prod"
# 6. Click "Run workflow"
# 7. Wait for approval prompt
# 8. Click "Approve and deploy"
# 9. Monitor CloudWatch for 15 minutes
```

### Create Pull Request
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and commit
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature

# 3. Create PR on GitHub
# 4. Wait for PR checks to pass
# 5. Request review
# 6. Merge after approval
```

---

## Monitoring Deployments

### View Workflow Status
- Go to: [GitHub Actions](https://github.com/skrinak/SavingGrace/actions)
- See all running and completed workflows
- Click on a workflow to see detailed logs

### View CloudWatch Dashboards
- **Dev**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-dev
- **Staging**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-staging
- **Prod**: https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-prod

### Check Health Endpoints
```bash
# Dev
curl https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/health

# Staging
curl https://8wg0ijp4ld.execute-api.us-west-2.amazonaws.com/staging/health

# Production (placeholder)
curl https://api.savinggrace.org/prod/health
```

---

## Rollback Procedures

### Backend Rollback
```bash
# Option 1: Redeploy from last known good commit
git checkout <LAST_GOOD_COMMIT>

# Trigger manual deployment via GitHub Actions
# Go to: Backend CI/CD → Run workflow → Select environment

# Option 2: CloudFormation rollback
aws cloudformation rollback-stack \
  --stack-name SavingGrace-Lambda-<env> \
  --region us-west-2
```

### Frontend Rollback
```bash
# Option 1: Redeploy from last known good commit
git checkout <LAST_GOOD_COMMIT>

# Trigger manual deployment via GitHub Actions
# Go to: Frontend CI/CD → Run workflow → Select environment

# Option 2: S3 versioning rollback
aws s3 cp s3://savinggrace-frontend-<env>-563334150189/ \
  s3://savinggrace-frontend-<env>-563334150189/ \
  --recursive \
  --version-id <VERSION_ID>
```

---

## Troubleshooting

### Workflow Failed with "403 Forbidden"
**Cause**: IAM credentials in GitHub Secrets are incorrect or expired

**Fix**:
1. Verify IAM user exists in AWS
2. Check IAM policy allows required actions
3. Update GitHub Secrets with new credentials

### Smoke Tests Failed
**Cause**: Health endpoint not responding

**Fix**:
1. Check CloudWatch logs for errors
2. Verify Lambda function deployed successfully
3. Check API Gateway configuration
4. Manually test health endpoint

### CDK Deploy Failed
**Cause**: Stack in UPDATE_FAILED state

**Fix**:
1. Check CloudFormation stack status
2. Force update: `cdk deploy --all --force`
3. If persistent, delete stack and redeploy

---

## Best Practices

### Before Merging to Main
- ✅ All PR checks passed
- ✅ Code reviewed and approved
- ✅ Tests written and passing
- ✅ Documentation updated

### Before Production Deployment
- ✅ Staging tested and verified
- ✅ Stakeholders notified
- ✅ Release notes prepared
- ✅ Rollback plan ready
- ✅ Monitor CloudWatch for 15+ minutes after deployment

### After Deployment
- ✅ Verify health endpoints
- ✅ Test critical workflows
- ✅ Monitor CloudWatch alarms
- ✅ Notify stakeholders of success

---

## Support

For CI/CD issues:
- **DevOps**: ops@savinggrace.org
- **GitHub Issues**: https://github.com/skrinak/SavingGrace/issues

---

**Quick Links**:
- [Full Deployment Guide](DEPLOYMENT.md)
- [Operations Runbook](../RUNBOOK.md)
- [GitHub Actions](https://github.com/skrinak/SavingGrace/actions)
- [CloudWatch Dashboards](https://console.aws.amazon.com/cloudwatch/home?region=us-west-2)
