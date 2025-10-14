#!/usr/bin/env python3
"""
SavingGrace CDK Application
AWS Account: 921212210452
Region: us-west-2 ONLY
"""
import aws_cdk as cdk

from stacks.database_stack import DatabaseStack
from stacks.storage_stack import StorageStack
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

# Monitoring Stack (CloudWatch dashboards, alarms)
monitoring_stack = MonitoringStack(
    app,
    f"SavingGrace-Monitoring-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace monitoring for {environment}",
)

# Add stack dependencies
monitoring_stack.add_dependency(database_stack)
monitoring_stack.add_dependency(storage_stack)

# Tag all resources
cdk.Tags.of(app).add("Project", "SavingGrace")
cdk.Tags.of(app).add("Environment", environment)
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
