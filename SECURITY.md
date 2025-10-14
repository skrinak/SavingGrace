# Security Documentation - SavingGrace

**Last Updated**: 2025-10-13
**Review Cycle**: Quarterly
**Next Review**: 2026-01-13

## Table of Contents

1. [Security Overview](#security-overview)
2. [Compliance & Standards](#compliance--standards)
3. [Data Security](#data-security)
4. [Authentication & Authorization](#authentication--authorization)
5. [Infrastructure Security](#infrastructure-security)
6. [Security Monitoring](#security-monitoring)
7. [Incident Response](#incident-response)
8. [Security Auditing](#security-auditing)
9. [GDPR Compliance](#gdpr-compliance)
10. [Security Best Practices](#security-best-practices)

---

## Security Overview

SavingGrace is a food donation tracking platform built with security-first principles. The application handles Personally Identifiable Information (PII) of recipients and must comply with SOC2, GDPR, and CCPA requirements.

### Security Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      CloudFront (HTTPS)                       │
│              WAF + DDoS Protection + TLS 1.2+                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   API Gateway REST API                        │
│              Cognito Authorizer + Throttling                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    Lambda Functions                           │
│              IAM Roles + VPC (optional)                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│         DynamoDB (Encrypted) + S3 (Encrypted)                 │
│                   CloudWatch Logs                             │
└──────────────────────────────────────────────────────────────┘
```

### AWS Accounts

- **Frontend Account**: 563334150189 (CloudFront, S3, WAF)
- **Backend Account**: 921212210452 (API Gateway, Lambda, DynamoDB, Cognito)
- **Region**: us-west-2 (US West Oregon)

---

## Compliance & Standards

### SOC2 Type II Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Access Controls** | Cognito + IAM + RBAC | ✅ Implemented |
| **Encryption at Rest** | AES-256 (DynamoDB + S3) | ✅ Implemented |
| **Encryption in Transit** | TLS 1.2+ | ✅ Implemented |
| **Audit Logging** | CloudWatch + CloudTrail | ✅ Implemented |
| **MFA for Admins** | Cognito MFA | ⚠️ Configurable |
| **Data Backup** | DynamoDB PITR + S3 Versioning | ✅ Implemented |
| **Incident Response** | Documented plan | ⚠️ In Progress |

### GDPR Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Right to Access (Art. 15)** | Data export API | ⚠️ Pending |
| **Right to Erasure (Art. 17)** | Soft delete + PII removal | ✅ Implemented |
| **Data Portability (Art. 20)** | JSON export format | ⚠️ Pending |
| **Privacy by Design (Art. 25)** | Encryption + RBAC | ✅ Implemented |
| **Security of Processing (Art. 32)** | Encryption + monitoring | ✅ Implemented |
| **Breach Notification (Art. 33)** | GuardDuty + alerts | ⚠️ Recommended |

### CCPA Compliance

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Right to Know** | Data export API | ⚠️ Pending |
| **Right to Delete** | Account deletion | ✅ Implemented |
| **Right to Opt-Out** | N/A (no data selling) | ✅ N/A |
| **Data Minimization** | Only collect necessary data | ✅ Implemented |

---

## Data Security

### Data Classification

| Classification | Examples | Protection Level |
|----------------|----------|------------------|
| **Critical PII** | Recipient SSN, medical info | Encrypted + Access Restricted |
| **Standard PII** | Names, emails, phone numbers | Encrypted + Access Logged |
| **Business Data** | Donation quantities, inventory | Encrypted + Access Controlled |
| **Public Data** | Dashboard statistics (aggregated) | Read-Only Access |

### Encryption

#### At Rest
- **DynamoDB**: AES-256 encryption (AWS managed keys)
- **S3**: AES-256 encryption (AWS managed keys)
- **Cognito**: Encrypted by default

#### In Transit
- **API Gateway**: TLS 1.2+ enforced
- **CloudFront**: HTTPS required (HTTP redirects to HTTPS)
- **Lambda**: AWS internal network (encrypted)

### PII Handling

#### PII Fields
```typescript
// Recipient PII
{
  firstName: string;      // PII
  lastName: string;       // PII
  contactPhone: string;   // PII
  email: string;          // PII
  address: string;        // PII
  householdSize: number;  // Sensitive
  dietaryRestrictions: string[];  // Sensitive
}
```

#### PII Protection Measures

1. **Masking in List Views**
   ```typescript
   // List view (masked)
   firstName: "John"
   lastName: "D."
   phone: "***-***-1234"
   email: "j***@example.com"
   ```

2. **Full Display in Detail Views** (with authorization)
   ```typescript
   // Detail view (authorized users only)
   firstName: "John"
   lastName: "Doe"
   phone: "555-123-1234"
   email: "john.doe@example.com"
   ```

3. **No PII in Logs**
   ```python
   # ❌ NEVER log PII
   logger.error(f"Error for user {email}")

   # ✅ Use user ID instead
   logger.error(f"Error for user {user_id}")
   ```

4. **PII Retention**
   - Active users: Retained
   - Deleted users: PII removed within 30 days
   - Audit logs: User ID retained, PII removed

---

## Authentication & Authorization

### Cognito User Pool

**User Pool ID**: `us-west-2_DeQrm3GHa`
**Client ID**: `pn75f7u9cqsunkje417vtqvvf`

#### Password Policy
- Minimum length: 8 characters
- Requires: uppercase, lowercase, number, special character
- Password expiration: Not enforced (user choice)
- MFA: Optional for users, recommended for admins

#### Custom Attributes
```json
{
  "custom:role": "Admin | Donor Coordinator | Distribution Manager | Volunteer | Read-Only"
}
```

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all features, user management |
| **Donor Coordinator** | Manage donors, donations, inventory (read-only on recipients) |
| **Distribution Manager** | Manage recipients, distributions, inventory |
| **Volunteer** | Read access to donations, distributions, inventory |
| **Read-Only** | View-only access to reports and dashboards |

### Token Management

- **Access Token Lifetime**: 1 hour
- **Refresh Token Lifetime**: 30 days
- **Token Storage**: LocalStorage (frontend)
- **Token Transmission**: Authorization Bearer header

---

## Infrastructure Security

### IAM Policies

#### Lambda Execution Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-west-2:921212210452:table/SavingGrace-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::savinggrace-receipts-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-west-2:921212210452:log-group:/aws/lambda/SavingGrace-*"
    }
  ]
}
```

### Network Security

#### API Gateway
- **Throttling**: 1000 requests/sec steady, 2000 burst
- **CORS**: CloudFront domain + localhost (dev only)
- **Authentication**: Cognito authorizer on all endpoints (except /health)
- **Logging**: Full request/response logging in dev, summary in prod

#### WAF Rules
1. **AWS Managed Core Rule Set**: Protects against OWASP Top 10
2. **AWS Known Bad Inputs**: Blocks malicious patterns
3. **Rate Limiting**: Max 1000 requests per 5 minutes per IP

#### S3 Security
- **Block Public Access**: Enabled on all buckets
- **Bucket Policies**: CloudFront OAI only (frontend), Lambda only (receipts)
- **Versioning**: Enabled
- **Encryption**: AES-256

### Secrets Management

- **AWS Secrets Manager**: Database credentials (if using RDS)
- **Systems Manager Parameter Store**: Non-sensitive configuration
- **Environment Variables**: Lambda configuration (non-sensitive)

❌ **Never store secrets in**:
- Source code
- Git repository
- CloudWatch logs
- DynamoDB

---

## Security Monitoring

### CloudWatch Logs

**Log Groups**:
- `/aws/lambda/SavingGrace-*` - Lambda function logs
- `/aws/apigateway/SavingGrace-*` - API Gateway logs
- `/aws/cognito/userpool/*` - Cognito logs

**Log Retention**: 30 days (dev), 90 days (prod)

**PII Filtering**: Application-level filtering (no PII logged)

### CloudWatch Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| Lambda Error Rate | > 1% | SNS notification |
| API Gateway 5xx | > 0.5% | SNS notification |
| DynamoDB Throttling | > 0 | SNS notification |
| Cognito Failed Logins | > 10/min | SNS notification |

### AWS GuardDuty (Recommended)

Enable GuardDuty for threat detection:

```bash
aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --region us-west-2
```

### AWS CloudTrail

Enable CloudTrail for API audit logging:

```bash
aws cloudtrail create-trail \
  --name SavingGrace-Audit-Trail \
  --s3-bucket-name savinggrace-cloudtrail-dev-921212210452 \
  --region us-west-2
```

---

## Incident Response

### Incident Response Plan

#### 1. Detection
- CloudWatch alarms trigger
- GuardDuty findings
- User reports
- Security audit findings

#### 2. Assessment
1. Determine severity (Low, Medium, High, Critical)
2. Identify affected systems and data
3. Estimate impact (users affected, data exposed)

#### 3. Containment
1. Isolate affected resources
2. Rotate compromised credentials
3. Block malicious IPs (WAF rules)
4. Disable compromised user accounts

#### 4. Eradication
1. Patch vulnerabilities
2. Remove malware/backdoors
3. Update IAM policies
4. Deploy security fixes

#### 5. Recovery
1. Restore from backups if needed
2. Re-enable services
3. Monitor for recurrence

#### 6. Post-Incident
1. Document incident timeline
2. Conduct root cause analysis
3. Update security policies
4. Notify affected users (GDPR: within 72 hours)

### Incident Severity Levels

| Severity | Examples | Response Time |
|----------|----------|---------------|
| **Critical** | Data breach, unauthorized access to PII | Immediate (< 1 hour) |
| **High** | Service outage, DDoS attack | < 4 hours |
| **Medium** | Failed login attempts, minor vulnerabilities | < 24 hours |
| **Low** | Configuration drift, non-critical alerts | < 72 hours |

### Contact Information

- **Security Team**: security@savinggrace.example.com
- **Data Protection Officer**: dpo@savinggrace.example.com
- **On-Call**: PagerDuty integration (to be configured)

---

## Security Auditing

### Automated Security Audit

Run security audit script:

```bash
./scripts/security-audit.sh dev
```

**Checks**:
- IAM policy analysis
- DynamoDB encryption status
- S3 bucket security configuration
- CloudWatch log PII exposure
- Cognito security settings
- API Gateway configuration

**Output**: Detailed audit report in `security-audit-<timestamp>/`

### GDPR Compliance Testing

Run GDPR compliance script:

```bash
./scripts/test-gdpr-compliance.sh
```

**Tests**:
- Data portability (export)
- Right to deletion
- PII encryption
- Compliance checklist

### Manual Security Review

#### Quarterly Review Checklist

- [ ] Review IAM policies for least privilege
- [ ] Check for unused IAM roles/users
- [ ] Verify MFA enabled for admin users
- [ ] Review CloudWatch logs for anomalies
- [ ] Check GuardDuty findings
- [ ] Review CloudTrail logs
- [ ] Test backup and restore procedures
- [ ] Update security documentation
- [ ] Review and update incident response plan
- [ ] Conduct security awareness training

#### Penetration Testing

- **Frequency**: Annually
- **Scope**: API endpoints, authentication, authorization
- **Tools**: OWASP ZAP, Burp Suite
- **Exclusions**: DDoS testing (violates AWS ToS)

---

## GDPR Compliance

### Data Subject Rights

#### Right to Access (Article 15)

**Implementation**:
```bash
# User requests data export
GET /users/me/export
Authorization: Bearer <access_token>

# Response includes:
{
  "user": { ... },
  "donations": [ ... ],
  "distributions": [ ... ],
  "activityLog": [ ... ]
}
```

#### Right to Erasure (Article 17)

**Implementation**:
```bash
# User requests account deletion
DELETE /users/me
Authorization: Bearer <access_token>

# Actions:
# 1. Remove user from Cognito
# 2. Soft delete user record
# 3. Remove all PII
# 4. Anonymize audit logs
# 5. Retain financial records (legal requirement)
```

#### Right to Data Portability (Article 20)

Export format: JSON
Delivery: Email with secure download link
Timeline: Within 30 days

### GDPR Technical Measures

- [x] Encryption at rest (Article 32)
- [x] Encryption in transit (Article 32)
- [x] Access controls (Article 32)
- [x] Pseudonymization in logs (Article 32)
- [ ] Data breach notification process (Article 33)
- [ ] DPO designated (Article 37)

---

## Security Best Practices

### For Developers

1. **Never log PII**
   ```python
   # ❌ Bad
   logger.info(f"User {email} logged in")

   # ✅ Good
   logger.info(f"User {user_id} logged in")
   ```

2. **Use parameterized queries** (DynamoDB prevents injection by default)

3. **Validate all input**
   ```python
   def validate_email(email: str) -> bool:
       return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None
   ```

4. **Apply least privilege**
   - Lambda functions should only have necessary permissions
   - Frontend users should only see data for their role

5. **Rotate secrets regularly**
   - Access keys: Every 90 days
   - Passwords: On demand (no forced expiration)

### For Operations

1. **Enable MFA** for all AWS console access
2. **Use CloudWatch alarms** for security events
3. **Enable GuardDuty** for threat detection
4. **Regular security audits** (quarterly minimum)
5. **Keep dependencies updated** (npm audit, pip-audit)

### For Users

1. **Use strong passwords** (enforced by Cognito)
2. **Enable MFA** (recommended for admin users)
3. **Don't share credentials**
4. **Report suspicious activity**
5. **Log out when done**

---

## Security Testing

### E2E Security Tests

Located in `e2e/auth/`:
- Authentication tests
- Authorization tests (RBAC)
- Session management
- PII masking verification

Run tests:
```bash
npm run test:e2e
```

### Performance Testing

Located in `artillery.yml`:
- Load testing (100 concurrent users)
- Performance targets: p95 < 500ms

Run tests:
```bash
npm run test:performance
```

### Security Scanning

```bash
# Frontend dependencies
cd frontend && npm audit

# Backend dependencies
cd backend && pip-audit

# Infrastructure security
./scripts/security-audit.sh dev
```

---

## Appendix

### Security Tools

| Tool | Purpose | Status |
|------|---------|--------|
| **AWS WAF** | Web application firewall | ✅ Deployed |
| **AWS GuardDuty** | Threat detection | ⚠️ Recommended |
| **AWS CloudTrail** | API audit logging | ⚠️ Recommended |
| **AWS Secrets Manager** | Secrets management | ✅ Available |
| **Cognito** | Authentication | ✅ Deployed |
| **CloudWatch** | Monitoring | ✅ Deployed |
| **Playwright** | E2E testing | ✅ Configured |
| **Artillery** | Performance testing | ✅ Configured |

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [GDPR Full Text](https://gdpr-info.eu/)
- [SOC2 Framework](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report)
- [CCPA Overview](https://oag.ca.gov/privacy/ccpa)

---

**Document Owner**: Security Team
**Last Review**: 2025-10-13
**Next Review**: 2026-01-13
**Classification**: Internal Use Only
