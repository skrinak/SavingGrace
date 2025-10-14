"""
Logging Utilities
Structured logging for Lambda functions with CloudWatch integration
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured JSON logger for CloudWatch"""

    def __init__(self, name: str, level: str = "INFO"):
        """
        Initialize structured logger

        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        self.logger.handlers = []

        # Add JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

        # Store context for all logs
        self.context = {
            "service": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
            "version": os.environ.get("AWS_LAMBDA_FUNCTION_VERSION", "unknown"),
            "environment": os.environ.get("ENVIRONMENT", "dev"),
        }

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Internal log method

        Args:
            level: Log level
            message: Log message
            extra: Additional fields
            error: Exception object
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **self.context,
        }

        if extra:
            log_data.update(extra)

        if error:
            log_data["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }

        getattr(self.logger, level.lower())(json.dumps(log_data))

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log("DEBUG", message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log("INFO", message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log("WARNING", message, extra=kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message"""
        self._log("ERROR", message, extra=kwargs, error=error)

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message"""
        self._log("CRITICAL", message, extra=kwargs, error=error)

    def set_context(self, **kwargs) -> None:
        """
        Set context fields for all subsequent logs

        Args:
            **kwargs: Context fields to set
        """
        self.context.update(kwargs)

    def log_api_request(
        self, method: str, path: str, user_id: Optional[str] = None, **kwargs
    ) -> None:
        """
        Log API request

        Args:
            method: HTTP method
            path: Request path
            user_id: User ID
            **kwargs: Additional fields
        """
        self.info(
            "API request",
            request_method=method,
            request_path=path,
            user_id=user_id,
            **kwargs,
        )

    def log_api_response(self, status_code: int, duration_ms: float, **kwargs) -> None:
        """
        Log API response

        Args:
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional fields
        """
        self.info(
            "API response",
            response_status=status_code,
            response_duration_ms=duration_ms,
            **kwargs,
        )

    def log_database_operation(
        self, operation: str, table: str, duration_ms: float, **kwargs
    ) -> None:
        """
        Log database operation

        Args:
            operation: Operation type (get, put, query, etc.)
            table: Table name
            duration_ms: Operation duration in milliseconds
            **kwargs: Additional fields
        """
        self.info(
            "Database operation",
            db_operation=operation,
            db_table=table,
            db_duration_ms=duration_ms,
            **kwargs,
        )


class JsonFormatter(logging.Formatter):
    """JSON log formatter for CloudWatch"""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record

        Returns:
            JSON string
        """
        return record.getMessage()


# Global logger cache
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str = __name__, level: Optional[str] = None) -> StructuredLogger:
    """
    Get or create structured logger

    Args:
        name: Logger name
        level: Log level (defaults to LOG_LEVEL env var or INFO)

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        log_level: str = level if level is not None else os.environ.get("LOG_LEVEL", "INFO")
        _loggers[name] = StructuredLogger(name, log_level)
    return _loggers[name]


def log_lambda_event(event: Dict[str, Any], context: Any) -> None:
    """
    Log Lambda invocation event

    Args:
        event: Lambda event
        context: Lambda context
    """
    logger = get_logger()
    logger.info(
        "Lambda invocation",
        event_type=event.get("requestContext", {}).get("requestId"),
        request_id=context.request_id,
        function_name=context.function_name,
        memory_limit_mb=context.memory_limit_in_mb,
    )
