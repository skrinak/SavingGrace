"""
DynamoDB Helper Utilities
Common operations for DynamoDB table access
"""
import os
from typing import Any, Dict, List, Optional, cast
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from .errors import DatabaseError, NotFoundError


class DynamoDBHelper:
    """Helper class for DynamoDB operations"""

    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize DynamoDB helper

        Args:
            table_name: DynamoDB table name (defaults to TABLE_NAME env var)
        """
        self.table_name = table_name or os.environ.get("TABLE_NAME")
        if not self.table_name:
            raise ValueError("table_name or TABLE_NAME environment variable required")

        self.dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        self.table = self.dynamodb.Table(self.table_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Put item into DynamoDB table

        Args:
            item: Item to insert

        Returns:
            Inserted item

        Raises:
            DatabaseError: If put operation fails
        """
        try:
            # Add timestamps
            now = datetime.utcnow().isoformat()
            item["created_at"] = item.get("created_at", now)
            item["updated_at"] = now

            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to put item: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def get_item(self, pk: str, sk: str) -> Dict[str, Any]:
        """
        Get item from DynamoDB table

        Args:
            pk: Partition key value
            sk: Sort key value

        Returns:
            Retrieved item

        Raises:
            NotFoundError: If item not found
            DatabaseError: If get operation fails
        """
        try:
            response = self.table.get_item(Key={"PK": pk, "SK": sk})

            if "Item" not in response:
                raise NotFoundError(resource="Item", resource_id=f"{pk}#{sk}")

            return cast(Dict[str, Any], response["Item"])
        except NotFoundError:
            raise
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to get item: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def update_item(
        self,
        pk: str,
        sk: str,
        updates: Dict[str, Any],
        condition_expression: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update item in DynamoDB table

        Args:
            pk: Partition key value
            sk: Sort key value
            updates: Dictionary of attributes to update
            condition_expression: Optional condition expression

        Returns:
            Updated item

        Raises:
            NotFoundError: If item not found
            DatabaseError: If update operation fails
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()

            # Build update expression
            update_expr = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
            expr_attr_names = {f"#{k}": k for k in updates.keys()}
            expr_attr_values = {f":{k}": v for k, v in updates.items()}

            params = {
                "Key": {"PK": pk, "SK": sk},
                "UpdateExpression": update_expr,
                "ExpressionAttributeNames": expr_attr_names,
                "ExpressionAttributeValues": expr_attr_values,
                "ReturnValues": "ALL_NEW",
            }

            if condition_expression:
                params["ConditionExpression"] = condition_expression

            response = self.table.update_item(**params)
            return cast(Dict[str, Any], response["Attributes"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise NotFoundError(resource="Item", resource_id=f"{pk}#{sk}")
            raise DatabaseError(
                message=f"Failed to update item: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def delete_item(self, pk: str, sk: str) -> None:
        """
        Delete item from DynamoDB table

        Args:
            pk: Partition key value
            sk: Sort key value

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            self.table.delete_item(Key={"PK": pk, "SK": sk})
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to delete item: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def query(
        self,
        key_condition: Any,
        filter_expression: Optional[Any] = None,
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
        scan_forward: bool = True,
    ) -> Dict[str, Any]:
        """
        Query DynamoDB table

        Args:
            key_condition: Key condition expression
            filter_expression: Optional filter expression
            index_name: Optional GSI name
            limit: Maximum items to return
            exclusive_start_key: Pagination token
            scan_forward: Query direction (True=ascending, False=descending)

        Returns:
            Query response with items and pagination token

        Raises:
            DatabaseError: If query operation fails
        """
        try:
            params = {
                "KeyConditionExpression": key_condition,
                "ScanIndexForward": scan_forward,
            }

            if filter_expression is not None:
                params["FilterExpression"] = filter_expression
            if index_name:
                params["IndexName"] = index_name
            if limit:
                params["Limit"] = limit
            if exclusive_start_key:
                params["ExclusiveStartKey"] = exclusive_start_key

            response = self.table.query(**params)

            return {
                "items": response.get("Items", []),
                "count": response.get("Count", 0),
                "last_evaluated_key": response.get("LastEvaluatedKey"),
            }
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to query table: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def scan(
        self,
        filter_expression: Optional[Any] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Scan DynamoDB table (use sparingly, prefer query)

        Args:
            filter_expression: Optional filter expression
            limit: Maximum items to return
            exclusive_start_key: Pagination token

        Returns:
            Scan response with items and pagination token

        Raises:
            DatabaseError: If scan operation fails
        """
        try:
            params = {}

            if filter_expression is not None:
                params["FilterExpression"] = filter_expression
            if limit:
                params["Limit"] = limit
            if exclusive_start_key:
                params["ExclusiveStartKey"] = exclusive_start_key

            response = self.table.scan(**params)

            return {
                "items": response.get("Items", []),
                "count": response.get("Count", 0),
                "last_evaluated_key": response.get("LastEvaluatedKey"),
            }
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to scan table: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def batch_get_items(self, keys: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Batch get items from DynamoDB table

        Args:
            keys: List of keys (PK, SK) to retrieve

        Returns:
            List of retrieved items

        Raises:
            DatabaseError: If batch get operation fails
        """
        try:
            response = self.dynamodb.batch_get_item(RequestItems={self.table_name: {"Keys": keys}})
            return cast(List[Dict[str, Any]], response.get("Responses", {}).get(self.table_name, []))
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to batch get items: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )

    def batch_write_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Batch write items to DynamoDB table

        Args:
            items: List of items to write

        Raises:
            DatabaseError: If batch write operation fails
        """
        try:
            with self.table.batch_writer() as batch:
                for item in items:
                    # Add timestamps
                    now = datetime.utcnow().isoformat()
                    item["created_at"] = item.get("created_at", now)
                    item["updated_at"] = now
                    batch.put_item(Item=item)
        except ClientError as e:
            raise DatabaseError(
                message=f"Failed to batch write items: {str(e)}",
                details={"error_code": e.response["Error"]["Code"]},
            )
