#!/usr/bin/env python3
"""
HERP Async Base Client

Provides async HTTP client with authentication, rate limiting, retry logic,
circuit breaker, and observability.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    import httpx

try:
    import httpx as _httpx

    HTTPX_AVAILABLE = True
    httpx = _httpx
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore

from ..cache.manager import CacheManager
from ..circuit_breaker import AsyncCircuitBreaker, CircuitBreakerConfig
from ..errors.exceptions import (
    HerpAPIError,
    HerpAuthenticationError,
    HerpNotFoundError,
    HerpRateLimitError,
    HerpServerError,
)
from ..metrics.collector import MetricsCollector, get_metrics_collector
from ..utils.config import HerpConfig
from ..utils.decorators import async_smart_retry
from ..utils.logging import get_logger
from .rate_limiter import AsyncRateLimiter

logger = get_logger(__name__)


class AsyncHerpBaseClient:
    """
    Async Base HERP API Client

    Provides async HTTP methods with:
    - Bearer token authentication
    - Adaptive rate limiting
    - Automatic retry with exponential backoff
    - Circuit breaker for fault tolerance
    - Request/response logging
    - Metrics collection

    Usage:
        async with AsyncHerpBaseClient(config) as client:
            data = await client.get("/v1/candidacies")

        # Or manual lifecycle:
        client = AsyncHerpBaseClient(config)
        await client.__aenter__()
        try:
            data = await client.get("/v1/candidacies")
        finally:
            await client.__aexit__(None, None, None)
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
        Initialize async HERP base client

        Args:
            config: HERP configuration
            cache_manager: Optional cache manager for response caching
            enable_circuit_breaker: Whether to enable circuit breaker
            circuit_breaker_config: Circuit breaker configuration
            metrics_collector: Optional metrics collector

        Raises:
            ImportError: If httpx is not installed
        """
        if not HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for async client. Install with: pip install httpx"
            )

        self.config = config
        self.base_url = config.base_url
        self.rate_limiter = AsyncRateLimiter(requests_per_minute=config.rate_limit)
        self.cache_manager = cache_manager
        self.metrics = metrics_collector or get_metrics_collector()

        # Initialize httpx client (will be created in __aenter__)
        self._client: Optional["httpx.AsyncClient"] = None

        # Circuit breaker (optional)
        self.circuit_breaker = None
        if enable_circuit_breaker:
            cb_config = circuit_breaker_config or CircuitBreakerConfig()
            self.circuit_breaker = AsyncCircuitBreaker(
                failure_threshold=cb_config.failure_threshold,
                recovery_timeout=cb_config.recovery_timeout,
                expected_exception=HerpAPIError,
            )

    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=httpx.Timeout(self.config.timeout, connect=10.0),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Authorization": f"Bearer {self.config.api_token}",
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        }

        if self.config.custom_headers:
            headers.update(self.config.custom_headers)

        return headers

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> "httpx.Response":
        """
        Make an async HTTP request with rate limiting and metrics

        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            endpoint: API endpoint (e.g., "/v1/candidacies")
            **kwargs: Additional arguments for httpx request

        Returns:
            httpx.Response object

        Raises:
            HerpAPIError: For API errors
            HerpRateLimitError: For rate limit errors
            HerpAuthenticationError: For authentication errors
            HerpServerError: For server errors
        """
        if not self._client:
            raise RuntimeError(
                "Client not initialized. Use 'async with AsyncHerpBaseClient(...)' "
                "or call await client.__aenter__() first"
            )

        # Wait for rate limiter
        await self.rate_limiter.acquire()

        # Record request metric
        start_time = datetime.now()

        try:
            # Make request
            logger.debug(f"{method} {endpoint}")
            response = await self._client.request(method, endpoint, **kwargs)

            # Update rate limiter with response headers
            if "x-remaining-requests" in response.headers:
                remaining = int(response.headers["x-remaining-requests"])
                self.rate_limiter.update_from_response(remaining)

            # Record success metric
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.record_histogram(
                "herp.api.request.duration",
                duration,
                labels={
                    "method": method,
                    "endpoint": endpoint.split("?")[0],
                    "status": str(response.status_code),
                },
            )

            # Check response status
            if response.status_code == 429:
                retry_after = int(response.headers.get("retry-after", 60))
                error = HerpRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after}s",
                    retry_after=retry_after,
                )
                self.metrics.increment_counter(
                    "herp.api.errors",
                    labels={"type": "rate_limit", "endpoint": endpoint},
                )
                raise error

            if response.status_code == 401:
                error = HerpAuthenticationError("Invalid API token")
                self.metrics.increment_counter(
                    "herp.api.errors",
                    labels={"type": "authentication", "endpoint": endpoint},
                )
                raise error

            if response.status_code == 404:
                error = HerpNotFoundError(f"Resource not found: {endpoint}")
                self.metrics.increment_counter(
                    "herp.api.errors",
                    labels={"type": "not_found", "endpoint": endpoint},
                )
                raise error

            if response.status_code >= 500:
                error = HerpServerError(
                    f"Server error: {response.status_code} - {response.text}"
                )
                self.metrics.increment_counter(
                    "herp.api.errors",
                    labels={"type": "server_error", "endpoint": endpoint},
                )
                raise error

            if response.status_code >= 400:
                error = HerpAPIError(
                    f"API error: {response.status_code} - {response.text}"
                )
                self.metrics.increment_counter(
                    "herp.api.errors",
                    labels={"type": "client_error", "endpoint": endpoint},
                )
                raise error

            return response

        except httpx.RequestError as e:
            # Network errors
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics.record_histogram(
                "herp.api.request.duration",
                duration,
                labels={
                    "method": method,
                    "endpoint": endpoint.split("?")[0],
                    "status": "error",
                },
            )
            self.metrics.increment_counter(
                "herp.api.errors", labels={"type": "network", "endpoint": endpoint}
            )
            raise HerpAPIError(f"Network error: {str(e)}") from e

    @async_smart_retry(
        max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
    )
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Async GET request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (params, headers, etc.)

        Returns:
            Parsed JSON response
        """
        response = await self._make_request("GET", endpoint, **kwargs)
        return response.json()

    @async_smart_retry(
        max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
    )
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Async POST request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, files, etc.)

        Returns:
            Parsed JSON response
        """
        response = await self._make_request("POST", endpoint, **kwargs)
        return response.json()

    @async_smart_retry(
        max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
    )
    async def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Async PATCH request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, etc.)

        Returns:
            Parsed JSON response
        """
        response = await self._make_request("PATCH", endpoint, **kwargs)
        return response.json()

    @async_smart_retry(
        max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
    )
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Async PUT request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments (json, data, etc.)

        Returns:
            Parsed JSON response
        """
        response = await self._make_request("PUT", endpoint, **kwargs)
        return response.json()

    @async_smart_retry(
        max_attempts=3, base_delay=1.0, retryable_exceptions=(HerpAPIError,)
    )
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Async DELETE request

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments

        Returns:
            Parsed JSON response
        """
        response = await self._make_request("DELETE", endpoint, **kwargs)
        # Some DELETE requests return empty response
        if response.text:
            return response.json()
        return {}

    async def download_file(self, endpoint: str, **kwargs) -> bytes:
        """
        Download file content (async)

        Args:
            endpoint: API endpoint
            **kwargs: Additional arguments

        Returns:
            File content as bytes
        """
        if not self._client:
            raise RuntimeError("Client not initialized")

        await self.rate_limiter.acquire()

        response = await self._client.get(endpoint, **kwargs)

        if response.status_code != 200:
            raise HerpAPIError(f"Failed to download file: {response.status_code}")

        return response.content
