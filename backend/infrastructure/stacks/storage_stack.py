"""
S3 Storage Stack for SavingGrace
Creates S3 buckets for receipts and documents
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct


class StorageStack(Stack):
    """Stack for S3 storage buckets"""

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine removal policy based on environment
        auto_delete = environment == "dev"
        removal_policy = RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN

        # =========================================================================
        # RECEIPTS BUCKET
        # =========================================================================
        self.receipts_bucket = s3.Bucket(
            self,
            "ReceiptsBucket",
            bucket_name=f"savinggrace-receipts-{environment}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=removal_policy,
            auto_delete_objects=auto_delete,
            lifecycle_rules=[
                # Move to Glacier after 90 days
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        )
                    ],
                    enabled=True,
                ),
                # Delete from Glacier after 1 year
                s3.LifecycleRule(
                    expiration=Duration.days(365),
                    enabled=True,
                ),
            ],
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                    allowed_origins=["*"],  # Will be restricted to CloudFront domain in production
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
        )

        # =========================================================================
        # CLOUDTRAIL BUCKET (for audit logging)
        # =========================================================================
        self.cloudtrail_bucket = s3.Bucket(
            self,
            "CloudTrailBucket",
            bucket_name=f"savinggrace-cloudtrail-{environment}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,  # Always retain audit logs
            auto_delete_objects=False,
            lifecycle_rules=[
                # Move to Glacier after 30 days
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30),
                        )
                    ],
                    enabled=True,
                ),
            ],
        )

        # Allow CloudTrail to write to bucket
        self.cloudtrail_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AWSCloudTrailAclCheck",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudtrail.amazonaws.com")],
                actions=["s3:GetBucketAcl"],
                resources=[self.cloudtrail_bucket.bucket_arn],
            )
        )

        self.cloudtrail_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AWSCloudTrailWrite",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudtrail.amazonaws.com")],
                actions=["s3:PutObject"],
                resources=[f"{self.cloudtrail_bucket.bucket_arn}/*"],
                conditions={"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}},
            )
        )

        # =========================================================================
        # FRONTEND BUCKET (S3 + CloudFront hosting - separate account)
        # Note: This will be created in frontend account (563334150189)
        # =========================================================================

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "ReceiptsBucketName", value=self.receipts_bucket.bucket_name)
        CfnOutput(self, "ReceiptsBucketArn", value=self.receipts_bucket.bucket_arn)

        CfnOutput(self, "CloudTrailBucketName", value=self.cloudtrail_bucket.bucket_name)
        CfnOutput(self, "CloudTrailBucketArn", value=self.cloudtrail_bucket.bucket_arn)
