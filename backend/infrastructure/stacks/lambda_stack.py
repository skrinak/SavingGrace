"""
Lambda Functions Stack for SavingGrace
Creates all 35 Lambda functions with API Gateway integration
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_cognito as cognito,
    aws_apigateway as apigateway,
    CfnOutput,
)
from constructs import Construct
import os


class LambdaStack(Stack):
    """Stack for all Lambda functions"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        shared_layer: lambda_.LayerVersion,
        user_pool: cognito.UserPool,
        api: apigateway.RestApi,
        api_resources: dict,
        authorizer: apigateway.CognitoUserPoolsAuthorizer,
        tables: dict,
        receipts_bucket: s3.Bucket,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================================
        # LAMBDA EXECUTION ROLE
        # =========================================================================
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=f"Execution role for SavingGrace Lambda functions ({environment})",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSXRayDaemonWriteAccess"
                ),
            ],
        )

        # Grant DynamoDB permissions
        for table in tables.values():
            table.grant_read_write_data(lambda_role)

        # Grant S3 permissions for receipts bucket
        receipts_bucket.grant_read_write(lambda_role)

        # Create exports bucket for reports
        exports_bucket = s3.Bucket(
            self,
            "ExportsBucket",
            bucket_name=f"savinggrace-exports-{environment}-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        exports_bucket.grant_read_write(lambda_role)

        # Grant Cognito permissions for user management
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminUpdateUserAttributes",
                    "cognito-idp:AdminDeleteUser",
                    "cognito-idp:AdminAddUserToGroup",
                    "cognito-idp:AdminRemoveUserFromGroup",
                    "cognito-idp:AdminEnableUser",
                    "cognito-idp:AdminDisableUser",
                    "cognito-idp:ListUsers",
                ],
                resources=[user_pool.user_pool_arn],
            )
        )

        # =========================================================================
        # COMMON LAMBDA CONFIGURATION
        # =========================================================================
        common_env = {
            "ENVIRONMENT": environment,
            "USER_POOL_ID": user_pool.user_pool_id,
            "RECEIPTS_BUCKET_NAME": receipts_bucket.bucket_name,
            "EXPORTS_BUCKET_NAME": exports_bucket.bucket_name,
            "LOG_LEVEL": "INFO" if environment == "production" else "DEBUG",
        }

        lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "layers": [shared_layer],
            "role": lambda_role,
            "timeout": Duration.seconds(30),
            "memory_size": 256,
            "tracing": lambda_.Tracing.ACTIVE,
            "environment": common_env,
        }

        # =========================================================================
        # HELPER FUNCTION TO CREATE LAMBDA AND INTEGRATE WITH API GATEWAY
        # =========================================================================
        def create_lambda_function(
            function_id: str,
            handler_path: str,
            description: str,
            table_name: str,
            timeout_seconds: int = 30,
        ) -> lambda_.Function:
            """Create Lambda function with common configuration"""
            # Get path to functions directory (backend/functions)
            infrastructure_dir = os.path.dirname(os.path.dirname(__file__))
            backend_dir = os.path.dirname(infrastructure_dir)
            functions_dir = os.path.join(backend_dir, "functions")

            # Extract module name (donors, donations, etc.) and handler file name
            module_name = handler_path.split("/")[0]
            handler_file = handler_path.split("/")[-1].replace(".py", "")

            func = lambda_.Function(
                self,
                function_id,
                function_name=f"SavingGrace-{function_id}-{environment}",
                description=description,
                code=lambda_.Code.from_asset(os.path.join(functions_dir, module_name)),
                handler=f"{handler_file}.lambda_handler",
                timeout=Duration.seconds(timeout_seconds),
                environment={
                    **common_env,
                    "TABLE_NAME": table_name,
                },
                **{k: v for k, v in lambda_config.items() if k not in ["environment", "timeout"]},
            )
            return func

        def integrate_lambda_with_api(
            resource: apigateway.Resource,
            method: str,
            function: lambda_.Function,
            require_auth: bool = True,
        ) -> None:
            """Integrate Lambda function with API Gateway resource"""
            integration = apigateway.LambdaIntegration(
                function,
                proxy=True,
                integration_responses=[
                    apigateway.IntegrationResponse(status_code="200")
                ],
            )

            method_options = {
                "method_responses": [apigateway.MethodResponse(status_code="200")],
            }

            if require_auth:
                method_options["authorizer"] = authorizer
                method_options["authorization_type"] = apigateway.AuthorizationType.COGNITO

            resource.add_method(method, integration, **method_options)

        # =========================================================================
        # DONORS LAMBDA FUNCTIONS (5)
        # =========================================================================
        donors_table_name = tables["donors"].table_name

        self.create_donor_fn = create_lambda_function(
            "CreateDonor",
            "donors/create_donor.py",
            "Create new donor",
            donors_table_name,
        )
        integrate_lambda_with_api(api_resources["donors"], "POST", self.create_donor_fn)

        self.get_donor_fn = create_lambda_function(
            "GetDonor",
            "donors/get_donor.py",
            "Get donor by ID",
            donors_table_name,
        )
        integrate_lambda_with_api(api_resources["donor_id"], "GET", self.get_donor_fn)

        self.update_donor_fn = create_lambda_function(
            "UpdateDonor",
            "donors/update_donor.py",
            "Update donor",
            donors_table_name,
        )
        integrate_lambda_with_api(api_resources["donor_id"], "PUT", self.update_donor_fn)

        self.list_donors_fn = create_lambda_function(
            "ListDonors",
            "donors/list_donors.py",
            "List all donors",
            donors_table_name,
        )
        # Remove placeholder method and add real one
        integrate_lambda_with_api(api_resources["donors"], "GET", self.list_donors_fn)

        self.get_donor_donations_fn = create_lambda_function(
            "GetDonorDonations",
            "donors/get_donor_donations.py",
            "Get donations for donor",
            tables["donations"].table_name,
        )
        integrate_lambda_with_api(
            api_resources["donor_donations"], "GET", self.get_donor_donations_fn
        )

        # =========================================================================
        # DONATIONS LAMBDA FUNCTIONS (6)
        # =========================================================================
        donations_table_name = tables["donations"].table_name

        self.create_donation_fn = create_lambda_function(
            "CreateDonation",
            "donations/create_donation.py",
            "Create new donation",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donations"], "POST", self.create_donation_fn
        )

        self.get_donation_fn = create_lambda_function(
            "GetDonation",
            "donations/get_donation.py",
            "Get donation by ID",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donation_id"], "GET", self.get_donation_fn
        )

        self.update_donation_fn = create_lambda_function(
            "UpdateDonation",
            "donations/update_donation.py",
            "Update donation",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donation_id"], "PUT", self.update_donation_fn
        )

        self.list_donations_fn = create_lambda_function(
            "ListDonations",
            "donations/list_donations.py",
            "List all donations",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donations"], "GET", self.list_donations_fn
        )

        self.get_receipt_fn = create_lambda_function(
            "GetReceipt",
            "donations/get_receipt.py",
            "Get donation receipt",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donation_receipt"], "GET", self.get_receipt_fn
        )

        self.get_expiring_donations_fn = create_lambda_function(
            "GetExpiringDonations",
            "donations/get_expiring_donations.py",
            "Get expiring donations",
            donations_table_name,
        )
        integrate_lambda_with_api(
            api_resources["donations_expiring"], "GET", self.get_expiring_donations_fn
        )

        # =========================================================================
        # RECIPIENTS LAMBDA FUNCTIONS (5)
        # =========================================================================
        recipients_table_name = tables["recipients"].table_name

        self.create_recipient_fn = create_lambda_function(
            "CreateRecipient",
            "recipients/create_recipient.py",
            "Create new recipient",
            recipients_table_name,
        )
        integrate_lambda_with_api(
            api_resources["recipients"], "POST", self.create_recipient_fn
        )

        self.get_recipient_fn = create_lambda_function(
            "GetRecipient",
            "recipients/get_recipient.py",
            "Get recipient by ID",
            recipients_table_name,
        )
        integrate_lambda_with_api(
            api_resources["recipient_id"], "GET", self.get_recipient_fn
        )

        self.update_recipient_fn = create_lambda_function(
            "UpdateRecipient",
            "recipients/update_recipient.py",
            "Update recipient",
            recipients_table_name,
        )
        integrate_lambda_with_api(
            api_resources["recipient_id"], "PUT", self.update_recipient_fn
        )

        self.list_recipients_fn = create_lambda_function(
            "ListRecipients",
            "recipients/list_recipients.py",
            "List all recipients",
            recipients_table_name,
        )
        integrate_lambda_with_api(
            api_resources["recipients"], "GET", self.list_recipients_fn
        )

        self.get_recipient_history_fn = create_lambda_function(
            "GetRecipientHistory",
            "recipients/get_recipient_history.py",
            "Get recipient distribution history",
            tables["distributions"].table_name,
        )
        integrate_lambda_with_api(
            api_resources["recipient_history"], "GET", self.get_recipient_history_fn
        )

        # =========================================================================
        # DISTRIBUTIONS LAMBDA FUNCTIONS (5)
        # =========================================================================
        distributions_table_name = tables["distributions"].table_name

        self.create_distribution_fn = create_lambda_function(
            "CreateDistribution",
            "distributions/create_distribution.py",
            "Create new distribution",
            distributions_table_name,
        )
        integrate_lambda_with_api(
            api_resources["distributions"], "POST", self.create_distribution_fn
        )

        self.get_distribution_fn = create_lambda_function(
            "GetDistribution",
            "distributions/get_distribution.py",
            "Get distribution by ID",
            distributions_table_name,
        )
        integrate_lambda_with_api(
            api_resources["distribution_id"], "GET", self.get_distribution_fn
        )

        self.update_distribution_fn = create_lambda_function(
            "UpdateDistribution",
            "distributions/update_distribution.py",
            "Update distribution",
            distributions_table_name,
        )
        integrate_lambda_with_api(
            api_resources["distribution_id"], "PUT", self.update_distribution_fn
        )

        self.list_distributions_fn = create_lambda_function(
            "ListDistributions",
            "distributions/list_distributions.py",
            "List all distributions",
            distributions_table_name,
        )
        integrate_lambda_with_api(
            api_resources["distributions"], "GET", self.list_distributions_fn
        )

        self.complete_distribution_fn = create_lambda_function(
            "CompleteDistribution",
            "distributions/complete_distribution.py",
            "Mark distribution as complete",
            distributions_table_name,
            timeout_seconds=60,
        )
        integrate_lambda_with_api(
            api_resources["distribution_complete"],
            "POST",
            self.complete_distribution_fn,
        )

        # =========================================================================
        # INVENTORY LAMBDA FUNCTIONS (4)
        # =========================================================================
        inventory_table_name = tables["inventory"].table_name

        self.get_inventory_by_category_fn = create_lambda_function(
            "GetInventoryByCategory",
            "inventory/get_inventory_by_category.py",
            "Get inventory by category",
            inventory_table_name,
        )
        integrate_lambda_with_api(
            api_resources["inventory_category"],
            "GET",
            self.get_inventory_by_category_fn,
        )

        self.list_inventory_fn = create_lambda_function(
            "ListInventory",
            "inventory/list_inventory.py",
            "List all inventory",
            inventory_table_name,
        )
        integrate_lambda_with_api(
            api_resources["inventory"], "GET", self.list_inventory_fn
        )

        self.adjust_inventory_fn = create_lambda_function(
            "AdjustInventory",
            "inventory/adjust_inventory.py",
            "Adjust inventory quantities",
            inventory_table_name,
        )
        integrate_lambda_with_api(
            api_resources["inventory_adjust"], "POST", self.adjust_inventory_fn
        )

        self.get_inventory_alerts_fn = create_lambda_function(
            "GetInventoryAlerts",
            "inventory/get_inventory_alerts.py",
            "Get inventory alerts",
            inventory_table_name,
        )
        integrate_lambda_with_api(
            api_resources["inventory_alerts"], "GET", self.get_inventory_alerts_fn
        )

        # =========================================================================
        # REPORTS LAMBDA FUNCTIONS (5)
        # =========================================================================
        # Reports need access to multiple tables
        self.get_dashboard_fn = create_lambda_function(
            "GetDashboard",
            "reports/get_dashboard.py",
            "Get dashboard metrics",
            donors_table_name,  # Primary table, will access others via env
            timeout_seconds=60,
        )
        # Add environment variables for other tables
        self.get_dashboard_fn.add_environment("DONATIONS_TABLE_NAME", donations_table_name)
        self.get_dashboard_fn.add_environment("RECIPIENTS_TABLE_NAME", recipients_table_name)
        self.get_dashboard_fn.add_environment("DISTRIBUTIONS_TABLE_NAME", distributions_table_name)
        self.get_dashboard_fn.add_environment("INVENTORY_TABLE_NAME", inventory_table_name)
        integrate_lambda_with_api(
            api_resources["reports_dashboard"], "GET", self.get_dashboard_fn
        )

        self.get_donations_report_fn = create_lambda_function(
            "GetDonationsReport",
            "reports/get_donations_report.py",
            "Get donations report",
            donations_table_name,
            timeout_seconds=60,
        )
        integrate_lambda_with_api(
            api_resources["reports_donations"], "GET", self.get_donations_report_fn
        )

        self.get_distributions_report_fn = create_lambda_function(
            "GetDistributionsReport",
            "reports/get_distributions_report.py",
            "Get distributions report",
            distributions_table_name,
            timeout_seconds=60,
        )
        integrate_lambda_with_api(
            api_resources["reports_distributions"],
            "GET",
            self.get_distributions_report_fn,
        )

        self.get_impact_report_fn = create_lambda_function(
            "GetImpactReport",
            "reports/get_impact_report.py",
            "Get impact report",
            donations_table_name,
            timeout_seconds=60,
        )
        self.get_impact_report_fn.add_environment("DISTRIBUTIONS_TABLE_NAME", distributions_table_name)
        integrate_lambda_with_api(
            api_resources["reports_impact"], "GET", self.get_impact_report_fn
        )

        self.export_report_fn = create_lambda_function(
            "ExportReport",
            "reports/export_report.py",
            "Export report to S3",
            donors_table_name,
            timeout_seconds=120,
        )
        self.export_report_fn.add_environment("DONATIONS_TABLE_NAME", donations_table_name)
        self.export_report_fn.add_environment("DISTRIBUTIONS_TABLE_NAME", distributions_table_name)
        self.export_report_fn.add_environment("INVENTORY_TABLE_NAME", inventory_table_name)
        integrate_lambda_with_api(
            api_resources["reports_export"], "POST", self.export_report_fn
        )

        # =========================================================================
        # USERS LAMBDA FUNCTIONS (5)
        # =========================================================================
        users_table_name = tables["users"].table_name

        self.create_user_fn = create_lambda_function(
            "CreateUser",
            "users/create_user.py",
            "Create new user",
            users_table_name,
        )
        integrate_lambda_with_api(api_resources["users"], "POST", self.create_user_fn)

        self.get_user_fn = create_lambda_function(
            "GetUser",
            "users/get_user.py",
            "Get user by ID",
            users_table_name,
        )
        integrate_lambda_with_api(api_resources["user_id"], "GET", self.get_user_fn)

        self.update_user_fn = create_lambda_function(
            "UpdateUser",
            "users/update_user.py",
            "Update user",
            users_table_name,
        )
        integrate_lambda_with_api(api_resources["user_id"], "PUT", self.update_user_fn)

        self.delete_user_fn = create_lambda_function(
            "DeleteUser",
            "users/delete_user.py",
            "Delete user",
            users_table_name,
        )
        integrate_lambda_with_api(
            api_resources["user_id"], "DELETE", self.delete_user_fn
        )

        self.update_user_role_fn = create_lambda_function(
            "UpdateUserRole",
            "users/update_user_role.py",
            "Update user role",
            users_table_name,
        )
        integrate_lambda_with_api(
            api_resources["user_role"], "PUT", self.update_user_role_fn
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(
            self, "LambdaFunctionCount", value=str(35), description="Total Lambda functions deployed"
        )
        CfnOutput(self, "ExportsBucketName", value=exports_bucket.bucket_name)
