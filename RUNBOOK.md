# SavingGrace Operations Runbook

**Last Updated**: 2025-10-14
**Version**: 1.0

## Table of Contents

1. [Overview](#overview)
2. [Monitoring](#monitoring)
3. [Common Incidents](#common-incidents)
4. [Emergency Procedures](#emergency-procedures)
5. [Routine Operations](#routine-operations)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This runbook provides operational procedures for the SavingGrace platform.

### System Architecture

- **Frontend**: CloudFront + S3 (Account: 563334150189)
- **Backend**: API Gateway + Lambda + DynamoDB (Account: 921212210452)
- **Region**: us-west-2
- **Environment**: dev, staging, prod

### Key Resources

| Resource | Identifier |
|----------|------------|
| API Gateway | `https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/` |
| Cognito User Pool | `us-west-2_DeQrm3GHa` |
| DynamoDB Tables | `SavingGrace-{Resource}-{env}` |
| S3 Buckets | `savinggrace-{purpose}-{env}-{account}` |

---

## Monitoring

### CloudWatch Dashboard

Access the main dashboard:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-west-2#dashboards:name=SavingGrace-dev
```

### Key Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Lambda Errors | > 5 in 5 min | Investigate immediately |
| API 5XX Errors | > 10 in 5 min | Check Lambda logs |
| API Latency (p99) | > 1000ms | Investigate performance |
| DynamoDB Throttles | > 0 | Increase capacity or optimize queries |

### SNS Alert Topics

| Topic | Purpose | Severity |
|-------|---------|----------|
| `savinggrace-critical-alerts-{env}` | Service outages, errors | Critical |
| `savinggrace-warning-alerts-{env}` | Performance degradation | Warning |
| `savinggrace-expiration-alerts-{env}` | Food expiration warnings | Info |

### Subscribe to Alerts

```bash
# Subscribe to critical alerts
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:921212210452:savinggrace-critical-alerts-dev \
  --protocol email \
  --notification-endpoint admin@savinggrace.org \
  --region us-west-2

# Confirm subscription via email
```

---

## Common Incidents

### 1. Lambda Function Errors

**Symptoms**: Lambda error alarm triggered, API returns 500 errors

**Investigation**:
1. Check CloudWatch Logs:
   ```bash
   aws logs tail /aws/lambda/SavingGrace-{function}-dev --follow --region us-west-2
   ```

2. Identify error pattern:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/SavingGrace-{function}-dev \
     --filter-pattern "ERROR" \
     --start-time $(date -u -d '1 hour ago' +%s)000 \
     --region us-west-2
   ```

3. Check recent deployments:
   ```bash
   aws lambda list-versions-by-function \
     --function-name SavingGrace-{function}-dev \
     --region us-west-2
   ```

**Resolution**:
- **Code error**: Rollback to previous version:
  ```bash
  aws lambda update-function-configuration \
    --function-name SavingGrace-{function}-dev \
    --environment Variables={...previous config...} \
    --region us-west-2
  ```

- **Permission error**: Check IAM role has necessary permissions

- **Resource error**: Check DynamoDB table exists and is accessible

**Prevention**:
- Always run E2E tests before deployment
- Implement gradual rollout (canary deployment)
- Monitor error rates immediately after deployment

---

### 2. API Gateway 5XX Errors

**Symptoms**: API Gateway 5XX alarm triggered, clients receive 502/503/504 errors

**Investigation**:
1. Check API Gateway logs:
   ```bash
   aws logs tail /aws/apigateway/SavingGrace-API-dev --follow --region us-west-2
   ```

2. Check Lambda concurrency limits:
   ```bash
   aws lambda get-function-concurrency \
     --function-name SavingGrace-{function}-dev \
     --region us-west-2
   ```

3. Check for throttling:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Throttles \
     --dimensions Name=FunctionName,Value=SavingGrace-{function}-dev \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Sum \
     --region us-west-2
   ```

**Resolution**:
- **Lambda timeout**: Increase timeout in function configuration
- **Lambda concurrency**: Increase reserved concurrency
- **Cold start**: Implement Lambda warming or use provisioned concurrency
- **API throttling**: Increase throttling limits

**Prevention**:
- Set appropriate Lambda timeouts (5-30s)
- Monitor Lambda duration metrics
- Implement request queuing for high traffic

---

### 3. DynamoDB Throttling

**Symptoms**: DynamoDB throttle alarm, API returns 400 (ProvisionedThroughputExceededException)

**Investigation**:
1. Check table capacity:
   ```bash
   aws dynamodb describe-table \
     --table-name SavingGrace-{Resource}-dev \
     --query 'Table.[ProvisionedThroughput,BillingModeSummary]' \
     --region us-west-2
   ```

2. Check consumed capacity:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name ConsumedReadCapacityUnits \
     --dimensions Name=TableName,Value=SavingGrace-{Resource}-dev \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Average,Maximum \
     --region us-west-2
   ```

**Resolution**:
- **Immediate**: Enable auto-scaling or increase capacity manually
  ```bash
  aws dynamodb update-table \
    --table-name SavingGrace-{Resource}-dev \
    --billing-mode PAY_PER_REQUEST \
    --region us-west-2
  ```

- **Short-term**: Optimize queries (use GSIs, reduce scan operations)

- **Long-term**: Implement caching (ElastiCache, API Gateway caching)

**Prevention**:
- Use on-demand billing for unpredictable workloads
- Enable auto-scaling for provisioned capacity
- Monitor capacity utilization proactively

---

### 4. High API Latency

**Symptoms**: API latency alarm triggered, slow response times

**Investigation**:
1. Check X-Ray traces (if enabled):
   ```bash
   # View traces in X-Ray console
   # https://console.aws.amazon.com/xray/home?region=us-west-2
   ```

2. Check Lambda duration:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=SavingGrace-{function}-dev \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Average,Maximum \
     --region us-west-2
   ```

3. Identify slow queries:
   - Check CloudWatch Logs for slow DynamoDB queries
   - Look for full table scans

**Resolution**:
- **Code optimization**: Optimize slow functions
- **Query optimization**: Use GSIs instead of scans
- **Caching**: Implement API Gateway caching
- **Cold starts**: Use provisioned concurrency

**Prevention**:
- Performance test regularly (Artillery)
- Monitor p95 and p99 latency
- Set performance budgets

---

### 5. Cognito Authentication Issues

**Symptoms**: Users cannot log in, authentication errors

**Investigation**:
1. Check Cognito metrics:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Cognito \
     --metric-name UserAuthentication \
     --dimensions Name=UserPool,Value=us-west-2_DeQrm3GHa \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
     --period 300 \
     --statistics Sum \
     --region us-west-2
   ```

2. Check recent user pool changes:
   ```bash
   aws cognito-idp describe-user-pool \
     --user-pool-id us-west-2_DeQrm3GHa \
     --region us-west-2
   ```

3. Test authentication manually:
   ```bash
   aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id pn75f7u9cqsunkje417vtqvvf \
     --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123! \
     --region us-west-2
   ```

**Resolution**:
- **Incorrect password**: User needs to reset password
- **Unverified email**: Resend verification email
- **Account locked**: Admin unlock via console
- **MFA issues**: Disable/reset MFA for user

**Prevention**:
- Monitor failed login attempts
- Implement account lockout policies
- Provide clear error messages to users

---

### 6. S3 Access Denied

**Symptoms**: Receipt upload fails, 403 errors from S3

**Investigation**:
1. Check bucket policy:
   ```bash
   aws s3api get-bucket-policy \
     --bucket savinggrace-receipts-dev-921212210452 \
     --region us-west-2
   ```

2. Check Lambda IAM role:
   ```bash
   aws lambda get-function-configuration \
     --function-name SavingGrace-donations-dev \
     --query 'Role' \
     --region us-west-2
   ```

3. Test S3 access:
   ```bash
   aws s3 ls s3://savinggrace-receipts-dev-921212210452/ --region us-west-2
   ```

**Resolution**:
- Update IAM role to include S3 permissions
- Check bucket policy allows Lambda access
- Verify bucket exists and is in correct region

**Prevention**:
- Use IAM policy simulator to test permissions
- Implement least-privilege IAM policies
- Monitor S3 access logs

---

## Emergency Procedures

### Complete Service Outage

**Immediate Actions** (< 5 minutes):
1. Verify scope of outage (frontend, backend, or both)
2. Check AWS Health Dashboard for service issues
3. Notify stakeholders via status page
4. Engage on-call engineer

**Investigation** (5-15 minutes):
1. Check recent deployments/changes
2. Review CloudWatch alarms
3. Check Lambda quotas and limits
4. Verify DynamoDB tables are accessible

**Resolution** (15-60 minutes):
- Rollback recent changes if identified as cause
- Scale up resources if capacity issue
- Engage AWS Support if infrastructure issue

### Data Breach Response

**Immediate Actions**:
1. Isolate affected systems
2. Rotate all credentials and API keys
3. Notify security team and stakeholders
4. Preserve logs for forensics

**Investigation**:
1. Review CloudTrail logs
2. Check GuardDuty findings
3. Identify scope and impact
4. Determine entry point

**Resolution**:
1. Patch vulnerabilities
2. Notify affected users (GDPR: within 72 hours)
3. Implement additional security controls
4. Conduct post-mortem

---

## Routine Operations

### Daily Tasks

- [ ] Check CloudWatch dashboard for anomalies
- [ ] Review critical and warning alarms
- [ ] Check for expiring food items
- [ ] Monitor API error rates

### Weekly Tasks

- [ ] Review CloudWatch logs for errors
- [ ] Check Lambda cold start metrics
- [ ] Review DynamoDB capacity utilization
- [ ] Test backup restore procedure (monthly)

### Monthly Tasks

- [ ] Review and update IAM policies
- [ ] Security audit (run `./scripts/security-audit.sh`)
- [ ] Performance review (run `npm run test:performance`)
- [ ] Cost optimization review

### Quarterly Tasks

- [ ] Update dependencies (npm, pip)
- [ ] Review and update documentation
- [ ] Conduct security training
- [ ] Review and update this runbook

---

## Troubleshooting

### Check Health Endpoint

```bash
curl https://a9np4bbum8.execute-api.us-west-2.amazonaws.com/dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:00:00Z",
  "version": "1.0.0"
}
```

### Get Recent Lambda Logs

```bash
aws logs tail /aws/lambda/SavingGrace-{function}-dev \
  --since 1h \
  --format short \
  --region us-west-2
```

### List All Alarms in ALARM State

```bash
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --alarm-name-prefix SavingGrace \
  --region us-west-2
```

### Check API Gateway Metrics (Last Hour)

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiId,Value=a9np4bbum8 \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region us-west-2
```

### Test Database Connectivity

```bash
aws dynamodb describe-table \
  --table-name SavingGrace-Users-dev \
  --region us-west-2
```

### Get CloudFormation Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name SavingGrace-API-dev \
  --query 'Stacks[0].StackStatus' \
  --region us-west-2
```

---

## Appendix

### Useful AWS CLI Commands

#### List all Lambda functions
```bash
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `SavingGrace`)].FunctionName' \
  --output table \
  --region us-west-2
```

#### List all DynamoDB tables
```bash
aws dynamodb list-tables \
  --query 'TableNames[?starts_with(@, `SavingGrace`)]' \
  --output table \
  --region us-west-2
```

#### List all S3 buckets
```bash
aws s3 ls | grep savinggrace
```

#### Get API Gateway REST APIs
```bash
aws apigateway get-rest-apis \
  --query 'items[?starts_with(name, `SavingGrace`)].{Name:name,Id:id}' \
  --output table \
  --region us-west-2
```

### Contact Information

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call Engineer | PagerDuty | Primary |
| DevOps Lead | ops@savinggrace.org | Secondary |
| Security Team | security@savinggrace.org | For security incidents |
| AWS Support | AWS Console | For infrastructure issues |

### External Resources

- [AWS Status Dashboard](https://status.aws.amazon.com/)
- [AWS Support Center](https://console.aws.amazon.com/support/home)
- [CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
- [X-Ray Console](https://console.aws.amazon.com/xray/)

---

**Document Owner**: DevOps Team
**Last Review**: 2025-10-14
**Next Review**: 2026-01-14
