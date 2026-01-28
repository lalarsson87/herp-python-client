"""
Error Classification Module

Provides intelligent error classification for smart retry strategies.
Categorizes errors as transient (retryable) or permanent (fail-fast).
"""

from .classification import (
    ErrorCategory,
    ErrorSeverity,
    calculate_backoff,
    classify_error,
    smart_retry,
)
from .context import (
    ErrorContext,
    OperationContext,
    create_api_error_context,
)
from .exceptions import (  # Base exceptions; HERP exceptions; Notion exceptions; Sync exceptions; Cache exceptions; Circuit breaker; Retry; Helpers
    CacheError,
    CacheFullError,
    CacheSerializationError,
    CircuitBreakerError,
    HerpAPIError,
    HerpAuthenticationError,
    HerpNetworkError,
    HerpNotFoundError,
    HerpNotionError,
    HerpRateLimitError,
    HerpServerError,
    HerpValidationError,
    NotionAPIError,
    NotionAuthenticationError,
    NotionNetworkError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionServerError,
    NotionValidationError,
    PermanentError,
    RetryBudgetExceededError,
    RetryError,
    SyncDataError,
    SyncError,
    SyncTimeoutError,
    SyncValidationError,
    TransientError,
    exception_from_http_status,
    is_permanent_error,
    is_transient_error,
)

__all__ = [
    # Classification
    "ErrorSeverity",
    "ErrorCategory",
    "classify_error",
    "calculate_backoff",
    "smart_retry",
    # Context
    "ErrorContext",
    "OperationContext",
    "create_api_error_context",
    # Base exceptions
    "HerpNotionError",
    "TransientError",
    "PermanentError",
    # HERP exceptions
    "HerpAPIError",
    "HerpRateLimitError",
    "HerpAuthenticationError",
    "HerpValidationError",
    "HerpNotFoundError",
    "HerpServerError",
    "HerpNetworkError",
    # Notion exceptions
    "NotionAPIError",
    "NotionRateLimitError",
    "NotionAuthenticationError",
    "NotionValidationError",
    "NotionNotFoundError",
    "NotionServerError",
    "NotionNetworkError",
    # Sync exceptions
    "SyncError",
    "SyncValidationError",
    "SyncDataError",
    "SyncTimeoutError",
    # Cache exceptions
    "CacheError",
    "CacheFullError",
    "CacheSerializationError",
    # Circuit breaker
    "CircuitBreakerError",
    # Retry
    "RetryError",
    "RetryBudgetExceededError",
    # Helpers
    "exception_from_http_status",
    "is_transient_error",
    "is_permanent_error",
]
