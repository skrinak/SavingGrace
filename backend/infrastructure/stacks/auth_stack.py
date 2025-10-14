"""
Authentication Stack for SavingGrace
Creates Cognito User Pool with custom attributes and MFA
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_cognito as cognito,
    CfnOutput,
)
from constructs import Construct


class AuthStack(Stack):
    """Stack for Cognito authentication"""

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine removal policy based on environment
        removal_policy = RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN

        # =========================================================================
        # COGNITO USER POOL
        # =========================================================================
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"SavingGrace-{environment}",
            self_sign_up_enabled=False,  # Admin creates users
            sign_in_aliases=cognito.SignInAliases(email=True, username=False),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True),
                phone_number=cognito.StandardAttribute(required=False, mutable=True),
            ),
            custom_attributes={
                "role": cognito.StringAttribute(
                    mutable=True,
                    min_len=1,
                    max_len=50,
                ),
            },
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(7),
            ),
            mfa=cognito.Mfa.OPTIONAL,  # Required for admins (enforced in app)
            mfa_second_factor=cognito.MfaSecondFactor(sms=True, otp=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=removal_policy,
            advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED
            if environment == "production"
            else cognito.AdvancedSecurityMode.AUDIT,
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your SavingGrace account",
                email_body="Thank you for signing up to SavingGrace! Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True,
            ),
        )

        # =========================================================================
        # USER POOL CLIENT (for frontend)
        # =========================================================================
        self.user_pool_client = self.user_pool.add_client(
            "WebClient",
            user_pool_client_name=f"SavingGrace-Web-{environment}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                custom=False,
                admin_user_password=True,
            ),
            generate_secret=False,  # Public client (web/mobile)
            prevent_user_existence_errors=True,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            enable_token_revocation=True,
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO,
            ],
        )

        # =========================================================================
        # USER POOL GROUPS (RBAC roles)
        # =========================================================================
        self.admin_group = cognito.CfnUserPoolGroup(
            self,
            "AdminGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="Admin",
            description="Full system access, user management, configuration",
            precedence=1,
        )

        self.donor_coordinator_group = cognito.CfnUserPoolGroup(
            self,
            "DonorCoordinatorGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="DonorCoordinator",
            description="Manage donors, record donations",
            precedence=2,
        )

        self.distribution_manager_group = cognito.CfnUserPoolGroup(
            self,
            "DistributionManagerGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="DistributionManager",
            description="Manage distributions, recipients",
            precedence=3,
        )

        self.volunteer_group = cognito.CfnUserPoolGroup(
            self,
            "VolunteerGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="Volunteer",
            description="View-only access, mark distributions complete",
            precedence=4,
        )

        self.read_only_group = cognito.CfnUserPoolGroup(
            self,
            "ReadOnlyGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="ReadOnly",
            description="Dashboard and reporting access",
            precedence=5,
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolArn", value=self.user_pool.user_pool_arn)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
        CfnOutput(
            self,
            "UserPoolProviderURL",
            value=self.user_pool.user_pool_provider_url,
        )
