"""
Circuit Breaker Pattern Implementation

Prevents cascading failures by failing fast when error threshold is exceeded.
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

from ..constants import (
    CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD,
    CIRCUIT_BREAKER_TIMEOUT,
)
from ..errors.exceptions import CircuitBreakerOpenError
from .logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    name: str
    fail_max: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD
    success_threshold: int = CIRCUIT_BREAKER_SUCCESS_THRESHOLD
    timeout_duration: float = CIRCUIT_BREAKER_TIMEOUT

    def __str__(self) -> str:
        return (
            f"CircuitBreaker({self.name}, fail_max={self.fail_max}, "
            f"success_threshold={self.success_threshold}, "
            f"timeout={self.timeout_duration}s)"
        )


class CircuitBreaker:
    """
    Circuit breaker implementation

    Tracks failures and opens circuit when threshold is exceeded.
    Automatically attempts recovery after timeout period.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker

        Args:
            config: Circuit breaker configuration
        """
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        logger.info(
            "circuit_breaker.initialized",
            name=config.name,
            fail_max=config.fail_max,
            success_threshold=config.success_threshold,
            timeout_duration=config.timeout_duration,
        )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                logger.warning(
                    "circuit_breaker.rejected",
                    name=self.config.name,
                    state=self.state.value,
                    failure_count=self.failure_count,
                )
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.config.name} is open"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                "circuit_breaker.success",
                name=self.config.name,
                state=self.state.value,
                success_count=self.success_count,
                success_threshold=self.config.success_threshold,
            )

            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        else:
            # Reset failure count on success in CLOSED state
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.debug(
            "circuit_breaker.failure",
            name=self.config.name,
            state=self.state.value,
            failure_count=self.failure_count,
            fail_max=self.config.fail_max,
        )

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self._transition_to_open()
        elif self.failure_count >= self.config.fail_max:
            self._transition_to_open()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        return (time.time() - self.last_failure_time) >= self.config.timeout_duration

    def _transition_to_open(self) -> None:
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.success_count = 0
        logger.warning(
            "circuit_breaker.opened",
            name=self.config.name,
            failure_count=self.failure_count,
            fail_max=self.config.fail_max,
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info(
            "circuit_breaker.half_opened",
            name=self.config.name,
            timeout_duration=self.config.timeout_duration,
        )

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(
            "circuit_breaker.closed",
            name=self.config.name,
            success_count=self.success_count,
        )

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("circuit_breaker.reset", name=self.config.name)

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


class CircuitBreakerWrapper:
    """
    Convenience wrapper for circuit breaker decorator

    Provides easy integration with existing functions.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker wrapper

        Args:
            config: Circuit breaker configuration
        """
        self.circuit_breaker = CircuitBreaker(config)

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to wrap function with circuit breaker

        Args:
            func: Function to wrap

        Returns:
            Wrapped function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.circuit_breaker.call(func, *args, **kwargs)

        return wrapper

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result
        """
        return self.circuit_breaker.call(func, *args, **kwargs)

    def reset(self) -> None:
        """Reset the circuit breaker"""
        self.circuit_breaker.reset()

    def get_state(self) -> CircuitState:
        """Get current state"""
        return self.circuit_breaker.get_state()

    def get_stats(self) -> dict:
        """Get statistics"""
        return self.circuit_breaker.get_stats()
