#!/bin/bash

###############################################################################
# Frontend Deployment Script
# Deploys React app to S3 + CloudFront in frontend account (563334150189)
# Region: us-west-2
###############################################################################

set -e  # Exit on error

# Configuration
FRONTEND_ACCOUNT="563334150189"
REGION="us-west-2"
ENVIRONMENT="${1:-dev}"  # Default to dev if not specified
BUCKET_NAME="savinggrace-frontend-${ENVIRONMENT}-${FRONTEND_ACCOUNT}"
CLOUDFRONT_COMMENT="SavingGrace Frontend ${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is configured for frontend account
log_info "Checking AWS CLI configuration..."
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
if [ "$CURRENT_ACCOUNT" != "$FRONTEND_ACCOUNT" ]; then
    log_error "AWS CLI not configured for frontend account $FRONTEND_ACCOUNT"
    log_error "Current account: $CURRENT_ACCOUNT"
    log_error "Please configure AWS CLI with: aws configure --profile frontend"
    log_error "Or set AWS_PROFILE=frontend environment variable"
    exit 1
fi

log_info "Verified AWS account: $CURRENT_ACCOUNT"

# Navigate to frontend directory
log_info "Navigating to frontend directory..."
cd "$(dirname "$0")/../frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    npm install
fi

# Run TypeScript check
log_info "Running TypeScript type checking..."
npm run typecheck

# Build the frontend
log_info "Building frontend for $ENVIRONMENT environment..."
npm run build

if [ ! -d "dist" ]; then
    log_error "Build failed - dist directory not found"
    exit 1
fi

log_info "Build completed successfully"

# Create S3 bucket if it doesn't exist
log_info "Checking if S3 bucket exists: $BUCKET_NAME..."
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    log_info "Creating S3 bucket: $BUCKET_NAME..."
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION

    # Enable versioning
    log_info "Enabling versioning on S3 bucket..."
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled \
        --region $REGION

    # Block public access
    log_info "Blocking public access to S3 bucket..."
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
        --region $REGION

    # Enable encryption
    log_info "Enabling server-side encryption..."
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration \
            '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
        --region $REGION

    log_info "S3 bucket created and configured"
else
    log_info "S3 bucket already exists"
fi

# Sync built files to S3
log_info "Uploading files to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --delete \
    --cache-control "public, max-age=31536000" \
    --exclude "index.html" \
    --region $REGION

# Upload index.html with no-cache to ensure SPA routing works
log_info "Uploading index.html with no-cache..."
aws s3 cp dist/index.html "s3://$BUCKET_NAME/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --region $REGION

log_info "Files uploaded successfully"

# Check if CloudFront distribution exists
log_info "Checking for existing CloudFront distribution..."
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='$CLOUDFRONT_COMMENT'].Id | [0]" \
    --output text \
    --region $REGION 2>/dev/null || echo "")

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" == "None" ]; then
    log_warn "CloudFront distribution not found"
    log_warn "Please create CloudFront distribution manually or run setup script"
    log_warn "S3 bucket: $BUCKET_NAME"
else
    log_info "Found CloudFront distribution: $DISTRIBUTION_ID"
    log_info "Creating cache invalidation..."
    aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*" \
        --region $REGION
    log_info "Cache invalidation created"
fi

log_info "Deployment completed successfully!"
log_info "S3 Bucket: $BUCKET_NAME"
if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
    CLOUDFRONT_URL=$(aws cloudfront get-distribution \
        --id "$DISTRIBUTION_ID" \
        --query "Distribution.DomainName" \
        --output text \
        --region $REGION)
    log_info "CloudFront URL: https://$CLOUDFRONT_URL"
fi
