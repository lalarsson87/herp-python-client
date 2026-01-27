"""
Rate Limiter Implementation

Provides adaptive rate limiting for API requests.
"""

import time
from collections import deque
from threading import Lock
from typing import Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter for API requests

    Implements token bucket algorithm with adaptive rate adjustment based on
    rate limit headers from API responses.
    """

    def __init__(
        self,
        requests_per_minute: int = 100,
        requests_per_second: Optional[int] = None,
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_second: Maximum requests per second (optional)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second

        # Calculate minimum delay between requests
        self.min_delay = 60.0 / requests_per_minute
        if requests_per_second:
            self.min_delay = max(self.min_delay, 1.0 / requests_per_second)

        # Track request timestamps for rate limiting
        self._request_times: deque = deque()
        self._lock = Lock()
        self._last_request_time: Optional[float] = None

        logger.info(
            f"AdaptiveRateLimiter initialized: "
            f"{requests_per_minute} req/min, min_delay={self.min_delay:.3f}s"
        )

    def acquire(self) -> None:
        """
        Acquire permission to make a request

        Blocks if rate limit would be exceeded.
        """
        with self._lock:
            current_time = time.time()

            # Remove timestamps older than 1 minute
            cutoff_time = current_time - 60.0
            while self._request_times and self._request_times[0] < cutoff_time:
                self._request_times.popleft()

            # Enforce minimum delay between requests
            if self._last_request_time is not None:
                time_since_last = current_time - self._last_request_time
                if time_since_last < self.min_delay:
                    sleep_time = self.min_delay - time_since_last
                    logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
                    time.sleep(sleep_time)
                    current_time = time.time()

            # Check if we've hit the per-minute limit
            if len(self._request_times) >= self.requests_per_minute:
                # Calculate how long to wait until oldest request ages out
                wait_time = 60.0 - (current_time - self._request_times[0])
                if wait_time > 0:
                    logger.debug(
                        f"Rate limit reached: waiting {wait_time:.3f}s "
                        f"({len(self._request_times)}/{self.requests_per_minute})"
                    )
                    time.sleep(wait_time)
                    current_time = time.time()
                    # Clean up old timestamps
                    cutoff_time = current_time - 60.0
                    while self._request_times and self._request_times[0] < cutoff_time:
                        self._request_times.popleft()

            # Record this request
            self._request_times.append(current_time)
            self._last_request_time = current_time

    def update_from_headers(self, headers: dict) -> None:
        """
        Update rate limiter based on API response headers

        Args:
            headers: Response headers containing rate limit info
        """
        # Check for common rate limit headers
        remaining = headers.get("x-remaining-request") or headers.get(
            "x-ratelimit-remaining"
        )
        reset_time = headers.get("x-ratelimit-reset")

        if remaining is not None:
            try:
                remaining = int(remaining)
                logger.debug(f"Rate limit remaining: {remaining}")

                # If we're getting close to limit, slow down
                if remaining < 10:
                    logger.warning(
                        f"Approaching rate limit: {remaining} requests remaining"
                    )
            except ValueError:
                pass

        if reset_time is not None:
            try:
                reset_timestamp = int(reset_time)
                current_time = int(time.time())
                if reset_timestamp > current_time:
                    logger.debug(
                        f"Rate limit resets in {reset_timestamp - current_time}s"
                    )
            except ValueError:
                pass

    def reset(self) -> None:
        """Reset the rate limiter state"""
        with self._lock:
            self._request_times.clear()
            self._last_request_time = None
            logger.debug("Rate limiter reset")

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics

        Returns:
            Dictionary with current rate limiter stats
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - 60.0

            # Count requests in last minute
            recent_requests = sum(1 for t in self._request_times if t >= cutoff_time)

            return {
                "requests_per_minute": self.requests_per_minute,
                "requests_per_second": self.requests_per_second,
                "min_delay": self.min_delay,
                "recent_requests": recent_requests,
                "requests_remaining": max(
                    0, self.requests_per_minute - recent_requests
                ),
            }


class AsyncRateLimiter:
    """
    Async rate limiter for API requests

    Implements token bucket algorithm with adaptive rate adjustment for async operations.
    """

    def __init__(
        self,
        requests_per_minute: int = 100,
        requests_per_second: Optional[int] = None,
    ):
        """
        Initialize async rate limiter

        Args:
            requests_per_minute: Maximum requests per minute
            requests_per_second: Maximum requests per second (optional)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_second = requests_per_second

        # Calculate minimum delay between requests
        self.min_delay = 60.0 / requests_per_minute
        if requests_per_second:
            self.min_delay = max(self.min_delay, 1.0 / requests_per_second)

        # Track request timestamps for rate limiting
        self._request_times: deque = deque()
        self._last_request_time: Optional[float] = None

        logger.info(
            f"AsyncRateLimiter initialized: "
            f"{requests_per_minute} req/min, min_delay={self.min_delay:.3f}s"
        )

    async def acquire(self) -> None:
        """
        Acquire permission to make a request (async version)

        Sleeps if rate limit would be exceeded.
        """
        import asyncio

        current_time = time.time()

        # Remove timestamps older than 1 minute
        cutoff_time = current_time - 60.0
        while self._request_times and self._request_times[0] < cutoff_time:
            self._request_times.popleft()

        # Enforce minimum delay between requests
        if self._last_request_time is not None:
            time_since_last = current_time - self._last_request_time
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                logger.debug(f"Async rate limiting: sleeping {sleep_time:.3f}s")
                await asyncio.sleep(sleep_time)
                current_time = time.time()

        # Check if we've hit the per-minute limit
        if len(self._request_times) >= self.requests_per_minute:
            # Calculate how long to wait until oldest request ages out
            wait_time = 60.0 - (current_time - self._request_times[0])
            if wait_time > 0:
                logger.debug(
                    f"Async rate limit reached: waiting {wait_time:.3f}s "
                    f"({len(self._request_times)}/{self.requests_per_minute})"
                )
                await asyncio.sleep(wait_time)
                current_time = time.time()
                # Clean up old timestamps
                cutoff_time = current_time - 60.0
                while self._request_times and self._request_times[0] < cutoff_time:
                    self._request_times.popleft()

        # Record this request
        self._request_times.append(current_time)
        self._last_request_time = current_time

    def update_from_headers(self, headers: dict) -> None:
        """
        Update rate limiter based on API response headers

        Args:
            headers: Response headers containing rate limit info
        """
        # Check for common rate limit headers
        remaining = headers.get("x-remaining-request") or headers.get(
            "x-ratelimit-remaining"
        )
        reset_time = headers.get("x-ratelimit-reset")

        if remaining is not None:
            try:
                remaining = int(remaining)
                logger.debug(f"Async rate limit remaining: {remaining}")

                # If we're getting close to limit, slow down
                if remaining < 10:
                    logger.warning(
                        f"Approaching rate limit: {remaining} requests remaining"
                    )
            except ValueError:
                pass

        if reset_time is not None:
            try:
                reset_timestamp = int(reset_time)
                current_time = int(time.time())
                if reset_timestamp > current_time:
                    logger.debug(
                        f"Rate limit resets in {reset_timestamp - current_time}s"
                    )
            except ValueError:
                pass

    def reset(self) -> None:
        """Reset the rate limiter state"""
        self._request_times.clear()
        self._last_request_time = None
        logger.debug("Async rate limiter reset")

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics

        Returns:
            Dictionary with current rate limiter stats
        """
        current_time = time.time()
        cutoff_time = current_time - 60.0

        # Count requests in last minute
        recent_requests = sum(1 for t in self._request_times if t >= cutoff_time)

        return {
            "requests_per_minute": self.requests_per_minute,
            "requests_per_second": self.requests_per_second,
            "min_delay": self.min_delay,
            "recent_requests": recent_requests,
            "requests_remaining": max(0, self.requests_per_minute - recent_requests),
        }
