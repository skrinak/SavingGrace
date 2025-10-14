#!/usr/bin/env python3
"""
SavingGrace CDK Application
AWS Account: 921212210452
Region: us-west-2 ONLY
"""
import aws_cdk as cdk

from stacks.database_stack import DatabaseStack
from stacks.storage_stack import StorageStack
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack
from stacks.lambda_layer_stack import LambdaLayerStack
from stacks.lambda_stack import LambdaStack
from stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# Environment configuration
env_us_west_2 = cdk.Environment(
    account="921212210452",
    region="us-west-2"
)

# Get environment from context (default to dev)
environment = app.node.try_get_context("env") or "dev"

# Database Stack (DynamoDB tables)
database_stack = DatabaseStack(
    app,
    f"SavingGrace-Database-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace DynamoDB tables for {environment}",
)

# Storage Stack (S3 buckets)
storage_stack = StorageStack(
    app,
    f"SavingGrace-Storage-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace S3 storage for {environment}",
)

# Auth Stack (Cognito User Pool)
auth_stack = AuthStack(
    app,
    f"SavingGrace-Auth-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace Cognito authentication for {environment}",
)

# API Stack (API Gateway with Cognito authorizer)
api_stack = ApiStack(
    app,
    f"SavingGrace-API-{environment}",
    env=env_us_west_2,
    environment=environment,
    user_pool=auth_stack.user_pool,
    description=f"SavingGrace API Gateway for {environment}",
)

# Lambda Layer Stack (shared utilities)
lambda_layer_stack = LambdaLayerStack(
    app,
    f"SavingGrace-LambdaLayer-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace Lambda shared layer for {environment}",
)

# Lambda Stack (all 35 Lambda functions)
lambda_stack = LambdaStack(
    app,
    f"SavingGrace-Lambda-{environment}",
    env=env_us_west_2,
    environment=environment,
    shared_layer=lambda_layer_stack.shared_layer,
    user_pool=auth_stack.user_pool,
    api=api_stack.api,
    api_resources=api_stack.resources,
    authorizer=api_stack.authorizer,
    tables={
        "users": database_stack.users_table,
        "donors": database_stack.donors_table,
        "donations": database_stack.donations_table,
        "recipients": database_stack.recipients_table,
        "distributions": database_stack.distributions_table,
        "inventory": database_stack.inventory_table,
    },
    receipts_bucket=storage_stack.receipts_bucket,
    description=f"SavingGrace Lambda functions for {environment}",
)

# Monitoring Stack (CloudWatch dashboards, alarms)
monitoring_stack = MonitoringStack(
    app,
    f"SavingGrace-Monitoring-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace monitoring for {environment}",
)

# Add stack dependencies
api_stack.add_dependency(auth_stack)
# Lambda stack dependencies are implicit through resource references
# (CDK detects dependencies automatically when we reference resources)
lambda_stack.add_dependency(database_stack)
lambda_stack.add_dependency(storage_stack)
lambda_stack.add_dependency(lambda_layer_stack)
monitoring_stack.add_dependency(database_stack)
monitoring_stack.add_dependency(storage_stack)
monitoring_stack.add_dependency(auth_stack)
monitoring_stack.add_dependency(api_stack)
monitoring_stack.add_dependency(lambda_stack)

# Tag all resources
cdk.Tags.of(app).add("Project", "SavingGrace")
cdk.Tags.of(app).add("Environment", environment)
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
