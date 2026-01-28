"""
Tests for async base HTTP client
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

pytest.importorskip("httpx")

import httpx

from src.core.errors.exceptions import (
    HerpAPIError,
    HerpAuthenticationError,
    HerpNotFoundError,
    HerpRateLimitError,
    HerpServerError,
)
from src.core.herp.async_base_client import AsyncHerpBaseClient
from src.core.utils.config import HerpConfig


@pytest.fixture
def config():
    """Create test configuration"""
    return HerpConfig(
        api_key="test_key",
        base_url="https://api.test.com",
        rate_limit=100,
        timeout=30,
    )


@pytest_asyncio.fixture
async def async_client(config):
    """Create test async client"""
    async with AsyncHerpBaseClient(config) as client:
        yield client


@pytest.mark.asyncio
class TestAsyncHerpBaseClient:
    """Test AsyncHerpBaseClient"""

    async def test_initialization(self, config):
        """Test client initialization"""
        client = AsyncHerpBaseClient(config)

        assert client.config == config
        assert client.base_url == config.base_url
        assert client.rate_limiter is not None
        assert client._client is None  # Not initialized until __aenter__

    async def test_context_manager(self, config):
        """Test async context manager"""
        async with AsyncHerpBaseClient(config) as client:
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

        # Client should be closed after exit
        assert client._client is None

    async def test_headers(self, config):
        """Test request headers"""
        client = AsyncHerpBaseClient(config)
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_key"
        assert headers["Accept"] == "application/json"

    @patch("httpx.AsyncClient.request")
    async def test_successful_request(self, mock_request, async_client):
        """Test successful API request"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        # Make request
        response = await async_client._make_request("GET", "/test")

        assert response.status_code == 200

    @patch("httpx.AsyncClient.request")
    async def test_rate_limit_error(self, mock_request, async_client):
        """Test rate limit error handling"""
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60", "x-remaining-requests": "0"}
        mock_request.return_value = mock_response

        # Should raise HerpRateLimitError
        with pytest.raises(HerpRateLimitError):
            await async_client._make_request("GET", "/test")

    @patch("httpx.AsyncClient.request")
    async def test_authentication_error(self, mock_request, async_client):
        """Test authentication error handling"""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_request.return_value = mock_response

        # Should raise HerpAuthenticationError
        with pytest.raises(HerpAuthenticationError):
            await async_client._make_request("GET", "/test")

    @patch("httpx.AsyncClient.request")
    async def test_not_found_error(self, mock_request, async_client):
        """Test 404 error handling"""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_request.return_value = mock_response

        # Should raise HerpNotFoundError
        with pytest.raises(HerpNotFoundError):
            await async_client._make_request("GET", "/test")

    @patch("httpx.AsyncClient.request")
    async def test_server_error(self, mock_request, async_client):
        """Test server error handling"""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {}
        mock_request.return_value = mock_response

        # Should raise HerpServerError
        with pytest.raises(HerpServerError):
            await async_client._make_request("GET", "/test")

    @patch("httpx.AsyncClient.request")
    async def test_get_request(self, mock_request, async_client):
        """Test GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(return_value={"id": "123"})
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        result = await async_client.get("/test", params={"page": 1})

        assert result == {"id": "123"}

    @patch("httpx.AsyncClient.request")
    async def test_post_request(self, mock_request, async_client):
        """Test POST request"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json = AsyncMock(return_value={"id": "new"})
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        result = await async_client.post("/test", json={"name": "test"})

        assert result == {"id": "new"}

    async def test_request_without_initialization(self, config):
        """Test request fails without client initialization"""
        client = AsyncHerpBaseClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client._make_request("GET", "/test")

    async def test_connection_limits(self, config):
        """Test that connection limits are configured"""
        async with AsyncHerpBaseClient(config) as client:
            assert client._client is not None
            # Check limits are set (httpx.Limits object)
            limits = client._client._limits
            assert limits.max_keepalive_connections == 20
            assert limits.max_connections == 50
