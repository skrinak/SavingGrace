#!/usr/bin/env python3
"""
SavingGrace Frontend CDK Application
AWS Account: 563334150189 (Frontend Account)
Region: us-west-2
Note: WAF for CloudFront must be created in us-east-1
"""
import aws_cdk as cdk

from stacks.frontend_stack import FrontendStack

app = cdk.App()

# Environment configuration for frontend account
env_us_west_2 = cdk.Environment(account="563334150189", region="us-west-2")

# Get environment from context (default to dev)
environment = app.node.try_get_context("env") or "dev"

# Frontend Stack (S3 + CloudFront + WAF)
frontend_stack = FrontendStack(
    app,
    f"SavingGrace-Frontend-{environment}",
    env=env_us_west_2,
    environment=environment,
    description=f"SavingGrace frontend hosting for {environment}",
)

# Tag all resources
cdk.Tags.of(app).add("Project", "SavingGrace")
cdk.Tags.of(app).add("Environment", environment)
cdk.Tags.of(app).add("Component", "Frontend")
cdk.Tags.of(app).add("ManagedBy", "CDK")

app.synth()
