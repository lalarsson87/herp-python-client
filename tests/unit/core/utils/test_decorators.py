"""
Tests for utility decorators (retry logic)
"""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest

from src.core.errors.exceptions import (
    HerpAPIError,
    HerpRateLimitError,
    TransientError,
)
from src.core.utils.decorators import async_smart_retry, smart_retry


class TestSmartRetry:
    """Test synchronous smart_retry decorator"""

    def test_successful_call_no_retry(self):
        """Test successful call doesn't retry"""
        call_count = [0]

        @smart_retry(max_attempts=3)
        def success_func():
            call_count[0] += 1
            return "success"

        result = success_func()

        assert result == "success"
        assert call_count[0] == 1

    @patch("time.sleep")
    def test_retry_on_transient_error(self, mock_sleep):
        """Test retry on transient error"""
        call_count = [0]

        @smart_retry(max_attempts=3, base_delay=1.0)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise TransientError("temporary error")
            return "success"

        result = flaky_func()

        assert result == "success"
        assert call_count[0] == 3
        assert mock_sleep.call_count == 2  # Two retries

    @patch("time.sleep")
    def test_max_attempts_reached(self, mock_sleep):
        """Test raises exception after max attempts"""
        call_count = [0]

        @smart_retry(max_attempts=3)
        def always_fail():
            call_count[0] += 1
            raise TransientError("always fails")

        with pytest.raises(TransientError):
            always_fail()

        assert call_count[0] == 3
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff delays"""

        @smart_retry(max_attempts=4, base_delay=1.0, exponential_backoff=True)
        def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            fail_func()

        # Check delays: 1s, 2s, 4s
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("time.sleep")
    def test_linear_backoff(self, mock_sleep):
        """Test linear backoff (no exponential)"""

        @smart_retry(max_attempts=4, base_delay=2.0, exponential_backoff=False)
        def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            fail_func()

        # Check delays are constant
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [2.0, 2.0, 2.0]

    @patch("time.sleep")
    def test_max_delay_cap(self, mock_sleep):
        """Test max_delay caps exponential backoff"""

        @smart_retry(max_attempts=5, base_delay=2.0, max_delay=5.0)
        def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            fail_func()

        # Check delays are capped at max_delay
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        # 2, 4, 5 (capped), 5 (capped)
        assert delays == [2.0, 4.0, 5.0, 5.0]

    @patch("time.sleep")
    def test_rate_limit_error_longer_delay(self, mock_sleep):
        """Test rate limit errors get longer delay"""

        @smart_retry(max_attempts=2, base_delay=1.0)
        def rate_limited():
            raise HerpRateLimitError("rate limited")

        with pytest.raises(HerpRateLimitError):
            rate_limited()

        # Delay should be at least 5.0 for rate limit
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] >= 5.0

    def test_custom_retry_exceptions(self):
        """Test custom retryable exceptions"""
        call_count = [0]

        @smart_retry(max_attempts=3, retry_on=(ValueError,))
        def custom_error():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("custom error")
            return "success"

        result = custom_error()
        assert result == "success"
        assert call_count[0] == 2

    def test_non_retryable_exception_raises_immediately(self):
        """Test non-retryable exceptions raise immediately"""
        call_count = [0]

        @smart_retry(max_attempts=3, retry_on=(TransientError,))
        def non_retryable_error():
            call_count[0] += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            non_retryable_error()

        # Should fail immediately without retry
        assert call_count[0] == 1

    @patch("time.sleep")
    def test_retryable_exceptions_alias(self, mock_sleep):
        """Test retryable_exceptions parameter (backward compatibility)"""
        call_count = [0]

        @smart_retry(max_attempts=2, retryable_exceptions=(ValueError,))
        def func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("error")
            return "success"

        result = func()
        assert result == "success"
        assert call_count[0] == 2


@pytest.mark.asyncio
class TestAsyncSmartRetry:
    """Test asynchronous async_smart_retry decorator"""

    async def test_successful_call_no_retry(self):
        """Test successful async call doesn't retry"""
        call_count = [0]

        @async_smart_retry(max_attempts=3)
        async def success_func():
            call_count[0] += 1
            return "success"

        result = await success_func()

        assert result == "success"
        assert call_count[0] == 1

    @patch("asyncio.sleep")
    async def test_retry_on_transient_error(self, mock_sleep):
        """Test retry on transient error"""
        call_count = [0]

        # Make asyncio.sleep a coroutine
        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=3, base_delay=1.0)
        async def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise TransientError("temporary error")
            return "success"

        result = await flaky_func()

        assert result == "success"
        assert call_count[0] == 3
        assert mock_sleep.call_count == 2

    @patch("asyncio.sleep")
    async def test_max_attempts_reached(self, mock_sleep):
        """Test raises exception after max attempts"""
        call_count = [0]

        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=3)
        async def always_fail():
            call_count[0] += 1
            raise TransientError("always fails")

        with pytest.raises(TransientError):
            await always_fail()

        assert call_count[0] == 3
        assert mock_sleep.call_count == 2

    @patch("asyncio.sleep")
    async def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff delays"""

        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=4, base_delay=1.0, exponential_backoff=True)
        async def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            await fail_func()

        # Check delays: 1s, 2s, 4s
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("asyncio.sleep")
    async def test_linear_backoff(self, mock_sleep):
        """Test linear backoff (no exponential)"""

        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=4, base_delay=2.0, exponential_backoff=False)
        async def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            await fail_func()

        # Check delays are constant
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [2.0, 2.0, 2.0]

    @patch("asyncio.sleep")
    async def test_max_delay_cap(self, mock_sleep):
        """Test max_delay caps exponential backoff"""

        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=5, base_delay=2.0, max_delay=5.0)
        async def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            await fail_func()

        # Check delays are capped at max_delay
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [2.0, 4.0, 5.0, 5.0]

    @patch("asyncio.sleep")
    async def test_rate_limit_error_longer_delay(self, mock_sleep):
        """Test rate limit errors get longer delay"""

        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        @async_smart_retry(max_attempts=2, base_delay=1.0)
        async def rate_limited():
            raise HerpRateLimitError("rate limited")

        with pytest.raises(HerpRateLimitError):
            await rate_limited()

        # Delay should be at least 5.0 for rate limit
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays[0] >= 5.0

    async def test_custom_retry_exceptions(self):
        """Test custom retryable exceptions"""
        call_count = [0]

        @async_smart_retry(max_attempts=3, retry_on=(ValueError,))
        async def custom_error():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("custom error")
            return "success"

        result = await custom_error()
        assert result == "success"
        assert call_count[0] == 2

    async def test_non_retryable_exception_raises_immediately(self):
        """Test non-retryable exceptions raise immediately"""
        call_count = [0]

        @async_smart_retry(max_attempts=3, retry_on=(TransientError,))
        async def non_retryable_error():
            call_count[0] += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            await non_retryable_error()

        # Should fail immediately without retry
        assert call_count[0] == 1

    async def test_preserves_function_metadata(self):
        """Test decorator preserves function metadata"""

        @async_smart_retry()
        async def documented_func():
            """This is a docstring"""
            pass

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring"


class TestRetryEdgeCases:
    """Test edge cases for retry decorators"""

    @patch("time.sleep")
    def test_single_attempt(self, mock_sleep):
        """Test max_attempts=1 doesn't retry"""
        call_count = [0]

        @smart_retry(max_attempts=1)
        def fail_once():
            call_count[0] += 1
            raise TransientError("error")

        with pytest.raises(TransientError):
            fail_once()

        assert call_count[0] == 1
        assert mock_sleep.call_count == 0

    def test_function_with_arguments(self):
        """Test retry works with function arguments"""

        @smart_retry(max_attempts=2)
        def add(a, b):
            return a + b

        result = add(3, 4)
        assert result == 7

    def test_function_with_kwargs(self):
        """Test retry works with keyword arguments"""

        @smart_retry(max_attempts=2)
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = greet("World", greeting="Hi")
        assert result == "Hi, World!"

    @patch("time.sleep")
    def test_zero_base_delay(self, mock_sleep):
        """Test retry with zero base delay"""

        @smart_retry(max_attempts=3, base_delay=0.0)
        def fail_func():
            raise TransientError("error")

        with pytest.raises(TransientError):
            fail_func()

        # Delays should be 0
        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert all(d == 0.0 for d in delays)
