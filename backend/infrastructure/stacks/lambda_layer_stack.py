"""
Lambda Layer Stack for SavingGrace
Creates shared Lambda layer with common utilities
"""
from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    CfnOutput,
)
from constructs import Construct
import os


class LambdaLayerStack(Stack):
    """Stack for Lambda shared layer"""

    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =========================================================================
        # SHARED LAMBDA LAYER
        # =========================================================================
        # Get path to lambda_layer directory (backend/lambda_layer)
        infrastructure_dir = os.path.dirname(os.path.dirname(__file__))
        backend_dir = os.path.dirname(infrastructure_dir)
        layer_path = os.path.join(backend_dir, "lambda_layer")

        self.shared_layer = lambda_.LayerVersion(
            self,
            "SharedLayer",
            layer_version_name=f"SavingGrace-Shared-{environment}",
            code=lambda_.Code.from_asset(layer_path),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Shared utilities for SavingGrace Lambda functions",
        )

        # =========================================================================
        # OUTPUTS
        # =========================================================================
        CfnOutput(self, "SharedLayerArn", value=self.shared_layer.layer_version_arn)
