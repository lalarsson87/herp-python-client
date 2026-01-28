"""
Error Context for Structured Error Logging

Provides structured context for debugging errors in production.
Enables better error tracking and faster issue resolution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ErrorContext:
    """
    Structured error context for debugging

    Captures contextual information about API operations for
    better error tracking and debugging in production.

    Example:
        >>> context = ErrorContext(
        ...     operation="get_candidacy",
        ...     resource_type="candidacy",
        ...     resource_id="cand_123",
        ...     params={"fields": ["id", "name"]},
        ... )
        >>> logger.error(
        ...     "Failed to fetch candidacy",
        ...     extra={"context": context.to_dict(), "error": str(e)}
        ... )
    """

    operation: str  # Operation being performed (e.g., "get_candidacy", "list_requisitions")
    resource_type: str  # Resource type (e.g., "candidacy", "contact", "requisition")
    resource_id: Optional[str] = None  # Specific resource ID if applicable
    params: Optional[Dict[str, Any]] = None  # Request parameters
    user_id: Optional[str] = None  # User ID if available
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary for logging

        Returns:
            Dictionary with non-None fields
        """
        result = {
            "operation": self.operation,
            "resource_type": self.resource_type,
        }

        if self.resource_id:
            result["resource_id"] = self.resource_id

        if self.params:
            result["params"] = self.params

        if self.user_id:
            result["user_id"] = self.user_id

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def __str__(self) -> str:
        """String representation for debugging"""
        parts = [f"{self.operation}({self.resource_type}"]

        if self.resource_id:
            parts.append(f" id={self.resource_id}")

        if self.params:
            param_str = ", ".join(f"{k}={v}" for k, v in list(self.params.items())[:3])
            parts.append(f" params={{{param_str}}}")

        parts.append(")")

        return "".join(parts)


class OperationContext:
    """
    Context manager for structured error logging

    Automatically logs errors with context on exception.

    Example:
        >>> with OperationContext(
        ...     operation="create_candidacy",
        ...     resource_type="candidacy",
        ...     params=candidacy_data,
        ... ) as ctx:
        ...     result = client.candidacies.create(candidacy_data)
        ...     ctx.set_result(result["id"])  # Set resource_id on success

        # On exception, automatically logs error with full context
    """

    def __init__(
        self,
        operation: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        logger=None,
    ):
        """
        Initialize operation context

        Args:
            operation: Operation being performed
            resource_type: Resource type
            resource_id: Specific resource ID if applicable
            params: Request parameters
            user_id: User ID if available
            logger: Logger instance for error logging
        """
        self.context = ErrorContext(
            operation=operation,
            resource_type=resource_type,
            resource_id=resource_id,
            params=params,
            user_id=user_id,
        )
        self.logger = logger

    def __enter__(self):
        """Enter context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and log errors"""
        if exc_type is not None and self.logger:
            # Log error with context
            self.logger.error(
                f"Operation failed: {self.context.operation}",
                extra={
                    "context": self.context.to_dict(),
                    "error_type": exc_type.__name__,
                    "error": str(exc_val),
                },
                exc_info=True,
            )

        # Don't suppress exception
        return False

    def set_result(self, resource_id: str):
        """
        Set result resource ID

        Useful for create operations where resource_id is known after success.

        Args:
            resource_id: ID of created/updated resource
        """
        self.context.resource_id = resource_id

    def add_metadata(self, key: str, value: Any):
        """
        Add metadata to context

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.context.metadata[key] = value


def create_api_error_context(
    operation: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    **kwargs,
) -> ErrorContext:
    """
    Factory function to create error context for API operations

    Args:
        operation: Operation name (e.g., "get", "create", "update", "list")
        resource_type: Resource type (e.g., "candidacy", "contact")
        resource_id: Optional resource ID
        **kwargs: Additional context (params, user_id, metadata)

    Returns:
        ErrorContext instance

    Example:
        >>> context = create_api_error_context(
        ...     "get",
        ...     "candidacy",
        ...     resource_id="cand_123",
        ...     params={"fields": ["id", "name"]}
        ... )
    """
    return ErrorContext(
        operation=f"{operation}_{resource_type}",
        resource_type=resource_type,
        resource_id=resource_id,
        params=kwargs.get("params"),
        user_id=kwargs.get("user_id"),
        metadata=kwargs.get("metadata", {}),
    )
