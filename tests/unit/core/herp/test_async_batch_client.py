"""
Tests for HERP Async Batch Client
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.core.herp.async_batch_client import AsyncBatchHerpClient, AsyncBatchResult
from src.core.utils.config import HerpConfig


class TestAsyncBatchResult:
    """Test AsyncBatchResult dataclass"""

    def test_initialization(self):
        """Test batch result initialization"""
        result = AsyncBatchResult(
            successful=[{"id": "cand_1"}],
            failed=[{"id": "cand_2", "error": "Not found"}],
            total=2,
            success_count=1,
            failure_count=1,
        )

        assert len(result.successful) == 1
        assert len(result.failed) == 1
        assert result.total == 2
        assert result.success_count == 1
        assert result.failure_count == 1

    def test_str_representation(self):
        """Test string representation"""
        result = AsyncBatchResult(
            successful=[], failed=[], total=10, success_count=8, failure_count=2
        )

        str_repr = str(result)

        assert "total=10" in str_repr
        assert "successful=8" in str_repr
        assert "failed=2" in str_repr


class TestAsyncBatchHerpClientInitialization:
    """Test AsyncBatchHerpClient initialization"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    def test_initialization_basic(self, config):
        """Test basic initialization"""
        batch_client = AsyncBatchHerpClient(config)

        assert batch_client.config == config
        assert batch_client.max_concurrency == 10  # Default
        assert batch_client.client_kwargs == {}
        assert batch_client._client is None

    def test_initialization_with_custom_concurrency(self, config):
        """Test initialization with custom concurrency"""
        batch_client = AsyncBatchHerpClient(config, max_concurrency=20)

        assert batch_client.max_concurrency == 20

    def test_initialization_with_client_kwargs(self, config):
        """Test initialization with client kwargs"""
        cache_manager = Mock()
        batch_client = AsyncBatchHerpClient(
            config, max_concurrency=15, cache_manager=cache_manager
        )

        assert batch_client.max_concurrency == 15
        assert "cache_manager" in batch_client.client_kwargs
        assert batch_client.client_kwargs["cache_manager"] is cache_manager


class TestAsyncBatchHerpClientContextManager:
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
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config) as batch_client:
                # Should have created client
                assert MockClient.called
                # Should have entered client context
                mock_client.__aenter__.assert_called_once()
                # Client should be set
                assert batch_client._client is mock_client

            # After exit, should have closed client
            mock_client.__aexit__.assert_called_once()
            # Client should be None
            assert batch_client._client is None

    @pytest.mark.asyncio
    async def test_context_passes_client_kwargs(self, config):
        """Test context manager passes kwargs to client"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            cache_manager = Mock()

            async with AsyncBatchHerpClient(
                config, max_concurrency=20, cache_manager=cache_manager
            ):
                # Verify client was created with config and kwargs
                MockClient.assert_called_once_with(config, cache_manager=cache_manager)


class TestAsyncBatchHerpClientFetchCandidacies:
    """Test fetch_candidacies method"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_fetch_candidacies_all_successful(self, config):
        """Test fetching candidacies with all successes"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.get = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "name": "Alice"},
                    {"id": "cand_2", "name": "Bob"},
                    {"id": "cand_3", "name": "Charlie"},
                ]
            )
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config, max_concurrency=10) as batch_client:
                result = await batch_client.fetch_candidacies(
                    ["cand_1", "cand_2", "cand_3"]
                )

            assert result.total == 3
            assert result.success_count == 3
            assert result.failure_count == 0
            assert len(result.successful) == 3
            assert len(result.failed) == 0
            assert result.successful[0]["name"] in ["Alice", "Bob", "Charlie"]

    @pytest.mark.asyncio
    async def test_fetch_candidacies_with_failures(self, config):
        """Test fetching candidacies with some failures"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.get = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "name": "Alice"},
                    Exception("Not found"),
                    {"id": "cand_3", "name": "Charlie"},
                ]
            )
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.fetch_candidacies(
                    ["cand_1", "cand_2", "cand_3"]
                )

            assert result.total == 3
            assert result.success_count == 2
            assert result.failure_count == 1
            assert len(result.successful) == 2
            assert len(result.failed) == 1
            assert result.failed[0]["id"] == "cand_2"
            assert "error" in result.failed[0]

    @pytest.mark.asyncio
    async def test_fetch_candidacies_empty_list(self, config):
        """Test fetching with empty list"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.fetch_candidacies([])

            assert result.total == 0
            assert result.success_count == 0
            assert result.failure_count == 0

    @pytest.mark.asyncio
    async def test_fetch_candidacies_without_context(self, config):
        """Test fetch_candidacies raises error outside context"""
        batch_client = AsyncBatchHerpClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await batch_client.fetch_candidacies(["cand_1"])


class TestAsyncBatchHerpClientCreateCandidacies:
    """Test create_candidacies method"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_create_candidacies_all_successful(self, config):
        """Test creating candidacies with all successes"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.create = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "name": "Alice"},
                    {"id": "cand_2", "name": "Bob"},
                ]
            )
            MockClient.return_value = mock_client

            candidacy_data = [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.create_candidacies(candidacy_data)

            assert result.total == 2
            assert result.success_count == 2
            assert result.failure_count == 0
            assert len(result.successful) == 2

    @pytest.mark.asyncio
    async def test_create_candidacies_with_failures(self, config):
        """Test creating candidacies with some failures"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.create = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "name": "Alice"},
                    Exception("Validation error"),
                ]
            )
            MockClient.return_value = mock_client

            candidacy_data = [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "invalid"},
            ]

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.create_candidacies(candidacy_data)

            assert result.total == 2
            assert result.success_count == 1
            assert result.failure_count == 1
            assert len(result.failed) == 1
            assert result.failed[0]["index"] == 1
            assert "error" in result.failed[0]

    @pytest.mark.asyncio
    async def test_create_candidacies_without_context(self, config):
        """Test create_candidacies raises error outside context"""
        batch_client = AsyncBatchHerpClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await batch_client.create_candidacies([{"name": "Test"}])


class TestAsyncBatchHerpClientUpdateSteps:
    """Test update_candidacy_steps method"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_update_steps_all_successful(self, config):
        """Test updating steps with all successes"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.update_step = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "step": "interview"},
                    {"id": "cand_2", "step": "offer"},
                ]
            )
            MockClient.return_value = mock_client

            updates = [
                {"candidacy_id": "cand_1", "step": "interview"},
                {"candidacy_id": "cand_2", "step": "offer", "comment": "Great fit"},
            ]

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.update_candidacy_steps(updates)

            assert result.total == 2
            assert result.success_count == 2
            assert result.failure_count == 0

            # Verify update_step was called correctly
            assert mock_client.candidacies.update_step.call_count == 2

    @pytest.mark.asyncio
    async def test_update_steps_with_failures(self, config):
        """Test updating steps with some failures"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.update_step = AsyncMock(
                side_effect=[
                    {"id": "cand_1", "step": "interview"},
                    Exception("Invalid step"),
                ]
            )
            MockClient.return_value = mock_client

            updates = [
                {"candidacy_id": "cand_1", "step": "interview"},
                {"candidacy_id": "cand_2", "step": "invalid_step"},
            ]

            async with AsyncBatchHerpClient(config) as batch_client:
                result = await batch_client.update_candidacy_steps(updates)

            assert result.total == 2
            assert result.success_count == 1
            assert result.failure_count == 1
            assert result.failed[0]["candidacy_id"] == "cand_2"

    @pytest.mark.asyncio
    async def test_update_steps_without_context(self, config):
        """Test update_candidacy_steps raises error outside context"""
        batch_client = AsyncBatchHerpClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await batch_client.update_candidacy_steps(
                [{"candidacy_id": "cand_1", "step": "interview"}]
            )


class TestAsyncBatchHerpClientDelegation:
    """Test delegation methods"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_fetch_contacts_for_multiple_delegates(self, config):
        """Test fetch_contacts_for_multiple delegates to contacts API"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.contacts.list_for_multiple = AsyncMock(
                return_value={
                    "cand_1": [{"id": "contact_1"}],
                    "cand_2": [{"id": "contact_2"}],
                }
            )
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config, max_concurrency=20) as batch_client:
                result = await batch_client.fetch_contacts_for_multiple(
                    ["cand_1", "cand_2"]
                )

            # Should delegate with max_concurrency
            mock_client.contacts.list_for_multiple.assert_called_once_with(
                ["cand_1", "cand_2"], max_concurrency=20
            )
            assert "cand_1" in result
            assert "cand_2" in result

    @pytest.mark.asyncio
    async def test_fetch_files_for_multiple_delegates(self, config):
        """Test fetch_files_for_multiple delegates to files API"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.files.list_for_multiple = AsyncMock(
                return_value={
                    "cand_1": [{"id": "file_1"}],
                    "cand_2": [{"id": "file_2"}],
                }
            )
            MockClient.return_value = mock_client

            async with AsyncBatchHerpClient(config, max_concurrency=15) as batch_client:
                result = await batch_client.fetch_files_for_multiple(
                    ["cand_1", "cand_2"]
                )

            # Should delegate with max_concurrency
            mock_client.files.list_for_multiple.assert_called_once_with(
                ["cand_1", "cand_2"], max_concurrency=15
            )
            assert "cand_1" in result

    @pytest.mark.asyncio
    async def test_fetch_contacts_without_context(self, config):
        """Test fetch_contacts raises error outside context"""
        batch_client = AsyncBatchHerpClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await batch_client.fetch_contacts_for_multiple(["cand_1"])

    @pytest.mark.asyncio
    async def test_fetch_files_without_context(self, config):
        """Test fetch_files raises error outside context"""
        batch_client = AsyncBatchHerpClient(config)

        with pytest.raises(RuntimeError, match="Client not initialized"):
            await batch_client.fetch_files_for_multiple(["cand_1"])


class TestAsyncBatchHerpClientEdgeCases:
    """Test edge cases for async batch client"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return HerpConfig(
            api_key="test_token_123",
            base_url="https://test-api.herp.cloud/hire/public",
        )

    @pytest.mark.asyncio
    async def test_exception_in_context_still_closes(self, config):
        """Test exception in context still closes client"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value = mock_client

            with pytest.raises(ValueError, match="Test error"):
                async with AsyncBatchHerpClient(config):
                    raise ValueError("Test error")

            # Should still have called __aexit__
            mock_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_batch_operation(self, config):
        """Test large batch operation (100+ items)"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            # Generate 150 successful responses
            mock_client.candidacies.get = AsyncMock(
                side_effect=[{"id": f"cand_{i}", "name": f"User {i}"} for i in range(150)]
            )
            MockClient.return_value = mock_client

            candidacy_ids = [f"cand_{i}" for i in range(150)]

            async with AsyncBatchHerpClient(config, max_concurrency=20) as batch_client:
                result = await batch_client.fetch_candidacies(candidacy_ids)

            assert result.total == 150
            assert result.success_count == 150
            assert result.failure_count == 0

    @pytest.mark.asyncio
    async def test_reusing_batch_client_instance(self, config):
        """Test reusing same batch client instance in multiple contexts"""
        with patch("src.core.herp.async_batch_client.AsyncHerpClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.candidacies.get = AsyncMock(
                return_value={"id": "cand_1", "name": "Test"}
            )
            MockClient.return_value = mock_client

            batch_client_instance = AsyncBatchHerpClient(config)

            # First context
            async with batch_client_instance as batch_client:
                result1 = await batch_client.fetch_candidacies(["cand_1"])
                assert result1.success_count == 1

            # After first exit
            assert batch_client_instance._client is None

            # Second context - should reinitialize
            async with batch_client_instance as batch_client:
                result2 = await batch_client.fetch_candidacies(["cand_1"])
                assert result2.success_count == 1

            # After second exit
            assert batch_client_instance._client is None
