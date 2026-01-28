"""
Tests for base HTTP client
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock

from src.core.herp.base_client import HerpBaseClient
from src.core.errors.exceptions import (
    HerpAPIError,
    HerpRateLimitError,
    HerpAuthenticationError,
    HerpNotFoundError,
)
from src.core.utils.config import HerpConfig


@pytest.fixture
def config():
    """Create test configuration"""
    return HerpConfig(
        api_key="test_token",
        base_url="https://api.test.com",
        rate_limit=100,
    )


@pytest.fixture
def client(config):
    """Create test client"""
    return HerpBaseClient(config)


class TestHerpBaseClient:
    """Test HerpBaseClient"""

    def test_initialization(self, config):
        """Test client initialization"""
        client = HerpBaseClient(config)

        assert client.config == config
        assert client.base_url == config.base_url
        assert client.session is not None
        assert client.rate_limiter is not None

    def test_headers(self, client):
        """Test request headers"""
        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"

    @patch("requests.Session.request")
    def test_successful_request(self, mock_request, client):
        """Test successful API request"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        # Make request
        response = client._make_request("GET", "/test")

        assert response.status_code == 200
        assert response.json() == {"data": "test"}

    @patch("requests.Session.request")
    def test_rate_limit_error(self, mock_request, client):
        """Test rate limit error handling"""
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"retry-after": "60", "x-remaining-requests": "0"}
        mock_request.return_value = mock_response

        # Should raise HerpRateLimitError
        with pytest.raises(HerpRateLimitError):
            client._make_request("GET", "/test")

    @patch("requests.Session.request")
    def test_authentication_error(self, mock_request, client):
        """Test authentication error handling"""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        # Should raise HerpAuthenticationError
        with pytest.raises(HerpAuthenticationError):
            client._make_request("GET", "/test")

    @patch("requests.Session.request")
    def test_not_found_error(self, mock_request, client):
        """Test 404 error handling"""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        # Should raise HerpNotFoundError
        with pytest.raises(HerpNotFoundError):
            client._make_request("GET", "/test")

    @patch("requests.Session.request")
    def test_server_error(self, mock_request, client):
        """Test server error handling"""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        # Should raise HerpAPIError (not HerpServerError)
        with pytest.raises(HerpAPIError):
            client._make_request("GET", "/test")

    @patch("requests.Session.request")
    def test_network_error(self, mock_request, client):
        """Test network error handling"""
        # Mock network error
        mock_request.side_effect = requests.RequestException("Network error")

        # Should raise RequestException (not wrapped)
        with pytest.raises(requests.RequestException) as exc_info:
            client._make_request("GET", "/test")

        assert "Network error" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_get_request(self, mock_request, client):
        """Test GET request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123"}
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        result = client.get("/test", params={"page": 1})

        assert result == {"id": "123"}
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_post_request(self, mock_request, client):
        """Test POST request"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "new"}
        mock_response.headers = {"x-remaining-requests": "100"}
        mock_request.return_value = mock_response

        result = client.post("/test", json={"name": "test"})

        assert result == {"id": "new"}

    def test_connection_pooling(self, client):
        """Test that connection pooling is configured"""
        # Check that adapters are mounted
        assert "https://" in client.session.adapters
        assert "http://" in client.session.adapters

        # Verify adapter configuration
        adapter = client.session.get_adapter("https://api.test.com")
        assert adapter is not None
