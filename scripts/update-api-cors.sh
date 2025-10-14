#!/bin/bash

###############################################################################
# Update API Gateway CORS Configuration
# Adds CloudFront distribution URL to CORS allowed origins
# Backend account: 921212210452, Region: us-west-2
###############################################################################

set -e

# Configuration
BACKEND_ACCOUNT="921212210452"
REGION="us-west-2"
ENVIRONMENT="${1:-dev}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is configured for backend account
log_info "Checking AWS CLI configuration..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ "$CURRENT_ACCOUNT" != "$BACKEND_ACCOUNT" ]; then
    log_error "AWS CLI not configured for backend account $BACKEND_ACCOUNT"
    log_error "Current account: $CURRENT_ACCOUNT"
    log_error "Please configure AWS CLI with: aws configure --profile backend"
    exit 1
fi

log_info "Verified AWS account: $CURRENT_ACCOUNT"

# Get CloudFront URL from frontend stack
log_info "Getting CloudFront URL from frontend stack..."
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name "SavingGrace-Frontend-${ENVIRONMENT}" \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendURL`].OutputValue' \
    --output text \
    --region $REGION \
    --profile frontend 2>/dev/null || echo "")

if [ -z "$CLOUDFRONT_URL" ] || [ "$CLOUDFRONT_URL" == "None" ]; then
    log_error "Could not retrieve CloudFront URL from frontend stack"
    log_error "Make sure frontend stack is deployed: cd frontend/infrastructure && cdk deploy"
    exit 1
fi

log_info "CloudFront URL: $CLOUDFRONT_URL"

# Get API Gateway REST API ID
log_info "Finding API Gateway REST API..."
API_ID=$(aws apigateway get-rest-apis \
    --query "items[?name=='SavingGrace-API-${ENVIRONMENT}'].id | [0]" \
    --output text \
    --region $REGION)

if [ -z "$API_ID" ] || [ "$API_ID" == "None" ]; then
    log_error "Could not find API Gateway REST API"
    exit 1
fi

log_info "Found API Gateway: $API_ID"

# Note: CORS configuration in API Gateway is complex and varies by resource
# The best approach is to update the CDK stack to include the CloudFront URL

log_warn "CORS configuration should be updated in the CDK stack"
log_warn "Add the following to your API Gateway CORS configuration:"
log_warn ""
log_warn "Allowed Origins:"
log_warn "  - http://localhost:5173 (dev)"
log_warn "  - $CLOUDFRONT_URL"
log_warn ""
log_warn "Update infrastructure/stacks/api_stack.py with:"
log_warn ""
log_warn "default_cors_preflight_options=apigateway.CorsOptions("
log_warn "    allow_origins=[\"$CLOUDFRONT_URL\", \"http://localhost:5173\"],"
log_warn "    allow_methods=[\"GET\", \"POST\", \"PUT\", \"DELETE\", \"OPTIONS\"],"
log_warn "    allow_headers=[\"Content-Type\", \"Authorization\"],"
log_warn "    allow_credentials=True,"
log_warn "    max_age=Duration.hours(1),"
log_warn ")"
log_warn ""
log_warn "Then redeploy the backend stack: cd backend/infrastructure && cdk deploy SavingGrace-API-dev"

log_info "CloudFront URL ready to add to CORS: $CLOUDFRONT_URL"
