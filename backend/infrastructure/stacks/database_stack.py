"""
DynamoDB Tables Stack for SavingGrace
Creates all DynamoDB tables with GSIs as defined in PRD.md
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    CfnOutput,
)
from constructs import Construct


class DatabaseStack(Stack):
    """Stack for DynamoDB tables"""

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine removal policy based on environment
        removal_policy = RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN

        # =========================================================================
        # USERS TABLE
        # =========================================================================
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name=f"SavingGrace-Users-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
        )

        # =========================================================================
        # DONORS TABLE
        # =========================================================================
        self.donors_table = dynamodb.Table(
            self,
            "DonorsTable",
            table_name=f"SavingGrace-Donors-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
        )

        # GSI: DonorsByName
        self.donors_table.add_global_secondary_index(
            index_name="DonorsByName",
            partition_key=dynamodb.Attribute(name="name", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # =========================================================================
        # DONATIONS TABLE
        # =========================================================================
        self.donations_table = dynamodb.Table(
            self,
            "DonationsTable",
            table_name=f"SavingGrace-Donations-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # For inventory updates
        )

        # GSI: DonationsByDonor
        self.donations_table.add_global_secondary_index(
            index_name="DonationsByDonor",
            partition_key=dynamodb.Attribute(name="donorId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="receivedDate", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # GSI: DonationsByDate
        self.donations_table.add_global_secondary_index(
            index_name="DonationsByDate",
            partition_key=dynamodb.Attribute(
                name="entityType", type=dynamodb.AttributeType.STRING
            ),  # DONATION
            sort_key=dynamodb.Attribute(name="receivedDate", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # GSI: ItemsByExpiration
        self.donations_table.add_global_secondary_index(
            index_name="ItemsByExpiration",
            partition_key=dynamodb.Attribute(
                name="itemType", type=dynamodb.AttributeType.STRING
            ),  # ITEM
            sort_key=dynamodb.Attribute(name="expirationDate", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # =========================================================================
        # RECIPIENTS TABLE
        # =========================================================================
        self.recipients_table = dynamodb.Table(
            self,
            "RecipientsTable",
            table_name=f"SavingGrace-Recipients-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
        )

        # GSI: RecipientsByName
        self.recipients_table.add_global_secondary_index(
            index_name="RecipientsByName",
            partition_key=dynamodb.Attribute(name="lastName", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="firstName", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # =========================================================================
        # DISTRIBUTIONS TABLE
        # =========================================================================
        self.distributions_table = dynamodb.Table(
            self,
            "DistributionsTable",
            table_name=f"SavingGrace-Distributions-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,  # For inventory updates
        )

        # GSI: DistributionsByDate
        self.distributions_table.add_global_secondary_index(
            index_name="DistributionsByDate",
            partition_key=dynamodb.Attribute(
                name="entityType", type=dynamodb.AttributeType.STRING
            ),  # DISTRIBUTION
            sort_key=dynamodb.Attribute(
                name="distributionDate", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # GSI: DistributionsByRecipient
        self.distributions_table.add_global_secondary_index(
            index_name="DistributionsByRecipient",
            partition_key=dynamodb.Attribute(
                name="recipientId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="distributionDate", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # =========================================================================
        # INVENTORY TABLE (Materialized View)
        # =========================================================================
        self.inventory_table = dynamodb.Table(
            self,
            "InventoryTable",
            table_name=f"SavingGrace-Inventory-{environment}",
            partition_key=dynamodb.Attribute(name="PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True if environment == "production" else False,
            removal_policy=removal_policy,
        )

        # GSI: InventoryByExpiration
        self.inventory_table.add_global_secondary_index(
            index_name="InventoryByExpiration",
            partition_key=dynamodb.Attribute(name="status", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="expirationDate", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # GSI: InventoryByCategory
        self.inventory_table.add_global_secondary_index(
            index_name="InventoryByCategory",
            partition_key=dynamodb.Attribute(name="category", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="expirationDate", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "UsersTableName", value=self.users_table.table_name)
        CfnOutput(self, "UsersTableArn", value=self.users_table.table_arn)

        CfnOutput(self, "DonorsTableName", value=self.donors_table.table_name)
        CfnOutput(self, "DonorsTableArn", value=self.donors_table.table_arn)

        CfnOutput(self, "DonationsTableName", value=self.donations_table.table_name)
        CfnOutput(self, "DonationsTableArn", value=self.donations_table.table_arn)

        CfnOutput(self, "RecipientsTableName", value=self.recipients_table.table_name)
        CfnOutput(self, "RecipientsTableArn", value=self.recipients_table.table_arn)

        CfnOutput(self, "DistributionsTableName", value=self.distributions_table.table_name)
        CfnOutput(self, "DistributionsTableArn", value=self.distributions_table.table_arn)

        CfnOutput(self, "InventoryTableName", value=self.inventory_table.table_name)
        CfnOutput(self, "InventoryTableArn", value=self.inventory_table.table_arn)
