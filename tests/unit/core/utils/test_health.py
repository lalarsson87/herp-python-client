"""
Tests for health check utilities
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.utils.health import (
    check_api_connectivity,
    check_rate_limiter,
    check_cache,
    check_configuration,
    perform_health_check,
    validate_configuration,
    get_system_info,
)


class TestAPIConnectivity:
    """Test API connectivity checks"""

    @patch("src.core.utils.health.HerpClient")
    @patch("src.core.utils.health.load_herp_config")
    def test_api_accessible(self, mock_config, mock_client_class):
        """Test successful API connectivity"""
        # Mock config
        mock_cfg = Mock()
        mock_cfg.base_url = "https://api.test.com"
        mock_config.return_value = mock_cfg

        # Mock client
        mock_client = Mock()
        mock_client.candidacies.list.return_value = [{"id": "test"}]
        mock_client_class.return_value = mock_client

        result = check_api_connectivity()

        assert result["healthy"] is True
        assert "API is accessible" in result["message"]
        assert result["details"]["base_url"] == "https://api.test.com"

    @patch("src.core.utils.health.HerpClient")
    @patch("src.core.utils.health.load_herp_config")
    def test_api_not_accessible(self, mock_config, mock_client_class):
        """Test failed API connectivity"""
        mock_config.return_value = Mock()
        mock_client_class.side_effect = Exception("Connection failed")

        result = check_api_connectivity()

        assert result["healthy"] is False
        assert "failed" in result["message"].lower()


class TestRateLimiterCheck:
    """Test rate limiter health checks"""

    @patch("src.core.utils.health.HerpClient")
    @patch("src.core.utils.health.load_herp_config")
    def test_rate_limiter_ok(self, mock_config, mock_client_class):
        """Test rate limiter health check"""
        mock_config.return_value = Mock()

        # Mock client with rate limiter
        mock_rate_limiter = Mock()
        mock_rate_limiter.requests_per_minute = 100
        mock_rate_limiter.current_tokens = 50

        mock_client = Mock()
        mock_client.base_client.rate_limiter = mock_rate_limiter
        mock_client_class.return_value = mock_client

        result = check_rate_limiter()

        assert result["healthy"] is True
        assert result["details"]["requests_per_minute"] == 100


class TestCacheCheck:
    """Test cache health checks"""

    def test_cache_check(self):
        """Test cache health check (no global cache manager exists)"""
        result = check_cache()

        # Since there's no global cache manager, should report as disabled
        assert result["healthy"] is True
        assert result["message"] == "Cache disabled"
        assert result["details"]["enabled"] is False


class TestConfigurationCheck:
    """Test configuration validation"""

    @patch("src.core.utils.health.load_herp_config")
    def test_valid_configuration(self, mock_config):
        """Test valid configuration"""
        mock_cfg = Mock()
        mock_cfg.api_token = "test_token"
        mock_cfg.base_url = "https://api.test.com"
        mock_cfg.rate_limit = 100
        mock_cfg.timeout = 30
        mock_config.return_value = mock_cfg

        result = check_configuration()

        assert result["healthy"] is True
        assert "valid" in result["message"].lower()

    @patch("src.core.utils.health.load_herp_config")
    def test_invalid_configuration(self, mock_config):
        """Test invalid configuration"""
        mock_cfg = Mock()
        mock_cfg.api_token = ""  # Missing token
        mock_cfg.base_url = "https://api.test.com"
        mock_cfg.rate_limit = 100
        mock_cfg.timeout = 30
        mock_config.return_value = mock_cfg

        result = check_configuration()

        assert result["healthy"] is False
        assert "API token" in result["message"]


class TestPerformHealthCheck:
    """Test comprehensive health check"""

    @patch("src.core.utils.health.check_cache")
    @patch("src.core.utils.health.check_rate_limiter")
    @patch("src.core.utils.health.check_api_connectivity")
    @patch("src.core.utils.health.check_configuration")
    def test_all_checks(self, mock_config, mock_api, mock_rate, mock_cache):
        """Test that all health checks are performed"""
        mock_config.return_value = {"healthy": True, "message": "OK"}
        mock_api.return_value = {"healthy": True, "message": "OK"}
        mock_rate.return_value = {"healthy": True, "message": "OK"}
        mock_cache.return_value = {"healthy": True, "message": "OK"}

        results = perform_health_check()

        assert "Configuration" in results
        assert "API Connectivity" in results
        assert "Rate Limiter" in results
        assert "Cache" in results


class TestValidateConfiguration:
    """Test configuration validation"""

    @patch.dict(
        "os.environ",
        {
            "HERP_API_TOKEN": "test_token",
            "HERP_BASE_URL": "https://api.test.com",
            "HERP_RATE_LIMIT": "100",
            "HERP_TIMEOUT": "30",
        },
    )
    def test_valid_env_vars(self):
        """Test validation with valid environment variables"""
        results = validate_configuration()

        assert results["API Token"]["valid"] is True
        assert results["Base URL"]["valid"] is True
        assert results["Rate Limit"]["valid"] is True
        assert results["Timeout"]["valid"] is True

    @patch.dict("os.environ", {}, clear=True)
    def test_missing_env_vars(self):
        """Test validation with missing environment variables"""
        results = validate_configuration()

        assert results["API Token"]["valid"] is False
        assert results["Base URL"]["valid"] is False
        assert "suggestion" in results["API Token"]

    @patch.dict("os.environ", {"HERP_RATE_LIMIT": "invalid"})
    def test_invalid_rate_limit(self):
        """Test validation with invalid rate limit"""
        results = validate_configuration()

        assert results["Rate Limit"]["valid"] is False
        assert "integer" in results["Rate Limit"]["suggestion"]


class TestGetSystemInfo:
    """Test system info retrieval"""

    def test_system_info(self):
        """Test that system info is retrieved"""
        info = get_system_info()

        assert "package_version" in info
        assert "python_version" in info
        assert "platform" in info
        assert "architecture" in info
