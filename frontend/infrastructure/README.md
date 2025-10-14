# Frontend Infrastructure Deployment

This directory contains CDK infrastructure for deploying the SavingGrace React frontend to AWS.

## Architecture

- **S3 Bucket**: Hosts the static React build files
- **CloudFront**: CDN distribution with OAI for S3 access
- **WAF**: Web Application Firewall with AWS Managed Rules
- **Account**: 563334150189 (Frontend Account)
- **Region**: us-west-2

## Prerequisites

1. AWS CLI configured for frontend account (563334150189)
2. Python 3.11+ with `uv` installed
3. AWS CDK CLI installed (`npm install -g aws-cdk`)

## Setup

```bash
# Navigate to frontend infrastructure
cd frontend/infrastructure

# Install Python dependencies
uv pip install -r requirements.txt

# Bootstrap CDK (one-time setup per account/region)
cdk bootstrap --profile frontend
```

## Deployment

### Deploy Infrastructure (CloudFront + WAF)

```bash
# Navigate to frontend infrastructure
cd frontend/infrastructure

# Deploy to dev environment
cdk deploy --profile frontend

# Deploy to staging
cdk deploy --context env=staging --profile frontend

# Deploy to production
cdk deploy --context env=prod --profile frontend
```

### Deploy Frontend Code

After infrastructure is deployed, use the deployment script:

```bash
# From project root
./scripts/deploy-frontend.sh dev
```

The script will:
1. Build the React app
2. Upload to S3
3. Invalidate CloudFront cache

## Stack Outputs

After deployment, CDK will output:

- **FrontendBucketName**: S3 bucket name
- **DistributionId**: CloudFront distribution ID
- **DistributionDomainName**: CloudFront domain (e.g., d123456.cloudfront.net)
- **FrontendURL**: Full HTTPS URL to access the frontend
- **WAFArn**: WAF Web ACL ARN

## Security Features

### WAF Rules

1. **AWS Managed Core Rule Set**: Protects against common web attacks
2. **AWS Known Bad Inputs**: Blocks malicious patterns
3. **Rate Limiting**: Max 1000 requests per 5 minutes per IP

### S3 Security

- Versioning enabled
- Encryption at rest (AES-256)
- Block all public access
- Access only via CloudFront OAI

### CloudFront Security

- HTTPS required (redirects HTTP)
- HTTP/2 and HTTP/3 enabled
- Compression enabled
- SPA routing support (404 → index.html)

## CORS Configuration

After deployment, update the backend API Gateway CORS settings to allow the CloudFront domain:

```bash
# Get the CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name SavingGrace-Frontend-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' \
  --output text \
  --region us-west-2)

echo "Add this URL to API Gateway CORS allowed origins: $CLOUDFRONT_URL"
```

## Troubleshooting

### CloudFront not serving latest files

```bash
# Invalidate CloudFront cache manually
aws cloudfront create-invalidation \
  --distribution-id D123456 \
  --paths "/*" \
  --profile frontend
```

### 403 errors on SPA routes

The stack automatically configures error responses to redirect 403/404 to index.html for SPA routing. If issues persist, check CloudFront error responses configuration.

### WAF blocking legitimate traffic

Check WAF metrics in CloudWatch and adjust rules if needed:

```bash
aws wafv2 get-web-acl \
  --name SavingGrace-Frontend-dev \
  --scope CLOUDFRONT \
  --id <web-acl-id> \
  --region us-east-1
```

## Cost Optimization

- CloudFront uses PriceClass 100 (US, Canada, Europe) for lower costs
- S3 uses standard storage class
- Consider enabling CloudFront caching for static assets (already configured)

## Clean Up

```bash
# Destroy dev environment
cdk destroy --profile frontend

# Note: Production stack has RETAIN policy on S3 bucket
```
