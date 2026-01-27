"""
Utility Decorators

Provides retry decorators and other utility decorators for API clients.
"""

import asyncio
import time
from functools import wraps
from typing import Callable, Optional, Type, Tuple

from ..constants import (
    RETRY_DEFAULT_MAX_ATTEMPTS,
    RETRY_DEFAULT_BASE_DELAY,
    RETRY_MAX_DELAY,
)
from ..errors.exceptions import (
    TransientError,
    HerpRateLimitError,
    NotionRateLimitError,
)
from .logging import get_logger

logger = get_logger(__name__)


def smart_retry(
    max_attempts: int = RETRY_DEFAULT_MAX_ATTEMPTS,
    base_delay: float = RETRY_DEFAULT_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    exponential_backoff: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator for synchronous retry logic with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        exponential_backoff: Use exponential backoff (default: True)
        retry_on: Tuple of exception types to retry on (default: TransientError)
        retryable_exceptions: Alias for retry_on (for backward compatibility)

    Returns:
        Decorated function with retry logic
    """
    # Support both parameter names
    if retryable_exceptions is not None:
        retry_on = retryable_exceptions
    if retry_on is None:
        retry_on = (TransientError,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    if exponential_backoff:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay

                    # Add extra delay for rate limit errors
                    if isinstance(e, (HerpRateLimitError, NotionRateLimitError)):
                        delay = max(delay, 5.0)  # Minimum 5s for rate limits

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def async_smart_retry(
    max_attempts: int = RETRY_DEFAULT_MAX_ATTEMPTS,
    base_delay: float = RETRY_DEFAULT_BASE_DELAY,
    max_delay: float = RETRY_MAX_DELAY,
    exponential_backoff: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator for asynchronous retry logic with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries
        exponential_backoff: Use exponential backoff (default: True)
        retry_on: Tuple of exception types to retry on (default: TransientError)
        retryable_exceptions: Alias for retry_on (for backward compatibility)

    Returns:
        Decorated async function with retry logic
    """
    # Support both parameter names
    if retryable_exceptions is not None:
        retry_on = retryable_exceptions
    if retry_on is None:
        retry_on = (TransientError,)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    if exponential_backoff:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay

                    # Add extra delay for rate limit errors
                    if isinstance(e, (HerpRateLimitError, NotionRateLimitError)):
                        delay = max(delay, 5.0)  # Minimum 5s for rate limits

                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
