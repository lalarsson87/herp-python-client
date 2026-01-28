"""
Exception Types for HERP-Notion Integration

Explicit exception classes for better error handling and classification.
Replaces fragile string matching with type-based error classification.
"""

# ============================================================================
# Base Exceptions
# ============================================================================


class HerpNotionError(Exception):
    """Base exception for all HERP-Notion integration errors"""

    pass


class TransientError(HerpNotionError):
    """Base class for transient errors that should be retried"""

    pass


class PermanentError(HerpNotionError):
    """Base class for permanent errors that should fail-fast"""

    pass


# ============================================================================
# HERP API Exceptions
# ============================================================================


class HerpAPIError(HerpNotionError):
    """Base exception for HERP API errors"""

    pass


class HerpRateLimitError(TransientError, HerpAPIError):
    """HERP API rate limit exceeded"""

    pass


class HerpAuthenticationError(PermanentError, HerpAPIError):
    """HERP API authentication failed (401, 403)"""

    pass


class HerpValidationError(PermanentError, HerpAPIError):
    """HERP API validation error (400, invalid input)"""

    pass


class HerpNotFoundError(PermanentError, HerpAPIError):
    """HERP API resource not found (404)"""

    pass


class HerpServerError(TransientError, HerpAPIError):
    """HERP API server error (500, 502, 503, 504)"""

    pass


class HerpNetworkError(TransientError, HerpAPIError):
    """HERP API network connectivity error"""

    pass


# ============================================================================
# Notion API Exceptions
# ============================================================================


class NotionAPIError(HerpNotionError):
    """Base exception for Notion API errors"""

    pass


class NotionRateLimitError(TransientError, NotionAPIError):
    """Notion API rate limit exceeded"""

    pass


class NotionAuthenticationError(PermanentError, NotionAPIError):
    """Notion API authentication failed (401, 403)"""

    pass


class NotionValidationError(PermanentError, NotionAPIError):
    """Notion API validation error (400, invalid input)"""

    pass


class NotionNotFoundError(PermanentError, NotionAPIError):
    """Notion API resource not found (404)"""

    pass


class NotionServerError(TransientError, NotionAPIError):
    """Notion API server error (500, 502, 503, 504)"""

    pass


class NotionNetworkError(TransientError, NotionAPIError):
    """Notion API network connectivity error"""

    pass


# ============================================================================
# Sync Exceptions
# ============================================================================


class SyncError(HerpNotionError):
    """Base exception for sync operation errors"""

    pass


class SyncValidationError(PermanentError, SyncError):
    """Sync validation error (invalid configuration, missing fields)"""

    pass


class SyncDataError(PermanentError, SyncError):
    """Sync data error (data transformation failed, mapping error)"""

    pass


class SyncTimeoutError(TransientError, SyncError):
    """Sync operation timed out"""

    pass


# ============================================================================
# Cache Exceptions
# ============================================================================


class CacheError(HerpNotionError):
    """Base exception for cache errors"""

    pass


class CacheFullError(TransientError, CacheError):
    """Cache is full (should trigger eviction but can retry)"""

    pass


class CacheSerializationError(PermanentError, CacheError):
    """Failed to serialize/deserialize cache entry"""

    pass


# ============================================================================
# Circuit Breaker Exceptions
# ============================================================================


class CircuitBreakerError(TransientError):
    """Circuit breaker is open (service is down)"""

    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Circuit breaker is open and rejecting requests"""

    pass


# ============================================================================
# Retry Exceptions
# ============================================================================


class RetryError(HerpNotionError):
    """Base exception for retry mechanism errors"""

    pass


class RetryBudgetExceededError(RetryError):
    """Retry budget (max total duration) exceeded"""

    pass


# ============================================================================
# Helper Functions
# ============================================================================


def exception_from_http_status(
    status_code: int, message: str, api: str = "herp"
) -> HerpNotionError:
    """
    Create appropriate exception from HTTP status code

    Args:
        status_code: HTTP status code
        message: Error message
        api: API name ("herp" or "notion")

    Returns:
        Appropriate exception instance

    Example:
        >>> exc = exception_from_http_status(429, "Rate limit exceeded", "herp")
        >>> isinstance(exc, HerpRateLimitError)
        True
    """
    api = api.lower()

    # Map status codes to exception classes
    # Type annotation: all exceptions inherit from HerpNotionError
    default_exc: type[HerpNotionError]

    if api == "herp":
        status_map = {
            400: HerpValidationError,
            401: HerpAuthenticationError,
            403: HerpAuthenticationError,
            404: HerpNotFoundError,
            429: HerpRateLimitError,
            500: HerpServerError,
            502: HerpServerError,
            503: HerpServerError,
            504: HerpServerError,
        }
        default_exc = HerpAPIError
    elif api == "notion":
        status_map = {
            400: NotionValidationError,
            401: NotionAuthenticationError,
            403: NotionAuthenticationError,
            404: NotionNotFoundError,
            429: NotionRateLimitError,
            500: NotionServerError,
            502: NotionServerError,
            503: NotionServerError,
            504: NotionServerError,
        }
        default_exc = NotionAPIError
    else:
        status_map = {}
        default_exc = HerpNotionError

    exc_class = status_map.get(status_code, default_exc)
    return exc_class(f"{message} (HTTP {status_code})")


def is_transient_error(exc: Exception) -> bool:
    """
    Check if exception is transient (should retry)

    Args:
        exc: Exception to check

    Returns:
        True if transient, False otherwise

    Example:
        >>> exc = HerpRateLimitError("Rate limit")
        >>> is_transient_error(exc)
        True
        >>> exc = HerpAuthenticationError("Invalid token")
        >>> is_transient_error(exc)
        False
    """
    return isinstance(exc, TransientError)


def is_permanent_error(exc: Exception) -> bool:
    """
    Check if exception is permanent (should fail-fast)

    Args:
        exc: Exception to check

    Returns:
        True if permanent, False otherwise

    Example:
        >>> exc = HerpValidationError("Invalid input")
        >>> is_permanent_error(exc)
        True
    """
    return isinstance(exc, PermanentError)
