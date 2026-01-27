#!/usr/bin/env python3
"""
HERP Base API Client

Core HTTP client with authentication, rate limiting, and metrics.
Used as base for all specialized API clients.
"""

import time
from typing import Any, Dict, Optional

import requests

from ..cache import CacheManager
from ..errors.exceptions import (
    HerpAPIError,
    HerpAuthenticationError,
    HerpRateLimitError,
)
from ..observability.metrics import MetricsCollector, get_metrics_collector
from ..utils.circuit_breaker import CircuitBreakerConfig, CircuitBreakerWrapper
from ..utils.config import HerpConfig
from ..utils.logging import get_logger
from .rate_limiter import AdaptiveRateLimiter

logger = get_logger(__name__)


class HerpBaseClient:
    """
    Base HERP API Client

    Provides core HTTP methods with authentication, rate limiting,
    retries, and observability. Used as base for specialized clients.
    """

    def __init__(
        self,
        config: HerpConfig,
        cache_manager: Optional[CacheManager] = None,
        enable_circuit_breaker: bool = False,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize base HERP client

        Args:
            config: HERP configuration object
            cache_manager: Optional cache manager for response caching
            enable_circuit_breaker: Enable circuit breaker pattern (default: False)
            circuit_breaker_config: Circuit breaker configuration
            metrics_collector: Optional metrics collector
        """
        self.config = config
        self.base_url = config.base_url
        self.cache_manager = cache_manager
        self.rate_limiter = AdaptiveRateLimiter(requests_per_minute=config.rate_limit)
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

        # Metrics collector (mandatory - uses global if not provided)
        self.metrics = metrics_collector or get_metrics_collector()
        logger.debug("Metrics collection enabled for HERP API")

        # Circuit breaker (optional)
        self.circuit_breaker = None
        if enable_circuit_breaker:
            cb_config = circuit_breaker_config or CircuitBreakerConfig(
                name="herp-api", fail_max=5, timeout_duration=60
            )
            self.circuit_breaker = CircuitBreakerWrapper(cb_config)
            logger.info(f"Circuit breaker enabled for HERP API: {cb_config}")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request_impl(
        self, method: str, endpoint: str, **kwargs
    ) -> requests.Response:
        """
        Internal implementation of HTTP request with rate limiting and error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            HerpAPIError: On API errors
            HerpRateLimitError: On rate limit errors
            HerpAuthenticationError: On authentication errors
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = f"{self.base_url}{endpoint}"

        # Acquire rate limit token
        self.rate_limiter.acquire()

        # Make request and record metrics
        start_time = time.time()

        try:
            response = self.session.request(method, url, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Update rate limiter from response headers
            self.rate_limiter.update_from_headers(response.headers)

            # Log the request
            logger.debug(
                f"{method} {endpoint} -> {response.status_code} ({duration_ms:.0f}ms)"
            )

            # Record metrics (always, regardless of success/failure)
            self.metrics.increment(
                "herp.api.requests",
                tags={"method": method, "endpoint": endpoint, "status": str(response.status_code)}
            )
            self.metrics.timing(
                "herp.api.duration",
                duration_ms,
                tags={"method": method, "endpoint": endpoint}
            )

            # Handle errors
            if response.status_code == 429:
                raise HerpRateLimitError("Rate limit exceeded")
            elif response.status_code == 401:
                raise HerpAuthenticationError("Authentication failed")
            elif response.status_code >= 400:
                raise HerpAPIError(
                    f"API error: {response.status_code} - {response.text}"
                )

            return response

        except (HerpAPIError, HerpRateLimitError, HerpAuthenticationError):
            # Re-raise our own exceptions (already recorded in metrics above)
            raise
        except Exception as e:
            # Record unexpected errors
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.increment(
                "herp.api.errors",
                tags={"method": method, "endpoint": endpoint, "error_type": type(e).__name__}
            )
            self.metrics.timing(
                "herp.api.duration",
                duration_ms,
                tags={"method": method, "endpoint": endpoint}
            )
            raise

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with optional circuit breaker protection

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to base_url)
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            HerpAPIError: On API errors
            HerpRateLimitError: On rate limit errors
            HerpAuthenticationError: On authentication errors
            CircuitBreakerError: When circuit breaker is open
        """
        if self.circuit_breaker:
            # Call through circuit breaker
            return self.circuit_breaker.breaker.call(
                self._make_request_impl, method, endpoint, **kwargs
            )
        else:
            # Direct call without circuit breaker
            return self._make_request_impl(method, endpoint, **kwargs)

    # ========================================================================
    # HTTP Methods
    # ========================================================================

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        GET request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (params, headers, etc.)

        Returns:
            JSON response data
        """
        from ..errors import smart_retry

        @smart_retry(
            max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
        )
        def _get():
            response = self._make_request("GET", endpoint, **kwargs)
            return response.json()

        return _get()

    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        POST request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, headers, etc.)

        Returns:
            JSON response data
        """
        from ..errors import smart_retry

        @smart_retry(
            max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
        )
        def _post():
            response = self._make_request("POST", endpoint, **kwargs)
            return response.json()

        return _post()

    def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        PATCH request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, headers, etc.)

        Returns:
            JSON response data
        """
        from ..errors import smart_retry

        @smart_retry(
            max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
        )
        def _patch():
            response = self._make_request("PATCH", endpoint, **kwargs)
            return response.json()

        return _patch()

    def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        PUT request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, headers, etc.)

        Returns:
            JSON response data
        """
        from ..errors import smart_retry

        @smart_retry(
            max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
        )
        def _put():
            response = self._make_request("PUT", endpoint, **kwargs)
            return response.json()

        return _put()

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        DELETE request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments

        Returns:
            JSON response data
        """
        from ..errors import smart_retry

        @smart_retry(
            max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
        )
        def _delete():
            response = self._make_request("DELETE", endpoint, **kwargs)
            return response.json() if response.content else {}

        return _delete()
