#!/usr/bin/env python3
"""
Async HERP API Rate Limiter

Implements non-blocking rate limiting for HERP API calls using asyncio.
Complies with the 100 requests/minute rate limit without blocking the event loop.
"""

import asyncio
import time
from collections import deque
from typing import Optional


class AsyncHerpRateLimiter:
    """
    Async token bucket rate limiter for HERP API

    HERP API has a rate limit of 100 requests per minute per tenant.
    This implementation uses a token bucket algorithm with asyncio for non-blocking operation.

    Example:
        >>> async def main():
        ...     limiter = AsyncHerpRateLimiter()
        ...     await limiter.acquire()
        ...     response = await make_api_call()
        ...
        >>> asyncio.run(main())
    """

    def __init__(
        self, requests_per_minute: int = 100, burst_size: Optional[int] = None
    ):
        """
        Initialize async rate limiter

        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Maximum burst size (default: same as requests_per_minute)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute

        # Calculate delay between requests
        self.min_interval = 60.0 / requests_per_minute

        # Token bucket
        self.tokens = float(self.burst_size)
        self.last_refill = time.time()

        # Async lock for thread-safe operations across coroutines
        self.lock = asyncio.Lock()

        # Track request timestamps for monitoring
        self.request_history: deque = deque(maxlen=requests_per_minute)

    def _refill_tokens(self):
        """Refill tokens based on elapsed time (synchronous helper)"""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * (self.requests_per_minute / 60.0)

        if tokens_to_add >= 1.0:
            self.tokens = min(self.burst_size, self.tokens + int(tokens_to_add))
            self.last_refill = now

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire permission to make a request (async, non-blocking)

        Args:
            timeout: Maximum time to wait in seconds (None = wait indefinitely)

        Returns:
            True if permission granted, False if timeout

        Raises:
            asyncio.TimeoutError: If timeout is exceeded

        Example:
            >>> async with limiter.acquire():
            ...     response = await make_api_call()
        """
        start_time = time.time()

        while True:
            async with self.lock:
                self._refill_tokens()

                # Check if we have tokens available
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    self.request_history.append(time.time())
                    return True

                # Check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False

                # Calculate wait time for next token
                wait_time = self.min_interval / 2

            # Wait outside the lock to allow other coroutines to proceed
            await asyncio.sleep(wait_time)

    async def wait(self):
        """
        Block (async) until a request can be made

        This is equivalent to acquire(timeout=None)

        Example:
            >>> await limiter.wait()
            >>> response = await make_api_call()
        """
        await self.acquire(timeout=None)

    def get_current_rate(self) -> float:
        """
        Get current request rate (requests per minute)

        Returns:
            Current rate based on recent request history

        Note: This is synchronous for quick stats access
        """
        now = time.time()
        one_minute_ago = now - 60.0

        # Count requests in the last minute
        recent_requests = sum(
            1 for timestamp in self.request_history if timestamp >= one_minute_ago
        )

        return float(recent_requests)

    async def get_available_tokens(self) -> float:
        """
        Get number of available tokens (async)

        Returns:
            Number of requests that can be made immediately
        """
        async with self.lock:
            self._refill_tokens()
            return self.tokens

    async def reset(self):
        """Reset the rate limiter to initial state (async)"""
        async with self.lock:
            self.tokens = float(self.burst_size)
            self.last_refill = time.time()
            self.request_history.clear()

    async def __aenter__(self):
        """Async context manager entry - acquire token"""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass


class AsyncAdaptiveRateLimiter(AsyncHerpRateLimiter):
    """
    Async adaptive rate limiter that adjusts based on API responses

    Monitors the x-remaining-request header from HERP API responses
    and adjusts rate limiting accordingly without blocking the event loop.

    Example:
        >>> async def main():
        ...     limiter = AsyncAdaptiveRateLimiter()
        ...     await limiter.acquire()
        ...     response = await make_api_call()
        ...     limiter.update_from_response_headers(response.headers)
        ...
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: Optional[int] = None,
        safety_margin: float = 0.9,
    ):
        """
        Initialize async adaptive rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
            safety_margin: Safety factor (0.9 = use 90% of limit)
        """
        super().__init__(requests_per_minute, burst_size)
        self.safety_margin = safety_margin
        self.api_remaining: Optional[int] = None
        self.last_api_check = time.time()

    def update_from_response_headers(self, headers: dict):
        """
        Update rate limiter based on API response headers (synchronous)

        This is synchronous because it's typically called immediately after
        receiving a response, before the next request.

        Args:
            headers: Response headers from HERP API

        Example:
            >>> response = await client.get(url)
            >>> limiter.update_from_response_headers(response.headers)
        """
        # Check for x-remaining-request header
        remaining = headers.get("x-remaining-request")
        if remaining is not None:
            try:
                self.api_remaining = int(remaining)
                self.last_api_check = time.time()

                # Adjust tokens if we're close to the limit
                # Note: Direct token manipulation without lock is safe here
                # as it only reduces tokens, making it conservative
                if self.api_remaining < 10:
                    # Very close to limit, reduce tokens significantly
                    self.tokens = min(self.tokens, self.api_remaining * 0.5)
                elif self.api_remaining < 30:
                    # Getting close, be conservative
                    self.tokens = min(self.tokens, self.api_remaining * 0.8)

            except (ValueError, TypeError):
                pass

    async def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire with adaptive behavior (async, non-blocking)

        Checks API remaining count before acquiring if available.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if permission granted, False if timeout
        """
        # If we know we're at the limit, handle timeout appropriately
        if self.api_remaining is not None and self.api_remaining <= 0:
            if timeout is not None and timeout < 60.0:
                # Timeout is less than the wait period, so we'll timeout
                return False

            # Wait for the rate limit to reset
            # HERP resets per minute, so wait up to 60 seconds
            await asyncio.sleep(60.0)

            # Adjust timeout for remaining time
            if timeout is not None:
                timeout = max(0, timeout - 60.0)

        return await super().acquire(timeout=timeout)


# Global async rate limiter instance
_global_async_limiter: Optional[AsyncHerpRateLimiter] = None
_limiter_lock = asyncio.Lock()


async def get_async_rate_limiter(
    requests_per_minute: int = 100, adaptive: bool = True
) -> AsyncHerpRateLimiter:
    """
    Get or create global async rate limiter

    Args:
        requests_per_minute: Rate limit (only used on first call)
        adaptive: Use adaptive rate limiter (only used on first call)

    Returns:
        Global async rate limiter instance

    Example:
        >>> async def main():
        ...     limiter = await get_async_rate_limiter()
        ...     await limiter.acquire()
        ...     response = await make_api_call()
    """
    global _global_async_limiter

    async with _limiter_lock:
        if _global_async_limiter is None:
            if adaptive:
                _global_async_limiter = AsyncAdaptiveRateLimiter(
                    requests_per_minute=requests_per_minute
                )
            else:
                _global_async_limiter = AsyncHerpRateLimiter(
                    requests_per_minute=requests_per_minute
                )

    return _global_async_limiter


async def reset_async_rate_limiter():
    """
    Reset global async rate limiter

    Primarily for testing purposes.
    """
    global _global_async_limiter

    async with _limiter_lock:
        _global_async_limiter = None
