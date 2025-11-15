"""
Error Classification Module

Provides intelligent error classification for smart retry strategies.
Categorizes errors as transient (retryable) or permanent (fail-fast).
"""

from .classification import (
    ErrorSeverity,
    ErrorCategory,
    classify_error,
    calculate_backoff,
    smart_retry,
)
from .exceptions import (
    # Base exceptions
    HerpNotionError,
    TransientError,
    PermanentError,
    # HERP exceptions
    HerpAPIError,
    HerpRateLimitError,
    HerpAuthenticationError,
    HerpValidationError,
    HerpNotFoundError,
    HerpServerError,
    HerpNetworkError,
    # Notion exceptions
    NotionAPIError,
    NotionRateLimitError,
    NotionAuthenticationError,
    NotionValidationError,
    NotionNotFoundError,
    NotionServerError,
    NotionNetworkError,
    # Sync exceptions
    SyncError,
    SyncValidationError,
    SyncDataError,
    SyncTimeoutError,
    # Cache exceptions
    CacheError,
    CacheFullError,
    CacheSerializationError,
    # Circuit breaker
    CircuitBreakerError,
    # Retry
    RetryError,
    RetryBudgetExceededError,
    # Helpers
    exception_from_http_status,
    is_transient_error,
    is_permanent_error,
)

__all__ = [
    # Classification
    "ErrorSeverity",
    "ErrorCategory",
    "classify_error",
    "calculate_backoff",
    "smart_retry",
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
