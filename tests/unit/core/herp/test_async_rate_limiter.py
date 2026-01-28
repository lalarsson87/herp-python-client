"""
Tests for Async HERP Rate Limiter
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.core.herp.async_rate_limiter import (
    AsyncAdaptiveRateLimiter,
    AsyncHerpRateLimiter,
    get_async_rate_limiter,
    reset_async_rate_limiter,
)


class TestAsyncHerpRateLimiterInitialization:
    """Test AsyncHerpRateLimiter initialization"""

    def test_initialization_default(self):
        """Test default initialization"""
        limiter = AsyncHerpRateLimiter()

        assert limiter.requests_per_minute == 100
        assert limiter.burst_size == 100
        assert limiter.min_interval == 0.6  # 60 / 100
        assert limiter.tokens == 100.0
        assert len(limiter.request_history) == 0

    def test_initialization_custom_rate(self):
        """Test initialization with custom rate"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=60)

        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 60
        assert limiter.min_interval == 1.0  # 60 / 60

    def test_initialization_custom_burst(self):
        """Test initialization with custom burst size"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=100, burst_size=50)

        assert limiter.requests_per_minute == 100
        assert limiter.burst_size == 50
        assert limiter.tokens == 50.0

    def test_initialization_creates_lock(self):
        """Test initialization creates async lock"""
        limiter = AsyncHerpRateLimiter()

        assert isinstance(limiter.lock, asyncio.Lock)


class TestAsyncHerpRateLimiterAcquire:
    """Test async acquire method"""

    @pytest.mark.asyncio
    async def test_acquire_single_request(self):
        """Test acquiring single token"""
        limiter = AsyncHerpRateLimiter()

        result = await limiter.acquire()

        assert result is True
        assert limiter.tokens == 99.0
        assert len(limiter.request_history) == 1

    @pytest.mark.asyncio
    async def test_acquire_multiple_requests(self):
        """Test acquiring multiple tokens"""
        limiter = AsyncHerpRateLimiter(burst_size=10)

        results = []
        for _ in range(5):
            result = await limiter.acquire()
            results.append(result)

        assert all(results)
        assert limiter.tokens == 5.0
        assert len(limiter.request_history) == 5

    @pytest.mark.asyncio
    async def test_acquire_exhausts_tokens(self):
        """Test acquiring all available tokens"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=10, burst_size=5)

        # Acquire all 5 tokens
        for _ in range(5):
            await limiter.acquire()

        assert limiter.tokens == 0.0

    @pytest.mark.asyncio
    async def test_acquire_with_timeout_succeeds(self):
        """Test acquire with timeout when tokens available"""
        limiter = AsyncHerpRateLimiter()

        result = await limiter.acquire(timeout=1.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_with_timeout_fails(self):
        """Test acquire with timeout when no tokens"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=10, burst_size=1)

        # Exhaust tokens
        await limiter.acquire()

        # Try to acquire with short timeout (should fail)
        result = await limiter.acquire(timeout=0.1)

        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_refills_tokens(self):
        """Test tokens refill over time"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=120, burst_size=2)

        # Exhaust tokens
        await limiter.acquire()
        await limiter.acquire()
        assert limiter.tokens == 0.0

        # Wait for token refill (120 req/min = 2 req/sec = 0.5s per token)
        await asyncio.sleep(0.6)

        # Should have refilled at least 1 token
        result = await limiter.acquire()
        assert result is True


class TestAsyncHerpRateLimiterWait:
    """Test wait method"""

    @pytest.mark.asyncio
    async def test_wait_acquires_token(self):
        """Test wait acquires token"""
        limiter = AsyncHerpRateLimiter()

        await limiter.wait()

        assert limiter.tokens == 99.0
        assert len(limiter.request_history) == 1

    @pytest.mark.asyncio
    async def test_wait_blocks_until_available(self):
        """Test wait blocks until token available"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=120, burst_size=1)

        # Exhaust tokens
        await limiter.acquire()

        start_time = time.time()

        # Wait for token (should block briefly)
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Simulate token refill
            limiter.tokens = 1.0
            await limiter.wait()

        # Should have called sleep
        assert mock_sleep.called or limiter.tokens < 1.0


class TestAsyncHerpRateLimiterStats:
    """Test statistics methods"""

    @pytest.mark.asyncio
    async def test_get_current_rate_no_requests(self):
        """Test get_current_rate with no requests"""
        limiter = AsyncHerpRateLimiter()

        rate = limiter.get_current_rate()

        assert rate == 0.0

    @pytest.mark.asyncio
    async def test_get_current_rate_with_requests(self):
        """Test get_current_rate with recent requests"""
        limiter = AsyncHerpRateLimiter()

        # Make several requests
        for _ in range(5):
            await limiter.acquire()

        rate = limiter.get_current_rate()

        assert rate == 5.0

    @pytest.mark.asyncio
    async def test_get_available_tokens(self):
        """Test get_available_tokens"""
        limiter = AsyncHerpRateLimiter(burst_size=10)

        # Acquire some tokens
        await limiter.acquire()
        await limiter.acquire()

        available = await limiter.get_available_tokens()

        assert available == 8.0

    @pytest.mark.asyncio
    async def test_get_available_tokens_refills(self):
        """Test get_available_tokens triggers refill"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=120, burst_size=10)

        # Exhaust some tokens
        for _ in range(5):
            await limiter.acquire()

        # Wait for refill
        await asyncio.sleep(0.6)

        # Get available should refill
        available = await limiter.get_available_tokens()

        # Should have refilled at least 1 token
        assert available > 5.0


class TestAsyncHerpRateLimiterReset:
    """Test reset method"""

    @pytest.mark.asyncio
    async def test_reset_restores_tokens(self):
        """Test reset restores tokens to burst size"""
        limiter = AsyncHerpRateLimiter(burst_size=10)

        # Exhaust tokens
        for _ in range(5):
            await limiter.acquire()

        assert limiter.tokens == 5.0

        # Reset
        await limiter.reset()

        assert limiter.tokens == 10.0

    @pytest.mark.asyncio
    async def test_reset_clears_history(self):
        """Test reset clears request history"""
        limiter = AsyncHerpRateLimiter()

        # Make requests
        for _ in range(5):
            await limiter.acquire()

        assert len(limiter.request_history) == 5

        # Reset
        await limiter.reset()

        assert len(limiter.request_history) == 0


class TestAsyncHerpRateLimiterContextManager:
    """Test async context manager"""

    @pytest.mark.asyncio
    async def test_context_manager_acquires(self):
        """Test context manager acquires token on entry"""
        limiter = AsyncHerpRateLimiter()

        async with limiter:
            # Should have acquired token
            assert limiter.tokens == 99.0

    @pytest.mark.asyncio
    async def test_context_manager_multiple(self):
        """Test multiple context manager uses"""
        limiter = AsyncHerpRateLimiter()

        async with limiter:
            pass

        async with limiter:
            pass

        # Should have acquired twice
        assert limiter.tokens == 98.0


class TestAsyncAdaptiveRateLimiterInitialization:
    """Test AsyncAdaptiveRateLimiter initialization"""

    def test_initialization_default(self):
        """Test default initialization"""
        limiter = AsyncAdaptiveRateLimiter()

        assert limiter.requests_per_minute == 100
        assert limiter.safety_margin == 0.9
        assert limiter.api_remaining is None

    def test_initialization_custom_safety_margin(self):
        """Test initialization with custom safety margin"""
        limiter = AsyncAdaptiveRateLimiter(safety_margin=0.8)

        assert limiter.safety_margin == 0.8


class TestAsyncAdaptiveRateLimiterHeaderUpdates:
    """Test update_from_response_headers"""

    def test_update_from_headers_normal(self):
        """Test updating from headers with normal remaining count"""
        limiter = AsyncAdaptiveRateLimiter()

        headers = {"x-remaining-request": "50"}
        limiter.update_from_response_headers(headers)

        assert limiter.api_remaining == 50

    def test_update_from_headers_low_remaining(self):
        """Test updating from headers with low remaining count"""
        limiter = AsyncAdaptiveRateLimiter()
        limiter.tokens = 50.0

        headers = {"x-remaining-request": "5"}
        limiter.update_from_response_headers(headers)

        assert limiter.api_remaining == 5
        # Should reduce tokens significantly
        assert limiter.tokens < 50.0

    def test_update_from_headers_very_low(self):
        """Test updating from headers with very low remaining"""
        limiter = AsyncAdaptiveRateLimiter()
        limiter.tokens = 50.0

        headers = {"x-remaining-request": "2"}
        limiter.update_from_response_headers(headers)

        assert limiter.api_remaining == 2
        # Should reduce tokens more aggressively
        assert limiter.tokens <= 1.0  # 2 * 0.5

    def test_update_from_headers_missing(self):
        """Test updating when header is missing"""
        limiter = AsyncAdaptiveRateLimiter()

        headers = {}
        limiter.update_from_response_headers(headers)

        # Should not change api_remaining
        assert limiter.api_remaining is None

    def test_update_from_headers_invalid(self):
        """Test updating with invalid header value"""
        limiter = AsyncAdaptiveRateLimiter()

        headers = {"x-remaining-request": "invalid"}
        limiter.update_from_response_headers(headers)

        # Should not change api_remaining
        assert limiter.api_remaining is None


class TestAsyncAdaptiveRateLimiterAcquire:
    """Test adaptive acquire behavior"""

    @pytest.mark.asyncio
    async def test_acquire_when_api_remaining_zero(self):
        """Test acquire when API remaining is zero"""
        limiter = AsyncAdaptiveRateLimiter()
        limiter.api_remaining = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Short timeout should fail
            result = await limiter.acquire(timeout=1.0)

            assert result is False
            # Should not sleep since timeout < 60
            assert not mock_sleep.called

    @pytest.mark.asyncio
    async def test_acquire_waits_when_at_limit(self):
        """Test acquire waits when at rate limit"""
        limiter = AsyncAdaptiveRateLimiter()
        limiter.api_remaining = 0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # After sleep, simulate tokens being available
            async def sleep_side_effect(duration):
                if duration >= 60.0:
                    limiter.tokens = 10.0

            mock_sleep.side_effect = sleep_side_effect

            result = await limiter.acquire(timeout=100.0)

            # Should have slept for rate limit reset
            mock_sleep.assert_called()
            assert result is True


class TestGlobalAsyncRateLimiter:
    """Test global rate limiter functions"""

    @pytest.mark.asyncio
    async def test_get_async_rate_limiter_creates(self):
        """Test get_async_rate_limiter creates limiter"""
        await reset_async_rate_limiter()

        limiter = await get_async_rate_limiter()

        assert isinstance(limiter, AsyncAdaptiveRateLimiter)

    @pytest.mark.asyncio
    async def test_get_async_rate_limiter_returns_same(self):
        """Test get_async_rate_limiter returns same instance"""
        await reset_async_rate_limiter()

        limiter1 = await get_async_rate_limiter()
        limiter2 = await get_async_rate_limiter()

        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_get_async_rate_limiter_non_adaptive(self):
        """Test get_async_rate_limiter with adaptive=False"""
        await reset_async_rate_limiter()

        limiter = await get_async_rate_limiter(adaptive=False)

        assert isinstance(limiter, AsyncHerpRateLimiter)
        assert not isinstance(limiter, AsyncAdaptiveRateLimiter)

    @pytest.mark.asyncio
    async def test_reset_async_rate_limiter(self):
        """Test reset_async_rate_limiter clears global"""
        limiter1 = await get_async_rate_limiter()

        await reset_async_rate_limiter()

        limiter2 = await get_async_rate_limiter()

        # Should be different instances
        assert limiter1 is not limiter2


class TestAsyncRateLimiterEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_concurrent_acquires(self):
        """Test concurrent acquire calls"""
        limiter = AsyncHerpRateLimiter(burst_size=10)

        # Create multiple concurrent acquire tasks
        tasks = [limiter.acquire() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(results)
        # Should have consumed 5 tokens
        assert limiter.tokens == 5.0

    @pytest.mark.asyncio
    async def test_request_history_max_length(self):
        """Test request history has max length"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=10)

        # Make more requests than max length
        for _ in range(20):
            await limiter.acquire()
            limiter.tokens += 1.0  # Refill manually to avoid blocking

        # History should be limited to requests_per_minute
        assert len(limiter.request_history) == 10

    @pytest.mark.asyncio
    async def test_token_refill_calculation(self):
        """Test token refill calculation"""
        limiter = AsyncHerpRateLimiter(requests_per_minute=60, burst_size=10)

        # Exhaust all tokens
        for _ in range(10):
            await limiter.acquire()

        # Manually advance time by 10 seconds
        with patch("time.time") as mock_time:
            original_time = limiter.last_refill
            mock_time.return_value = original_time + 10.0

            # Trigger refill
            limiter._refill_tokens()

            # Should have refilled 10 tokens (60 per minute = 1 per second * 10 seconds)
            assert limiter.tokens == 10.0

    def test_adaptive_limiter_inherits_base(self):
        """Test AsyncAdaptiveRateLimiter inherits from base"""
        limiter = AsyncAdaptiveRateLimiter()

        assert isinstance(limiter, AsyncHerpRateLimiter)

    @pytest.mark.asyncio
    async def test_zero_timeout_behavior(self):
        """Test acquire with zero timeout"""
        limiter = AsyncHerpRateLimiter()

        result = await limiter.acquire(timeout=0)

        # Should succeed immediately if tokens available
        assert result is True
