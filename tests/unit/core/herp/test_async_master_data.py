"""
Tests for HERP Async Master Data API Client
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.core.herp.async_master_data import AsyncMasterDataAPI


class TestAsyncMasterDataAPIInitialization:
    """Test AsyncMasterDataAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncMasterDataAPI(mock_client)

        assert api.client == mock_client


class TestAsyncMasterDataAPIListRequisitions:
    """Test list_requisitions method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncMasterDataAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_requisitions_no_cache(self, api):
        """Test listing requisitions without caching"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "requisitions": [
                    {
                        "id": "req_1",
                        "title": "Senior Python Engineer",
                        "status": "open",
                        "department": "Engineering",
                    },
                    {
                        "id": "req_2",
                        "title": "Product Manager",
                        "status": "open",
                        "department": "Product",
                    },
                ]
            }
        )

        result = await api_instance.list_requisitions(use_cache=False)

        mock_client.get.assert_called_once_with("/v1/requisitions")
        assert len(result) == 2
        assert result[0]["title"] == "Senior Python Engineer"
        assert result[1]["department"] == "Product"

    @pytest.mark.asyncio
    async def test_list_requisitions_with_cache(self, api):
        """Test listing requisitions with caching"""
        api_instance, mock_client = api

        # Setup cache manager
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)  # Cache miss
        mock_cache.set = Mock()
        mock_client.cache_manager = mock_cache

        mock_client.get = AsyncMock(
            return_value={
                "requisitions": [
                    {"id": "req_1", "title": "Senior Engineer", "status": "open"}
                ]
            }
        )

        result = await api_instance.list_requisitions(use_cache=True, ttl=300)

        # Should check cache
        mock_cache.get.assert_called_once_with("herp:master_data:requisitions")

        # Should fetch from API
        mock_client.get.assert_called_once()

        # Should store in cache
        mock_cache.set.assert_called_once()
        assert mock_cache.set.call_args[0][0] == "herp:master_data:requisitions"
        assert mock_cache.set.call_args[1]["ttl"] == 300

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_requisitions_cache_hit(self, api):
        """Test listing requisitions returns cached data"""
        api_instance, mock_client = api

        # Setup cache with cached data
        cached_data = [{"id": "req_cached", "title": "Cached Req"}]
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=cached_data)
        mock_client.cache_manager = mock_cache

        result = await api_instance.list_requisitions(use_cache=True)

        # Should check cache
        mock_cache.get.assert_called_once_with("herp:master_data:requisitions")

        # Should NOT call API
        mock_client.get.assert_not_called()

        # Should return cached data
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_list_requisitions_no_cache_manager(self, api):
        """Test listing requisitions when no cache manager"""
        api_instance, mock_client = api

        # No cache manager
        mock_client.cache_manager = None

        mock_client.get = AsyncMock(
            return_value={"requisitions": [{"id": "req_1", "title": "Engineer"}]}
        )

        result = await api_instance.list_requisitions(use_cache=True)

        # Should fetch directly without caching
        mock_client.get.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_requisitions_data_key_fallback(self, api):
        """Test list requisitions falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"data": [{"id": "req_1", "title": "Engineer"}]}
        )

        result = await api_instance.list_requisitions(use_cache=False)

        assert len(result) == 1
        assert result[0]["id"] == "req_1"

    @pytest.mark.asyncio
    async def test_list_requisitions_empty(self, api):
        """Test listing when no requisitions"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"requisitions": []})

        result = await api_instance.list_requisitions(use_cache=False)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_requisitions_custom_ttl(self, api):
        """Test listing requisitions with custom TTL"""
        api_instance, mock_client = api

        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        mock_client.cache_manager = mock_cache

        mock_client.get = AsyncMock(return_value={"requisitions": []})

        await api_instance.list_requisitions(use_cache=True, ttl=600)

        # Should use custom TTL
        assert mock_cache.set.call_args[1]["ttl"] == 600


class TestAsyncMasterDataAPIListUsers:
    """Test list_users method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncMasterDataAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_users_no_cache(self, api):
        """Test listing users without caching"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "users": [
                    {
                        "id": "user_1",
                        "name": "Alice Smith",
                        "email": "alice@company.com",
                        "role": "recruiter",
                    },
                    {
                        "id": "user_2",
                        "name": "Bob Jones",
                        "email": "bob@company.com",
                        "role": "hiring_manager",
                    },
                ]
            }
        )

        result = await api_instance.list_users(use_cache=False)

        mock_client.get.assert_called_once_with("/v1/users")
        assert len(result) == 2
        assert result[0]["name"] == "Alice Smith"
        assert result[1]["role"] == "hiring_manager"

    @pytest.mark.asyncio
    async def test_list_users_with_cache(self, api):
        """Test listing users with caching"""
        api_instance, mock_client = api

        # Setup cache manager
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)  # Cache miss
        mock_cache.set = Mock()
        mock_client.cache_manager = mock_cache

        mock_client.get = AsyncMock(
            return_value={
                "users": [{"id": "user_1", "name": "Alice Smith", "role": "recruiter"}]
            }
        )

        result = await api_instance.list_users(use_cache=True, ttl=600)

        # Should check cache
        mock_cache.get.assert_called_once_with("herp:master_data:users")

        # Should fetch from API
        mock_client.get.assert_called_once()

        # Should store in cache
        mock_cache.set.assert_called_once()
        assert mock_cache.set.call_args[0][0] == "herp:master_data:users"
        assert mock_cache.set.call_args[1]["ttl"] == 600

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_users_cache_hit(self, api):
        """Test listing users returns cached data"""
        api_instance, mock_client = api

        # Setup cache with cached data
        cached_data = [{"id": "user_cached", "name": "Cached User"}]
        mock_cache = Mock()
        mock_cache.get = Mock(return_value=cached_data)
        mock_client.cache_manager = mock_cache

        result = await api_instance.list_users(use_cache=True)

        # Should check cache
        mock_cache.get.assert_called_once_with("herp:master_data:users")

        # Should NOT call API
        mock_client.get.assert_not_called()

        # Should return cached data
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_list_users_no_cache_manager(self, api):
        """Test listing users when no cache manager"""
        api_instance, mock_client = api

        # No cache manager
        mock_client.cache_manager = None

        mock_client.get = AsyncMock(
            return_value={"users": [{"id": "user_1", "name": "Alice"}]}
        )

        result = await api_instance.list_users(use_cache=True)

        # Should fetch directly without caching
        mock_client.get.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_users_data_key_fallback(self, api):
        """Test list users falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"data": [{"id": "user_1", "name": "Alice"}]}
        )

        result = await api_instance.list_users(use_cache=False)

        assert len(result) == 1
        assert result[0]["id"] == "user_1"

    @pytest.mark.asyncio
    async def test_list_users_empty(self, api):
        """Test listing when no users"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"users": []})

        result = await api_instance.list_users(use_cache=False)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_users_custom_ttl(self, api):
        """Test listing users with custom TTL"""
        api_instance, mock_client = api

        mock_cache = Mock()
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        mock_client.cache_manager = mock_cache

        mock_client.get = AsyncMock(return_value={"users": []})

        await api_instance.list_users(use_cache=True, ttl=1200)

        # Should use custom TTL
        assert mock_cache.set.call_args[1]["ttl"] == 1200


class TestAsyncMasterDataAPICaching:
    """Test caching behavior"""

    @pytest.fixture
    def api(self):
        """Create API instance with cache manager"""
        mock_client = AsyncMock()
        mock_cache = Mock()
        mock_client.cache_manager = mock_cache
        return AsyncMasterDataAPI(mock_client), mock_client, mock_cache

    @pytest.mark.asyncio
    async def test_cached_fetch_cache_hit(self, api):
        """Test _cached_fetch returns cached data"""
        api_instance, mock_client, mock_cache = api

        cached_data = {"cached": True}
        mock_cache.get = Mock(return_value=cached_data)

        async def fetch_fn():
            return {"fresh": True}

        result = await api_instance._cached_fetch("test_key", fetch_fn)

        # Should return cached data
        assert result == cached_data

        # Fetch function should not be called
        mock_cache.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_cached_fetch_cache_miss(self, api):
        """Test _cached_fetch fetches and caches on miss"""
        api_instance, mock_client, mock_cache = api

        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()

        async def fetch_fn():
            return {"fresh": True}

        result = await api_instance._cached_fetch("test_key", fetch_fn, ttl=120)

        # Should return fresh data
        assert result == {"fresh": True}

        # Should store in cache
        mock_cache.set.assert_called_once_with("test_key", {"fresh": True}, ttl=120)

    @pytest.mark.asyncio
    async def test_cached_fetch_no_cache_manager(self, api):
        """Test _cached_fetch without cache manager"""
        api_instance, mock_client, _ = api

        # Remove cache manager
        mock_client.cache_manager = None

        async def fetch_fn():
            return {"fresh": True}

        result = await api_instance._cached_fetch("test_key", fetch_fn)

        # Should return fresh data without caching
        assert result == {"fresh": True}

    def test_invalidate_cache(self, api):
        """Test cache invalidation"""
        api_instance, mock_client, mock_cache = api

        mock_cache.delete = Mock()

        api_instance._invalidate_cache("test_key")

        mock_cache.delete.assert_called_once_with("test_key")

    def test_invalidate_cache_no_cache_manager(self, api):
        """Test cache invalidation without cache manager"""
        api_instance, mock_client, _ = api

        # Remove cache manager
        mock_client.cache_manager = None

        # Should not raise error
        api_instance._invalidate_cache("test_key")


class TestAsyncMasterDataAPIIntegration:
    """Integration-style tests for AsyncMasterDataAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        mock_cache = Mock()
        mock_client.cache_manager = mock_cache
        return AsyncMasterDataAPI(mock_client), mock_client, mock_cache

    @pytest.mark.asyncio
    async def test_requisitions_cache_workflow(self, api):
        """Test requisitions caching workflow"""
        api_instance, mock_client, mock_cache = api

        # First call - cache miss
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        mock_client.get = AsyncMock(
            return_value={"requisitions": [{"id": "req_1", "title": "Engineer"}]}
        )

        result1 = await api_instance.list_requisitions(use_cache=True)
        assert len(result1) == 1

        # Second call - cache hit
        mock_cache.get = Mock(return_value=result1)
        result2 = await api_instance.list_requisitions(use_cache=True)

        # Should return same data
        assert result2 == result1

        # API should only be called once
        assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_users_cache_workflow(self, api):
        """Test users caching workflow"""
        api_instance, mock_client, mock_cache = api

        # First call - cache miss
        mock_cache.get = Mock(return_value=None)
        mock_cache.set = Mock()
        mock_client.get = AsyncMock(
            return_value={"users": [{"id": "user_1", "name": "Alice"}]}
        )

        result1 = await api_instance.list_users(use_cache=True)
        assert len(result1) == 1

        # Second call - cache hit
        mock_cache.get = Mock(return_value=result1)
        result2 = await api_instance.list_users(use_cache=True)

        # Should return same data
        assert result2 == result1

        # API should only be called once
        assert mock_client.get.call_count == 1


class TestAsyncMasterDataAPIEdgeCases:
    """Test edge cases for async master data API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncMasterDataAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_requisitions_malformed_response(self, api):
        """Test list requisitions handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'requisitions' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list_requisitions(use_cache=False)

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_list_users_malformed_response(self, api):
        """Test list users handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'users' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list_users(use_cache=False)

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_cache_manager_attribute_missing(self, api):
        """Test when cache_manager attribute doesn't exist"""
        api_instance, mock_client = api

        # Remove cache_manager attribute entirely
        delattr(mock_client, "cache_manager")

        mock_client.get = AsyncMock(return_value={"requisitions": [{"id": "req_1"}]})

        # Should work without caching
        result = await api_instance.list_requisitions(use_cache=True)

        assert len(result) == 1
