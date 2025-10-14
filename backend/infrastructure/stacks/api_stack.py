"""
API Gateway Stack for SavingGrace
Creates REST API with Cognito authorizer and all endpoints
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_cognito as cognito,
    aws_logs as logs,
    CfnOutput,
)
from constructs import Construct


class ApiStack(Stack):
    """Stack for API Gateway"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        user_pool: cognito.UserPool,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================================
        # CLOUDWATCH LOG GROUP for API Gateway
        # =========================================================================
        self.api_logs = logs.LogGroup(
            self,
            "ApiLogs",
            log_group_name=f"/aws/apigateway/savinggrace-{environment}",
            retention=logs.RetentionDays.ONE_MONTH if environment == "dev" else logs.RetentionDays.THREE_MONTHS,
        )

        # =========================================================================
        # REST API
        # =========================================================================
        self.api = apigateway.RestApi(
            self,
            "Api",
            rest_api_name=f"SavingGrace-{environment}",
            description=f"SavingGrace API Gateway for {environment}",
            deploy_options=apigateway.StageOptions(
                stage_name=environment,
                throttling_rate_limit=1000,
                throttling_burst_limit=2000,
                logging_level=apigateway.MethodLoggingLevel.INFO,
                access_log_destination=apigateway.LogGroupLogDestination(self.api_logs),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
                metrics_enabled=True,
                tracing_enabled=True,
                cache_cluster_enabled=True if environment == "production" else False,
                cache_cluster_size="0.5" if environment == "production" else None,
                cache_ttl=Duration.minutes(5),
            ),
            cloud_watch_role=True,
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,  # Will restrict in production
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
                max_age=Duration.hours(1),
            ),
            endpoint_types=[apigateway.EndpointType.REGIONAL],
        )

        # =========================================================================
        # HEALTH CHECK ENDPOINT (no auth)
        # =========================================================================
        health = self.api.root.add_resource("health")
        health.add_method(
            "GET",
            apigateway.MockIntegration(
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "healthy", "service": "SavingGrace"}'
                        },
                    )
                ],
                request_templates={"application/json": '{"statusCode": 200}'},
            ),
            method_responses=[apigateway.MethodResponse(status_code="200")],
        )

        # =========================================================================
        # COGNITO AUTHORIZER
        # =========================================================================
        self.authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[user_pool],
            authorizer_name=f"SavingGrace-{environment}",
            identity_source="method.request.header.Authorization",
            results_cache_ttl=Duration.minutes(5),
        )

        # =========================================================================
        # API RESOURCES (will be integrated with Lambda functions)
        # =========================================================================
        # Donors
        donors = self.api.root.add_resource("donors")
        donor_id = donors.add_resource("{donorId}")
        donor_donations = donor_id.add_resource("donations")

        # Donations
        donations = self.api.root.add_resource("donations")
        donation_id = donations.add_resource("{donationId}")
        donation_receipt = donation_id.add_resource("receipt")
        donations_expiring = donations.add_resource("expiring")

        # Recipients
        recipients = self.api.root.add_resource("recipients")
        recipient_id = recipients.add_resource("{recipientId}")
        recipient_history = recipient_id.add_resource("history")

        # Distributions
        distributions = self.api.root.add_resource("distributions")
        distribution_id = distributions.add_resource("{distributionId}")
        distribution_complete = distribution_id.add_resource("complete")

        # Inventory
        inventory = self.api.root.add_resource("inventory")
        inventory_category = inventory.add_resource("{category}")
        inventory_alerts = inventory.add_resource("alerts")
        inventory_adjust = inventory.add_resource("adjust")

        # Reports
        reports = self.api.root.add_resource("reports")
        reports_dashboard = reports.add_resource("dashboard")
        reports_donations = reports.add_resource("donations")
        reports_distributions = reports.add_resource("distributions")
        reports_impact = reports.add_resource("impact")
        reports_export = reports.add_resource("export")

        # Users
        users = self.api.root.add_resource("users")
        user_id = users.add_resource("{userId}")
        user_role = user_id.add_resource("role")

        # Store resources for Lambda integration
        self.resources = {
            "donors": donors,
            "donor_id": donor_id,
            "donor_donations": donor_donations,
            "donations": donations,
            "donation_id": donation_id,
            "donation_receipt": donation_receipt,
            "donations_expiring": donations_expiring,
            "recipients": recipients,
            "recipient_id": recipient_id,
            "recipient_history": recipient_history,
            "distributions": distributions,
            "distribution_id": distribution_id,
            "distribution_complete": distribution_complete,
            "inventory": inventory,
            "inventory_category": inventory_category,
            "inventory_alerts": inventory_alerts,
            "inventory_adjust": inventory_adjust,
            "reports": reports,
            "reports_dashboard": reports_dashboard,
            "reports_donations": reports_donations,
            "reports_distributions": reports_distributions,
            "reports_impact": reports_impact,
            "reports_export": reports_export,
            "users": users,
            "user_id": user_id,
            "user_role": user_role,
        }

        # =========================================================================
        # REQUEST VALIDATORS
        # =========================================================================
        self.request_validator = apigateway.RequestValidator(
            self,
            "RequestValidator",
            rest_api=self.api,
            request_validator_name=f"SavingGrace-{environment}-validator",
            validate_request_body=True,
            validate_request_parameters=True,
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "ApiId", value=self.api.rest_api_id)
        CfnOutput(self, "ApiUrl", value=self.api.url)
        CfnOutput(self, "ApiArn", value=self.api.arn_for_execute_api())
