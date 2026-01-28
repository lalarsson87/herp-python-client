"""
Tests for rate limiter
"""

import time
from unittest.mock import Mock, patch

import pytest

from src.core.herp.rate_limiter import AdaptiveRateLimiter, AsyncRateLimiter


class TestAdaptiveRateLimiter:
    """Test AdaptiveRateLimiter"""

    def test_initialization(self):
        """Test rate limiter initialization"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        assert limiter.requests_per_minute == 100
        assert limiter.min_delay == 0.6  # 60/100
        assert len(limiter._request_times) == 0

    def test_initialization_with_rps(self):
        """Test rate limiter with requests per second"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100, requests_per_second=5)

        # Should use the more restrictive limit (1/5 = 0.2s > 60/100 = 0.6s)
        assert limiter.min_delay == 0.6

    @patch("time.sleep")
    @patch("time.time")
    def test_acquire_enforces_min_delay(self, mock_time, mock_sleep):
        """Test that acquire enforces minimum delay"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # First request at t=0
        mock_time.return_value = 0.0
        limiter.acquire()

        # Second request at t=0.3 (less than min_delay of 0.6)
        mock_time.return_value = 0.3
        limiter.acquire()

        # Should sleep for 0.3 seconds to reach min_delay
        mock_sleep.assert_called_with(pytest.approx(0.3, abs=0.01))

    @patch("time.sleep")
    @patch("time.time")
    def test_acquire_no_sleep_when_enough_time_passed(self, mock_time, mock_sleep):
        """Test that acquire doesn't sleep if enough time has passed"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # First request at t=0
        mock_time.return_value = 0.0
        limiter.acquire()

        # Second request at t=1.0 (more than min_delay)
        mock_time.return_value = 1.0
        limiter.acquire()

        # Should not call sleep
        assert mock_sleep.call_count == 0

    def test_update_from_headers(self):
        """Test updating from response headers"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # Test with remaining requests header
        headers = {"x-remaining-request": "50"}
        limiter.update_from_headers(headers)  # Should not raise

        # Test with rate limit reset header
        headers = {"x-ratelimit-reset": str(int(time.time()) + 60)}
        limiter.update_from_headers(headers)  # Should not raise

        # Test with both headers
        headers = {
            "x-remaining-request": "10",
            "x-ratelimit-reset": str(int(time.time()) + 60),
        }
        limiter.update_from_headers(headers)  # Should not raise

    def test_reset(self):
        """Test resetting rate limiter"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # Make a few requests
        with patch("time.sleep"):
            limiter.acquire()
            limiter.acquire()

        assert len(limiter._request_times) > 0

        # Reset should clear state
        limiter.reset()
        assert len(limiter._request_times) == 0
        assert limiter._last_request_time is None

    def test_get_stats(self):
        """Test getting rate limiter statistics"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # Make some requests
        with patch("time.sleep"):
            limiter.acquire()
            limiter.acquire()

        stats = limiter.get_stats()

        assert "requests_per_minute" in stats
        assert "recent_requests" in stats
        assert stats["requests_per_minute"] == 100
        assert stats["recent_requests"] == 2


@pytest.mark.asyncio
class TestAsyncRateLimiter:
    """Test AsyncRateLimiter"""

    async def test_initialization(self):
        """Test async rate limiter initialization"""
        limiter = AsyncRateLimiter(requests_per_minute=100)

        assert limiter.requests_per_minute == 100
        assert limiter.min_delay == 0.6  # 60/100

    @patch("asyncio.sleep")
    @patch("time.time")
    async def test_acquire_enforces_min_delay(self, mock_time, mock_sleep):
        """Test that async acquire enforces minimum delay"""
        limiter = AsyncRateLimiter(requests_per_minute=100)

        # Make async sleep a coroutine
        async def async_sleep_mock(duration):
            pass

        mock_sleep.side_effect = async_sleep_mock

        # First request at t=0
        mock_time.return_value = 0.0
        await limiter.acquire()

        # Second request at t=0.3 (less than min_delay of 0.6)
        mock_time.return_value = 0.3
        await limiter.acquire()

        # Should call async sleep
        assert mock_sleep.call_count > 0

    async def test_update_from_headers(self):
        """Test updating from headers"""
        limiter = AsyncRateLimiter(requests_per_minute=100)

        # Update with remaining requests header
        headers = {"x-remaining-request": "50"}
        limiter.update_from_headers(headers)

        # Should not raise any errors

    async def test_reset(self):
        """Test resetting async rate limiter"""
        limiter = AsyncRateLimiter(requests_per_minute=100)

        # Make some requests
        with patch("asyncio.sleep"):
            await limiter.acquire()
            await limiter.acquire()

        assert len(limiter._request_times) > 0

        # Reset should clear state
        limiter.reset()
        assert len(limiter._request_times) == 0
        assert limiter._last_request_time is None


class TestRateLimiterEdgeCases:
    """Test edge cases for rate limiters"""

    def test_very_high_rate_limit(self):
        """Test with very high rate limit"""
        limiter = AdaptiveRateLimiter(requests_per_minute=10000)

        # Should have very small min_delay
        assert limiter.min_delay == 0.006

    def test_very_low_rate_limit(self):
        """Test with very low rate limit"""
        limiter = AdaptiveRateLimiter(requests_per_minute=1)

        # Should have 60 second min_delay
        assert limiter.min_delay == 60.0

    def test_invalid_headers(self):
        """Test handling of invalid response headers"""
        limiter = AdaptiveRateLimiter(requests_per_minute=100)

        # Should not crash with invalid values
        headers = {"x-remaining-request": "invalid"}
        limiter.update_from_headers(headers)

        headers = {"x-ratelimit-reset": "not_a_number"}
        limiter.update_from_headers(headers)

        # Empty headers should work
        limiter.update_from_headers({})
