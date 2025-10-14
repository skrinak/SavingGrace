"""
Monitoring Stack for SavingGrace
Creates CloudWatch dashboards and alarms
"""
from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    CfnOutput,
)
from constructs import Construct


class MonitoringStack(Stack):
    """Stack for CloudWatch monitoring and alerting"""

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================================
        # SNS TOPICS FOR ALERTS
        # =========================================================================
        self.admin_alerts_topic = sns.Topic(
            self,
            "AdminAlertsTopic",
            topic_name=f"savinggrace-admin-alerts-{environment}",
            display_name=f"SavingGrace Admin Alerts ({environment})",
        )

        self.expiration_alerts_topic = sns.Topic(
            self,
            "ExpirationAlertsTopic",
            topic_name=f"savinggrace-expiration-alerts-{environment}",
            display_name=f"SavingGrace Expiration Alerts ({environment})",
        )

        # Add email subscription (will be configured via console or CLI)
        # self.admin_alerts_topic.add_subscription(
        #     sns_subscriptions.EmailSubscription("admin@savinggrace.org")
        # )

        # =========================================================================
        # CLOUDWATCH DASHBOARD
        # =========================================================================
        self.dashboard = cloudwatch.Dashboard(
            self,
            "MainDashboard",
            dashboard_name=f"SavingGrace-{environment}",
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "AdminAlertsTopicArn", value=self.admin_alerts_topic.topic_arn)
        CfnOutput(
            self, "ExpirationAlertsTopicArn", value=self.expiration_alerts_topic.topic_arn
        )
        CfnOutput(self, "DashboardURL", value=self.dashboard.dashboard_name)
