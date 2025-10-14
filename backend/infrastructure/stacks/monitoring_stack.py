"""
Monitoring Stack for SavingGrace
Creates CloudWatch dashboards, alarms, and SNS topics for alerting
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    CfnOutput,
)
from constructs import Construct


class MonitoringStack(Stack):
    """Stack for CloudWatch monitoring and alerting"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        environment: str,
        api_id: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================================
        # SNS TOPICS FOR ALERTS
        # =========================================================================
        self.critical_alerts_topic = sns.Topic(
            self,
            "CriticalAlertsTopic",
            topic_name=f"savinggrace-critical-alerts-{environment}",
            display_name=f"SavingGrace Critical Alerts ({environment})",
        )

        self.warning_alerts_topic = sns.Topic(
            self,
            "WarningAlertsTopic",
            topic_name=f"savinggrace-warning-alerts-{environment}",
            display_name=f"SavingGrace Warning Alerts ({environment})",
        )

        self.expiration_alerts_topic = sns.Topic(
            self,
            "ExpirationAlertsTopic",
            topic_name=f"savinggrace-expiration-alerts-{environment}",
            display_name=f"SavingGrace Expiration Alerts ({environment})",
        )

        # Add email subscription placeholders (configure via console or CLI)
        # self.critical_alerts_topic.add_subscription(
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

        # Lambda Metrics Section
        lambda_metrics = []
        lambda_functions = [
            "donors", "donations", "recipients", "distributions",
            "inventory", "reports", "users"
        ]

        for func in lambda_functions:
            lambda_metrics.append(
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Errors",
                    dimensions_map={
                        "FunctionName": f"SavingGrace-{func}-*"
                    },
                    statistic="Sum",
                    period=Duration.minutes(5),
                )
            )

        # API Gateway Metrics
        if api_id:
            api_4xx_metric = cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="4XXError",
                dimensions_map={"ApiId": api_id},
                statistic="Sum",
                period=Duration.minutes(5),
            )

            api_5xx_metric = cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={"ApiId": api_id},
                statistic="Sum",
                period=Duration.minutes(5),
            )

            api_latency_metric = cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Latency",
                dimensions_map={"ApiId": api_id},
                statistic="Average",
                period=Duration.minutes(5),
            )

            api_count_metric = cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="Count",
                dimensions_map={"ApiId": api_id},
                statistic="Sum",
                period=Duration.minutes(5),
            )

        # DynamoDB Metrics
        tables = ["Users", "Donors", "Donations", "Recipients", "Distributions", "Inventory"]
        dynamodb_metrics = []

        for table in tables:
            dynamodb_metrics.append(
                cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="UserErrors",
                    dimensions_map={"TableName": f"SavingGrace-{table}-{environment}"},
                    statistic="Sum",
                    period=Duration.minutes(5),
                )
            )

        # Add widgets to dashboard
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Gateway - Request Count",
                left=[api_count_metric] if api_id else [],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="API Gateway - Latency",
                left=[api_latency_metric] if api_id else [],
                width=12,
                height=6,
            ),
        )

        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="API Gateway - 4XX Errors",
                left=[api_4xx_metric] if api_id else [],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="API Gateway - 5XX Errors",
                left=[api_5xx_metric] if api_id else [],
                width=12,
                height=6,
            ),
        )

        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda - Total Errors",
                left=lambda_metrics[:4],
                width=24,
                height=6,
            ),
        )

        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="DynamoDB - User Errors",
                left=dynamodb_metrics[:3],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="DynamoDB - Throttles",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/DynamoDB",
                        metric_name="UserErrors",
                        dimensions_map={"TableName": f"SavingGrace-{tables[0]}-{environment}"},
                        statistic="Sum",
                        period=Duration.minutes(5),
                    )
                ],
                width=12,
                height=6,
            ),
        )

        # =========================================================================
        # CLOUDWATCH ALARMS
        # =========================================================================

        # Lambda Error Rate Alarm (> 1%)
        for func in lambda_functions:
            error_alarm = cloudwatch.Alarm(
                self,
                f"Lambda{func.capitalize()}ErrorAlarm",
                alarm_name=f"SavingGrace-Lambda-{func}-Errors-{environment}",
                metric=cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Errors",
                    dimensions_map={"FunctionName": f"SavingGrace-{func}-{environment}"},
                    statistic="Sum",
                    period=Duration.minutes(5),
                ),
                threshold=5,  # 5 errors in 5 minutes
                evaluation_periods=1,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"Lambda {func} function has high error rate",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            error_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(self.critical_alerts_topic)
            )

        # API Gateway 5XX Error Alarm
        if api_id:
            api_5xx_alarm = cloudwatch.Alarm(
                self,
                "APIGateway5XXAlarm",
                alarm_name=f"SavingGrace-API-5XX-Errors-{environment}",
                metric=api_5xx_metric,
                threshold=10,  # 10 5xx errors in 5 minutes
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="API Gateway has high 5XX error rate",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            api_5xx_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(self.critical_alerts_topic)
            )

            # API Gateway Latency Alarm (p99 > 1000ms)
            api_latency_alarm = cloudwatch.Alarm(
                self,
                "APIGatewayLatencyAlarm",
                alarm_name=f"SavingGrace-API-High-Latency-{environment}",
                metric=cloudwatch.Metric(
                    namespace="AWS/ApiGateway",
                    metric_name="Latency",
                    dimensions_map={"ApiId": api_id},
                    statistic="p99",
                    period=Duration.minutes(5),
                ),
                threshold=1000,  # 1 second
                evaluation_periods=3,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description="API Gateway latency is high (p99 > 1s)",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            api_latency_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(self.warning_alerts_topic)
            )

        # DynamoDB Throttle Alarm
        for table in tables:
            throttle_alarm = cloudwatch.Alarm(
                self,
                f"DynamoDB{table}ThrottleAlarm",
                alarm_name=f"SavingGrace-DynamoDB-{table}-Throttles-{environment}",
                metric=cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="UserErrors",
                    dimensions_map={"TableName": f"SavingGrace-{table}-{environment}"},
                    statistic="Sum",
                    period=Duration.minutes(5),
                ),
                threshold=1,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                alarm_description=f"DynamoDB {table} table is experiencing throttling",
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            throttle_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(self.critical_alerts_topic)
            )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "CriticalAlertsTopicArn", value=self.critical_alerts_topic.topic_arn)
        CfnOutput(self, "WarningAlertsTopicArn", value=self.warning_alerts_topic.topic_arn)
        CfnOutput(self, "ExpirationAlertsTopicArn", value=self.expiration_alerts_topic.topic_arn)
        CfnOutput(
            self,
            "DashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={self.dashboard.dashboard_name}"
        )
