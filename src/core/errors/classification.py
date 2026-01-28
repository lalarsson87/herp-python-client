"""
Error Classification System

Intelligent error classification for smart retry strategies.
Only retries transient errors, fails fast on permanent errors.
"""

import functools
import logging
import random
import time
from enum import Enum
from typing import Callable, Optional, Tuple, Type

from ..constants import (
    RETRY_DEFAULT_BASE_DELAY,
    RETRY_DEFAULT_MAX_ATTEMPTS,
    RETRY_MAX_DELAY,
    RETRY_MAX_TOTAL_DURATION,
    RETRY_NETWORK_BASE_DELAY,
    RETRY_RATE_LIMIT_BASE_DELAY,
)
from .exceptions import (
    HerpAuthenticationError,
    HerpNetworkError,
    HerpNotFoundError,
    HerpRateLimitError,
    HerpServerError,
    HerpValidationError,
    NotionAuthenticationError,
    NotionNetworkError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionServerError,
    NotionValidationError,
    PermanentError,
    RetryBudgetExceededError,
    RetryError,
    TransientError,
)

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity classification for retry strategy"""

    TRANSIENT = "transient"  # Temporary error, should retry
    PERMANENT = "permanent"  # Permanent error, fail fast
    DEGRADED = "degraded"  # Service degraded but may recover


class ErrorCategory(Enum):
    """Error category for fine-grained retry strategy"""

    RATE_LIMIT = "rate_limit"  # Rate limiting errors
    NETWORK = "network"  # Network connectivity errors
    AUTHENTICATION = "authentication"  # Auth/permission errors
    VALIDATION = "validation"  # Invalid input/data errors
    NOT_FOUND = "not_found"  # Resource not found errors
    SERVER_ERROR = "server_error"  # Server-side errors
    UNKNOWN = "unknown"  # Unknown/unclassified errors


def classify_error(exception: Exception) -> Tuple[ErrorSeverity, ErrorCategory]:
    """
    Classify error for intelligent retry strategy.

    Uses type-based classification first (more robust), then falls back to
    string matching for unknown exception types.

    Args:
        exception: The exception to classify

    Returns:
        Tuple of (severity, category)

    Example:
        >>> classify_error(HerpRateLimitError("Rate limit"))
        (ErrorSeverity.TRANSIENT, ErrorCategory.RATE_LIMIT)
        >>> classify_error(Exception("401 Unauthorized"))
        (ErrorSeverity.PERMANENT, ErrorCategory.AUTHENTICATION)
    """
    # Type-based classification (robust approach)
    if isinstance(exception, (HerpRateLimitError, NotionRateLimitError)):
        logger.debug(f"Classified as TRANSIENT/RATE_LIMIT by type: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.RATE_LIMIT)

    if isinstance(exception, (HerpAuthenticationError, NotionAuthenticationError)):
        logger.debug(f"Classified as PERMANENT/AUTHENTICATION by type: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.AUTHENTICATION)

    if isinstance(exception, (HerpValidationError, NotionValidationError)):
        logger.debug(f"Classified as PERMANENT/VALIDATION by type: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.VALIDATION)

    if isinstance(exception, (HerpNotFoundError, NotionNotFoundError)):
        logger.debug(f"Classified as PERMANENT/NOT_FOUND by type: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.NOT_FOUND)

    if isinstance(exception, (HerpServerError, NotionServerError)):
        logger.debug(f"Classified as TRANSIENT/SERVER_ERROR by type: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.SERVER_ERROR)

    if isinstance(exception, (HerpNetworkError, NotionNetworkError)):
        logger.debug(f"Classified as TRANSIENT/NETWORK by type: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.NETWORK)

    # Generic type-based classification
    if isinstance(exception, TransientError):
        logger.debug(f"Classified as TRANSIENT by base type: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.UNKNOWN)

    if isinstance(exception, PermanentError):
        logger.debug(f"Classified as PERMANENT by base type: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.UNKNOWN)

    # String-based classification (fallback for unknown exception types)
    error_msg = str(exception).lower()
    error_type = type(exception).__name__.lower()

    # Check for HTTP status codes in exception message
    status_code = None

    # Common patterns for status codes in error messages
    for code in [400, 401, 403, 404, 429, 500, 502, 503, 504]:
        if str(code) in error_msg or f"http {code}" in error_msg:
            status_code = code
            break

    # Rate limiting errors (TRANSIENT)
    rate_limit_indicators = [
        "rate limit",
        "too many requests",
        "quota exceeded",
        "throttle",
        "rate exceeded",
    ]
    if (
        any(indicator in error_msg for indicator in rate_limit_indicators)
        or status_code == 429
    ):
        logger.debug(f"Classified as TRANSIENT/RATE_LIMIT: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.RATE_LIMIT)

    # Authentication/Authorization errors (PERMANENT)
    auth_indicators = [
        "unauthorized",
        "authentication failed",
        "invalid token",
        "forbidden",
        "access denied",
        "permission denied",
        "invalid api key",
        "invalid credentials",
    ]
    if any(indicator in error_msg for indicator in auth_indicators) or status_code in [
        401,
        403,
    ]:
        logger.debug(f"Classified as PERMANENT/AUTHENTICATION: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.AUTHENTICATION)

    # Validation errors (PERMANENT) - Check before NOT_FOUND to catch "missing required"
    validation_indicators = [
        "validation",
        "invalid",
        "bad request",
        "malformed",
        "invalid input",
        "invalid parameter",
        "schema",
        "required field",
        "missing required",
    ]
    if (
        any(indicator in error_msg for indicator in validation_indicators)
        or status_code == 400
    ):
        logger.debug(f"Classified as PERMANENT/VALIDATION: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.VALIDATION)

    # Not Found errors (PERMANENT)
    not_found_indicators = [
        "not found",
        "does not exist",
        "no such",
        "missing",
        "unavailable resource",
    ]
    if (
        any(indicator in error_msg for indicator in not_found_indicators)
        or status_code == 404
    ):
        logger.debug(f"Classified as PERMANENT/NOT_FOUND: {exception}")
        return (ErrorSeverity.PERMANENT, ErrorCategory.NOT_FOUND)

    # Server errors (TRANSIENT for 500s, check specific codes)
    if status_code in [500, 502, 503, 504]:
        logger.debug(f"Classified as TRANSIENT/SERVER_ERROR: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.SERVER_ERROR)

    server_error_indicators = [
        "internal server error",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "server error",
    ]
    if any(indicator in error_msg for indicator in server_error_indicators):
        logger.debug(f"Classified as TRANSIENT/SERVER_ERROR: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.SERVER_ERROR)

    # Network errors (TRANSIENT)
    network_indicators = [
        "timeout",
        "connection",
        "network",
        "socket",
        "dns",
        "host",
        "unreachable",
        "reset",
        "connectionerror",
        "timeouterror",
        "refused",
    ]
    if any(indicator in error_msg for indicator in network_indicators):
        logger.debug(f"Classified as TRANSIENT/NETWORK: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.NETWORK)

    # Check exception type
    if "timeout" in error_type or "connection" in error_type:
        logger.debug(f"Classified as TRANSIENT/NETWORK by type: {exception}")
        return (ErrorSeverity.TRANSIENT, ErrorCategory.NETWORK)

    # Default to transient for unknown errors (conservative approach)
    logger.debug(f"Classified as TRANSIENT/UNKNOWN (default): {exception}")
    return (ErrorSeverity.TRANSIENT, ErrorCategory.UNKNOWN)


def calculate_backoff(
    attempt: int,
    category: ErrorCategory,
    base_delay: float = RETRY_DEFAULT_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    jitter: bool = True,
) -> float:
    """
    Calculate backoff delay based on error category.

    Different error categories use different backoff strategies:
    - RATE_LIMIT: Longer delays to respect rate limits
    - NETWORK: Moderate delays for network recovery
    - SERVER_ERROR: Standard exponential backoff
    - Others: Base exponential backoff

    Args:
        attempt: Current attempt number (0-indexed)
        category: Error category
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter

    Returns:
        Delay in seconds

    Example:
        >>> calculate_backoff(0, ErrorCategory.RATE_LIMIT)
        5.0
        >>> calculate_backoff(2, ErrorCategory.NETWORK)
        4.0
    """
    # Category-specific backoff strategies
    if category == ErrorCategory.RATE_LIMIT:
        # Rate limit: Start with longer delays
        delay = min(RETRY_RATE_LIMIT_BASE_DELAY * (2**attempt), max_delay)
    elif category == ErrorCategory.NETWORK:
        # Network: Moderate delays
        delay = min(RETRY_NETWORK_BASE_DELAY * (2**attempt), max_delay)
    elif category == ErrorCategory.SERVER_ERROR:
        # Server error: Standard exponential backoff
        delay = min(base_delay * (2**attempt), max_delay)
    else:
        # Default exponential backoff
        delay = min(base_delay * (2**attempt), max_delay)

    # Add jitter to prevent thundering herd
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return float(delay)


def smart_retry(
    max_attempts: int = RETRY_DEFAULT_MAX_ATTEMPTS,
    base_delay: float = RETRY_DEFAULT_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    max_total_duration: Optional[float] = RETRY_MAX_TOTAL_DURATION,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[
        Callable[[Exception, int, ErrorSeverity, ErrorCategory], None]
    ] = None,
) -> Callable:
    """
    Smart retry decorator that uses error classification.

    Only retries transient errors, fails fast on permanent errors.
    Uses category-specific backoff strategies with optional retry budget.

    Args:
        max_attempts: Maximum number of attempts (including first try)
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds
        max_total_duration: Maximum total time (seconds) to spend retrying.
                          None means no limit. Prevents runaway retries.
        jitter: Whether to add random jitter
        retryable_exceptions: Tuple of exception types to consider
        on_retry: Optional callback(exception, attempt, severity, category)

    Returns:
        Decorated function

    Example:
        >>> @smart_retry(max_attempts=3, max_total_duration=30.0)
        ... def fetch_data():
        ...     # Will retry transient errors, fail fast on permanent
        ...     # Will also fail fast if retries exceed 30 seconds total
        ...     return api.get("/data")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            retry_start_time = time.time() if max_total_duration else None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Only classify if exception type matches
                    if not isinstance(e, retryable_exceptions):
                        logger.debug(
                            f"{func.__name__}: Exception type {type(e).__name__} "
                            f"not in retryable types, not retrying"
                        )
                        raise

                    # Classify the error
                    severity, category = classify_error(e)

                    # Fail fast on permanent errors
                    if severity == ErrorSeverity.PERMANENT:
                        logger.warning(
                            f"{func.__name__}: Permanent error ({category.value}), "
                            f"not retrying: {e}"
                        )
                        raise

                    # Check retry budget BEFORE checking max attempts
                    # This ensures budget is enforced even if we haven't hit max attempts
                    if (
                        max_total_duration
                        and retry_start_time is not None
                        and attempt > 0
                    ):
                        elapsed = time.time() - retry_start_time
                        if elapsed >= max_total_duration:
                            logger.warning(
                                f"{func.__name__}: Retry budget of {max_total_duration:.1f}s "
                                f"exceeded (elapsed: {elapsed:.1f}s) before attempt {attempt + 1}"
                            )
                            raise RetryBudgetExceededError(
                                f"Retry budget of {max_total_duration:.1f}s exceeded "
                                f"after {attempt} attempts (elapsed: {elapsed:.1f}s). "
                                f"Last error: {last_exception}"
                            ) from last_exception

                    # Check if we have attempts left
                    if attempt >= max_attempts - 1:
                        logger.warning(
                            f"{func.__name__}: All {max_attempts} attempts failed "
                            f"with {severity.value}/{category.value} error"
                        )
                        break

                    # Calculate category-specific delay
                    delay = calculate_backoff(
                        attempt,
                        category,
                        base_delay=base_delay,
                        max_delay=max_delay,
                        jitter=jitter,
                    )

                    logger.info(
                        f"{func.__name__}: Attempt {attempt + 1}/{max_attempts} failed "
                        f"with {severity.value}/{category.value} error, "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    # Call retry callback if provided
                    if on_retry:
                        on_retry(e, attempt, severity, category)

                    # Wait before retrying
                    time.sleep(delay)

            # All attempts exhausted
            raise RetryError(
                f"Failed after {max_attempts} attempts. Last error: {last_exception}"
            ) from last_exception

        return wrapper

    return decorator
