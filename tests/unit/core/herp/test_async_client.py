"""
Tests for Async HERP Client (Main Facade)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.core.herp.async_client import AsyncHerpClient
from src.core.utils.config import HerpConfig


class TestAsyncHerpClientInitialization:
    """Test AsyncHerpClient initialization"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    def test_initialization_basic(self, config):
        """Test basic initialization"""
        client = AsyncHerpClient(config)

        assert client.config == config
        assert client._cache_manager is None
        assert client._enable_circuit_breaker is False
        assert client._circuit_breaker_config is None
        assert client._base_client is None

    def test_initialization_with_cache_manager(self, config):
        """Test initialization with cache manager"""
        cache_manager = Mock()
        client = AsyncHerpClient(config, cache_manager=cache_manager)

        assert client._cache_manager is cache_manager

    def test_initialization_with_circuit_breaker(self, config):
        """Test initialization with circuit breaker"""
        from src.core.circuit_breaker import CircuitBreakerConfig

        cb_config = CircuitBreakerConfig(
            name="test_cb", fail_max=10, timeout_duration=60
        )
        client = AsyncHerpClient(
            config, enable_circuit_breaker=True, circuit_breaker_config=cb_config
        )

        assert client._enable_circuit_breaker is True
        assert client._circuit_breaker_config == cb_config

    def test_initialization_with_metrics_collector(self, config):
        """Test initialization with custom metrics collector"""
        metrics = Mock()
        client = AsyncHerpClient(config, metrics_collector=metrics)

        assert client._metrics is metrics

    def test_specialized_clients_none_before_enter(self, config):
        """Test specialized clients are None before entering context"""
        client = AsyncHerpClient(config)

        assert client.candidacies is None
        assert client.contacts is None
        assert client.files is None
        assert client.evaluations is None
        assert client.assignments is None
        assert client.timeline is None
        assert client.master_data is None


class TestAsyncHerpClientContextManager:
    """Test async context manager functionality"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_context_manager_lifecycle(self, config):
        """Test async context manager enter and exit"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config) as client:
                # Should have created base client
                assert MockBaseClient.called
                # Should have entered base client context
                mock_base.__aenter__.assert_called_once()

                # Should have initialized all specialized clients
                assert client.candidacies is not None
                assert client.contacts is not None
                assert client.files is not None
                assert client.evaluations is not None
                assert client.assignments is not None
                assert client.timeline is not None
                assert client.master_data is not None

            # After exit, should have closed base client
            mock_base.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_specialized_clients_initialized(self, config):
        """Test all specialized clients are initialized on enter"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config) as client:
                from src.core.herp.async_candidates import AsyncCandidaciesAPI
                from src.core.herp.async_contacts import AsyncContactsAPI
                from src.core.herp.async_files import AsyncFilesAPI
                from src.core.herp.async_evaluations import AsyncEvaluationsAPI
                from src.core.herp.async_assignments import AsyncAssignmentsAPI
                from src.core.herp.async_timeline import AsyncTimelineAPI
                from src.core.herp.async_master_data import AsyncMasterDataAPI

                assert isinstance(client.candidacies, AsyncCandidaciesAPI)
                assert isinstance(client.contacts, AsyncContactsAPI)
                assert isinstance(client.files, AsyncFilesAPI)
                assert isinstance(client.evaluations, AsyncEvaluationsAPI)
                assert isinstance(client.assignments, AsyncAssignmentsAPI)
                assert isinstance(client.timeline, AsyncTimelineAPI)
                assert isinstance(client.master_data, AsyncMasterDataAPI)

    @pytest.mark.asyncio
    async def test_specialized_clients_cleared_on_exit(self, config):
        """Test specialized clients are cleared after exit"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            client_instance = AsyncHerpClient(config)

            async with client_instance as client:
                assert client.candidacies is not None

            # After exit, clients should be None
            assert client_instance.candidacies is None
            assert client_instance.contacts is None
            assert client_instance.files is None
            assert client_instance.evaluations is None
            assert client_instance.assignments is None
            assert client_instance.timeline is None
            assert client_instance.master_data is None
            assert client_instance._base_client is None

    @pytest.mark.asyncio
    async def test_base_client_receives_config(self, config):
        """Test base client receives correct config"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            cache_manager = Mock()
            from src.core.circuit_breaker import CircuitBreakerConfig

            cb_config = CircuitBreakerConfig(name="test_cb")
            metrics = Mock()

            async with AsyncHerpClient(
                config,
                cache_manager=cache_manager,
                enable_circuit_breaker=True,
                circuit_breaker_config=cb_config,
                metrics_collector=metrics,
            ):
                # Verify base client was created with correct parameters
                MockBaseClient.assert_called_once_with(
                    config=config,
                    cache_manager=cache_manager,
                    enable_circuit_breaker=True,
                    circuit_breaker_config=cb_config,
                    metrics_collector=metrics,
                )


class TestAsyncHerpClientProperties:
    """Test AsyncHerpClient properties"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_rate_limiter_property(self, config):
        """Test rate_limiter property returns base client's rate limiter"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            mock_rate_limiter = Mock()
            mock_base.rate_limiter = mock_rate_limiter
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config) as client:
                assert client.rate_limiter is mock_rate_limiter

    def test_rate_limiter_property_none_before_enter(self, config):
        """Test rate_limiter is None before entering context"""
        client = AsyncHerpClient(config)

        assert client.rate_limiter is None

    @pytest.mark.asyncio
    async def test_metrics_property(self, config):
        """Test metrics property returns metrics collector"""
        metrics = Mock()

        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config, metrics_collector=metrics) as client:
                assert client.metrics is metrics

    @pytest.mark.asyncio
    async def test_cache_manager_property(self, config):
        """Test cache_manager property returns cache manager"""
        cache_manager = Mock()

        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config, cache_manager=cache_manager) as client:
                assert client.cache_manager is cache_manager


class TestAsyncHerpClientErrorHandling:
    """Test error handling in AsyncHerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_exception_in_context_still_closes(self, config):
        """Test exception in context still calls __aexit__"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            with pytest.raises(ValueError, match="Test error"):
                async with AsyncHerpClient(config):
                    raise ValueError("Test error")

            # Should still have called __aexit__
            mock_base.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_base_client_enter_failure(self, config):
        """Test failure during base client __aenter__"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            mock_base.__aenter__.side_effect = RuntimeError("Connection failed")
            MockBaseClient.return_value = mock_base

            with pytest.raises(RuntimeError, match="Connection failed"):
                async with AsyncHerpClient(config):
                    pass  # Should not reach here


class TestAsyncHerpClientIntegration:
    """Integration-style tests for AsyncHerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_multiple_operations_in_context(self, config):
        """Test performing multiple operations in single context"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            async with AsyncHerpClient(config) as client:
                # Should be able to access all APIs
                assert client.candidacies is not None
                assert client.contacts is not None
                assert client.files is not None

                # All should share same base client
                assert client.candidacies.client is mock_base
                assert client.contacts.client is mock_base
                assert client.files.client is mock_base

    @pytest.mark.asyncio
    async def test_reusing_client_instance(self, config):
        """Test reusing same client instance in multiple contexts"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            client_instance = AsyncHerpClient(config)

            # First context
            async with client_instance as client:
                assert client.candidacies is not None

            # After first exit
            assert client_instance.candidacies is None

            # Second context - should reinitialize
            async with client_instance as client:
                assert client.candidacies is not None

            # After second exit
            assert client_instance.candidacies is None


class TestAsyncHerpClientEdgeCases:
    """Test edge cases for AsyncHerpClient"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    def test_metrics_defaults_to_global(self, config):
        """Test metrics collector defaults to global instance"""
        with patch(
            "src.core.herp.async_client.get_metrics_collector"
        ) as mock_get_metrics:
            mock_metrics = Mock()
            mock_get_metrics.return_value = mock_metrics

            client = AsyncHerpClient(config)

            assert client._metrics is mock_metrics
            mock_get_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_base_client_exit_with_exception_info(self, config):
        """Test __aexit__ passes exception info to base client"""
        with patch("src.core.herp.async_client.AsyncHerpBaseClient") as MockBaseClient:
            mock_base = AsyncMock()
            MockBaseClient.return_value = mock_base

            with pytest.raises(ValueError):
                async with AsyncHerpClient(config):
                    raise ValueError("Test")

            # Verify __aexit__ was called with exception info
            call_args = mock_base.__aexit__.call_args[0]
            assert call_args[0] == ValueError  # exc_type
            assert isinstance(call_args[1], ValueError)  # exc_val
            assert call_args[2] is not None  # exc_tb
