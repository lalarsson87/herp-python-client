"""
Circuit Breaker Pattern Implementation (Async and Sync)

This module provides both synchronous and asynchronous circuit breakers.
For sync-only circuit breaker, see utils.circuit_breaker.
"""

import asyncio
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional

from .constants import (
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
)
from .errors.exceptions import CircuitBreakerOpenError
from .utils.circuit_breaker import CircuitBreakerConfig, CircuitState
from .utils.logging import get_logger

logger = get_logger(__name__)


class AsyncCircuitBreaker:
    """
    Async circuit breaker implementation

    Tracks failures and opens circuit when threshold is exceeded.
    Automatically attempts recovery after timeout period.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize async circuit breaker

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
        logger.info(f"Async circuit breaker initialized: {config}")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    await self._transition_to_half_open()
                else:
                    logger.warning(
                        f"Async circuit breaker {self.config.name} is OPEN, "
                        f"rejecting call"
                    )
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker {self.config.name} is open"
                    )

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                await self._on_success()
            return result
        except Exception as e:
            async with self._lock:
                await self._on_failure()
            raise

    async def _on_success(self) -> None:
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Async circuit breaker {self.config.name} success in HALF_OPEN "
                f"({self.success_count}/{self.config.success_threshold})"
            )

            if self.success_count >= self.config.success_threshold:
                await self._transition_to_closed()
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.debug(
            f"Async circuit breaker {self.config.name} failure "
            f"({self.failure_count}/{self.config.fail_max})"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            await self._transition_to_open()
        elif self.failure_count >= self.config.fail_max:
            await self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.config.timeout_duration

    async def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        logger.warning(
            f"Async circuit breaker {self.config.name} opened after failures"
        )

    async def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info(
            f"Async circuit breaker {self.config.name} transitioning to HALF_OPEN "
            f"(testing recovery)"
        )

    async def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Async circuit breaker {self.config.name} closed (recovered)")

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Async circuit breaker {self.config.name} manually reset")

    def get_state(self) -> CircuitState:
        """Get current circuit state"""
        return self.state

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "config": {
                "name": self.config.name,
                "fail_max": self.config.fail_max,
                "success_threshold": self.config.success_threshold,
                "timeout_duration": self.config.timeout_duration,
            },
        }


class AsyncCircuitBreakerWrapper:
    """
    Convenience wrapper for async circuit breaker decorator

    Provides easy integration with existing async functions.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize async circuit breaker wrapper

        Args:
            config: Circuit breaker configuration
        """
        self.circuit_breaker = AsyncCircuitBreaker(config)

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap async function with circuit breaker

        Args:
            func: Async function to wrap

        Returns:
            Wrapped function
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.circuit_breaker.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with circuit breaker protection

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        return await self.circuit_breaker.call(func, *args, **kwargs)

    async def reset(self) -> None:
        """Reset the circuit breaker"""
        await self.circuit_breaker.reset()

    def get_state(self) -> CircuitState:
        """Get current state"""
        return self.circuit_breaker.get_state()

    def get_stats(self) -> dict:
        """Get statistics"""
        return self.circuit_breaker.get_stats()


# Re-export from utils for convenience
__all__ = [
    "AsyncCircuitBreaker",
    "AsyncCircuitBreakerWrapper",
    "CircuitBreakerConfig",
    "CircuitState",
]
