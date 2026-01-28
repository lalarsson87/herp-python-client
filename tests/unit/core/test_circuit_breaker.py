"""
Tests for async circuit breaker
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from src.core.circuit_breaker import (
    AsyncCircuitBreaker,
    AsyncCircuitBreakerWrapper,
    CircuitBreakerConfig,
    CircuitState,
)
from src.core.errors.exceptions import CircuitBreakerOpenError


@pytest.fixture
def config():
    """Create test circuit breaker configuration"""
    return CircuitBreakerConfig(
        name="test_breaker",
        fail_max=3,
        success_threshold=2,
        timeout_duration=1.0,
    )


@pytest.mark.asyncio
class TestAsyncCircuitBreaker:
    """Test AsyncCircuitBreaker"""

    async def test_initialization(self, config):
        """Test circuit breaker initialization"""
        breaker = AsyncCircuitBreaker(config)

        assert breaker.config == config
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.last_failure_time is None

    async def test_successful_call_in_closed_state(self, config):
        """Test successful function call in CLOSED state"""
        breaker = AsyncCircuitBreaker(config)

        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    async def test_failed_call_below_threshold(self, config):
        """Test failed calls below threshold keep circuit closed"""
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # First failure
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1

        # Second failure
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 2

    async def test_circuit_opens_after_threshold(self, config):
        """Test circuit opens after failure threshold is reached"""
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Reach threshold (3 failures)
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    async def test_open_circuit_rejects_calls(self, config):
        """Test OPEN circuit rejects calls immediately"""
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected immediately
        async def never_called():
            pytest.fail("Function should not be called when circuit is open")

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(never_called)

    async def test_half_open_after_timeout(self, config):
        """Test circuit transitions to HALF_OPEN after timeout"""
        config.timeout_duration = 0.1  # Short timeout for testing
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next call should transition to HALF_OPEN
        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.success_count == 1

    async def test_half_open_closes_after_success_threshold(self, config):
        """Test HALF_OPEN transitions to CLOSED after success threshold"""
        config.timeout_duration = 0.1
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Make successful calls to close circuit
        async def success_func():
            return "success"

        # First success (still HALF_OPEN)
        await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success (should close)
        await breaker.call(success_func)
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    async def test_half_open_reopens_on_failure(self, config):
        """Test HALF_OPEN immediately reopens on any failure"""
        config.timeout_duration = 0.1
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout and transition to HALF_OPEN
        await asyncio.sleep(0.15)

        async def success_func():
            return "success"

        await breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Failure should immediately reopen circuit
        with pytest.raises(ValueError):
            await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

    async def test_manual_reset(self, config):
        """Test manual reset of circuit breaker"""
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Manual reset
        await breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.last_failure_time is None

    async def test_get_state(self, config):
        """Test getting current state"""
        breaker = AsyncCircuitBreaker(config)

        assert breaker.get_state() == CircuitState.CLOSED

        async def fail_func():
            raise ValueError("test error")

        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.get_state() == CircuitState.OPEN

    async def test_get_stats(self, config):
        """Test getting circuit breaker statistics"""
        breaker = AsyncCircuitBreaker(config)

        stats = breaker.get_stats()

        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
        assert stats["config"]["name"] == "test_breaker"
        assert stats["config"]["fail_max"] == 3
        assert stats["config"]["success_threshold"] == 2
        assert stats["config"]["timeout_duration"] == 1.0

    async def test_success_resets_failure_count_in_closed_state(self, config):
        """Test success resets failure count in CLOSED state"""
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Two failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.failure_count == 2

        # Success should reset failure count
        await breaker.call(success_func)

        assert breaker.failure_count == 0
        assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
class TestAsyncCircuitBreakerWrapper:
    """Test AsyncCircuitBreakerWrapper"""

    async def test_wrapper_initialization(self, config):
        """Test wrapper initialization"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        assert wrapper.circuit_breaker is not None
        assert wrapper.get_state() == CircuitState.CLOSED

    async def test_decorator_usage(self, config):
        """Test using wrapper as decorator"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        @wrapper
        async def test_func(value):
            return value * 2

        result = await test_func(5)
        assert result == 10

    async def test_decorator_with_failures(self, config):
        """Test decorator handles failures"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        @wrapper
        async def fail_func():
            raise ValueError("test error")

        # Open circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await fail_func()

        assert wrapper.get_state() == CircuitState.OPEN

        # Next call rejected
        with pytest.raises(CircuitBreakerOpenError):
            await fail_func()

    async def test_wrapper_call_method(self, config):
        """Test wrapper call method"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        async def test_func(x, y):
            return x + y

        result = await wrapper.call(test_func, 3, 4)
        assert result == 7

    async def test_wrapper_reset(self, config):
        """Test wrapper reset"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        async def fail_func():
            raise ValueError("test error")

        # Open circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await wrapper.call(fail_func)

        assert wrapper.get_state() == CircuitState.OPEN

        # Reset
        await wrapper.reset()

        assert wrapper.get_state() == CircuitState.CLOSED

    async def test_wrapper_get_stats(self, config):
        """Test wrapper get_stats"""
        wrapper = AsyncCircuitBreakerWrapper(config)

        stats = wrapper.get_stats()

        assert "state" in stats
        assert "failure_count" in stats
        assert "config" in stats


@pytest.mark.asyncio
class TestCircuitBreakerEdgeCases:
    """Test edge cases for circuit breaker"""

    async def test_concurrent_calls(self, config):
        """Test circuit breaker with concurrent calls"""
        breaker = AsyncCircuitBreaker(config)
        call_count = [0]

        async def slow_func():
            call_count[0] += 1
            await asyncio.sleep(0.01)
            return "success"

        # Make concurrent calls
        tasks = [breaker.call(slow_func) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r == "success" for r in results)
        assert call_count[0] == 5

    async def test_exception_preservation(self, config):
        """Test that exceptions are preserved correctly"""
        breaker = AsyncCircuitBreaker(config)

        class CustomError(Exception):
            pass

        async def custom_fail():
            raise CustomError("custom message")

        # Exception should be preserved
        with pytest.raises(CustomError, match="custom message"):
            await breaker.call(custom_fail)

    async def test_zero_timeout_duration(self):
        """Test circuit breaker with zero timeout"""
        config = CircuitBreakerConfig(
            name="zero_timeout",
            fail_max=2,
            success_threshold=1,
            timeout_duration=0.0,
        )
        breaker = AsyncCircuitBreaker(config)

        async def fail_func():
            raise ValueError("error")

        # Open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Should immediately be able to attempt recovery
        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
