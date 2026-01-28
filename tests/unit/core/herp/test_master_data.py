"""
Tests for HERP Master Data API Client
"""

from unittest.mock import Mock, patch

import pytest

from src.core.herp.master_data import MasterDataAPI


class TestMasterDataAPI:
    """Test MasterDataAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        client = Mock()
        # Mock cache_manager
        client.cache_manager = Mock()
        client.cache_manager.get = Mock(return_value=None)
        client.cache_manager.set = Mock()
        return client

    @pytest.fixture
    def api(self, mock_client):
        """Create MasterDataAPI instance"""
        return MasterDataAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = MasterDataAPI(mock_client)

        assert api.client == mock_client

    def test_list_requisitions_no_cache(self, api, mock_client):
        """Test listing requisitions without cache"""
        mock_client.get.return_value = {
            "requisitions": [
                {"id": "req_1", "title": "Software Engineer", "status": "open"},
                {"id": "req_2", "title": "Product Manager", "status": "open"},
            ]
        }

        result = api.list_requisitions(use_cache=False)

        mock_client.get.assert_called_once_with("/v1/requisitions")
        assert len(result) == 2
        assert result[0]["title"] == "Software Engineer"
        assert result[1]["title"] == "Product Manager"

    def test_list_requisitions_with_cache_miss(self, api, mock_client):
        """Test list requisitions with cache miss"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {
            "requisitions": [{"id": "req_1", "title": "Engineer"}]
        }

        result = api.list_requisitions(use_cache=True)

        # Should fetch from API
        assert mock_client.get.called
        # Should cache result
        assert mock_client.cache_manager.set.called
        assert len(result) == 1

    def test_list_requisitions_with_cache_hit(self, api, mock_client):
        """Test list requisitions with cache hit"""
        cached_data = [{"id": "req_1", "title": "Cached Engineer"}]
        mock_client.cache_manager.get.return_value = cached_data

        result = api.list_requisitions(use_cache=True)

        # Should return cached data
        assert result == cached_data
        # Should not call API
        assert not mock_client.get.called

    def test_list_requisitions_default_cache_enabled(self, api, mock_client):
        """Test list requisitions uses cache by default"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"requisitions": []}

        api.list_requisitions()

        # Should attempt cache lookup (default use_cache=True)
        assert mock_client.cache_manager.get.called

    def test_list_requisitions_default_ttl(self, api, mock_client):
        """Test list requisitions uses default TTL of 300 seconds"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"requisitions": []}

        api.list_requisitions()

        # Should cache with default TTL
        call_args = mock_client.cache_manager.set.call_args
        assert call_args[1]["ttl"] == 300

    def test_list_requisitions_custom_ttl(self, api, mock_client):
        """Test list requisitions with custom TTL"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"requisitions": []}

        api.list_requisitions(use_cache=True, ttl=600)

        # Should cache with custom TTL
        call_args = mock_client.cache_manager.set.call_args
        assert call_args[1]["ttl"] == 600

    def test_list_requisitions_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key"""
        mock_client.get.return_value = {"data": [{"id": "req_1"}]}

        result = api.list_requisitions(use_cache=False)

        assert len(result) == 1

    def test_list_requisitions_empty(self, api, mock_client):
        """Test listing requisitions when none exist"""
        mock_client.get.return_value = {"requisitions": []}

        result = api.list_requisitions(use_cache=False)

        assert result == []

    def test_list_users_no_cache(self, api, mock_client):
        """Test listing users without cache"""
        mock_client.get.return_value = {
            "users": [
                {"id": "user_1", "name": "Alice", "email": "alice@company.com"},
                {"id": "user_2", "name": "Bob", "email": "bob@company.com"},
            ]
        }

        result = api.list_users(use_cache=False)

        mock_client.get.assert_called_once_with("/v1/users")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["email"] == "bob@company.com"

    def test_list_users_with_cache_miss(self, api, mock_client):
        """Test list users with cache miss"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"users": [{"id": "user_1", "name": "Alice"}]}

        result = api.list_users(use_cache=True)

        # Should fetch from API
        assert mock_client.get.called
        # Should cache result
        assert mock_client.cache_manager.set.called
        assert len(result) == 1

    def test_list_users_with_cache_hit(self, api, mock_client):
        """Test list users with cache hit"""
        cached_data = [{"id": "user_1", "name": "Cached User"}]
        mock_client.cache_manager.get.return_value = cached_data

        result = api.list_users(use_cache=True)

        # Should return cached data
        assert result == cached_data
        # Should not call API
        assert not mock_client.get.called

    def test_list_users_default_ttl(self, api, mock_client):
        """Test list users uses default TTL of 600 seconds"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"users": []}

        api.list_users()

        # Should cache with default TTL (600 for users)
        call_args = mock_client.cache_manager.set.call_args
        assert call_args[1]["ttl"] == 600

    def test_list_users_custom_ttl(self, api, mock_client):
        """Test list users with custom TTL"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"users": []}

        api.list_users(use_cache=True, ttl=1200)

        # Should cache with custom TTL
        call_args = mock_client.cache_manager.set.call_args
        assert call_args[1]["ttl"] == 1200

    def test_list_users_data_key_fallback(self, api, mock_client):
        """Test list users falls back to 'data' key"""
        mock_client.get.return_value = {"data": [{"id": "user_1"}]}

        result = api.list_users(use_cache=False)

        assert len(result) == 1

    def test_list_users_empty(self, api, mock_client):
        """Test listing users when none exist"""
        mock_client.get.return_value = {"users": []}

        result = api.list_users(use_cache=False)

        assert result == []

    def test_inherits_from_cache_mixin(self, api):
        """Test MasterDataAPI inherits from CacheMixin"""
        from src.core.herp.mixins import CacheMixin

        assert isinstance(api, CacheMixin)

    def test_has_cached_fetch_method(self, api):
        """Test MasterDataAPI has _cached_fetch method from mixin"""
        assert hasattr(api, "_cached_fetch")
        assert callable(api._cached_fetch)


class TestMasterDataAPIIntegration:
    """Integration-style tests for MasterDataAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        client = Mock()
        client.cache_manager = Mock()
        client.cache_manager.get = Mock(return_value=None)
        client.cache_manager.set = Mock()
        return client

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return MasterDataAPI(mock_client)

    def test_list_requisitions_and_users(self, api, mock_client):
        """Test listing both requisitions and users"""
        mock_client.get.side_effect = [
            {"requisitions": [{"id": "req_1"}]},
            {"users": [{"id": "user_1"}]},
        ]

        requisitions = api.list_requisitions(use_cache=False)
        users = api.list_users(use_cache=False)

        assert len(requisitions) == 1
        assert len(users) == 1

    def test_cache_keys_are_different(self, api, mock_client):
        """Test requisitions and users use different cache keys"""
        mock_client.cache_manager.get.return_value = None
        mock_client.get.return_value = {"requisitions": [], "users": []}

        api.list_requisitions(use_cache=True)
        requisitions_cache_key = mock_client.cache_manager.get.call_args[0][0]

        api.list_users(use_cache=True)
        users_cache_key = mock_client.cache_manager.get.call_args[0][0]

        # Should use different cache keys
        assert requisitions_cache_key != users_cache_key

    def test_refresh_cache(self, api, mock_client):
        """Test forcing cache refresh"""
        # First call with cache
        mock_client.cache_manager.get.return_value = [{"id": "old"}]
        cached = api.list_requisitions(use_cache=True)
        assert cached[0]["id"] == "old"

        # Force refresh
        mock_client.get.return_value = {"requisitions": [{"id": "new"}]}
        fresh = api.list_requisitions(use_cache=False)
        assert fresh[0]["id"] == "new"


class TestMasterDataAPIEdgeCases:
    """Test edge cases for MasterDataAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        client = Mock()
        client.cache_manager = Mock()
        client.cache_manager.get = Mock(return_value=None)
        client.cache_manager.set = Mock()
        return MasterDataAPI(client)

    def test_list_requisitions_no_cache_manager(self):
        """Test list requisitions when cache manager not available"""
        client = Mock(spec=["get"])  # Has get method but no cache_manager
        api = MasterDataAPI(client)

        client.get.return_value = {"requisitions": [{"id": "req_1"}]}

        # Should work without cache manager (falls back to direct fetch)
        result = api.list_requisitions(use_cache=True)

        assert len(result) == 1

    def test_list_users_no_cache_manager(self):
        """Test list users when cache manager not available"""
        client = Mock(spec=["get"])  # Has get method but no cache_manager
        api = MasterDataAPI(client)

        client.get.return_value = {"users": [{"id": "user_1"}]}

        # Should work without cache manager
        result = api.list_users(use_cache=True)

        assert len(result) == 1

    def test_list_requisitions_large_dataset(self, api):
        """Test list requisitions with large number of records"""
        large_dataset = [{"id": f"req_{i}", "title": f"Job {i}"} for i in range(1000)]
        api.client.get.return_value = {"requisitions": large_dataset}

        result = api.list_requisitions(use_cache=False)

        # Should handle large datasets
        assert len(result) == 1000

    def test_list_users_large_dataset(self, api):
        """Test list users with large number of records"""
        large_dataset = [{"id": f"user_{i}", "name": f"User {i}"} for i in range(500)]
        api.client.get.return_value = {"users": large_dataset}

        result = api.list_users(use_cache=False)

        assert len(result) == 500

    def test_cache_ttl_zero(self, api):
        """Test caching with zero TTL"""
        api.client.get.return_value = {"requisitions": []}

        api.list_requisitions(use_cache=True, ttl=0)

        # Should still attempt to cache (TTL validation is server-side)
        assert api.client.cache_manager.set.called

    def test_cache_ttl_very_large(self, api):
        """Test caching with very large TTL"""
        api.client.get.return_value = {"users": []}

        api.list_users(use_cache=True, ttl=86400)  # 24 hours

        call_args = api.client.cache_manager.set.call_args
        assert call_args[1]["ttl"] == 86400

    def test_requisitions_different_ttl_than_users(self, api):
        """Test requisitions and users have different default TTLs"""
        api.client.get.return_value = {}

        # Get default TTLs
        api.list_requisitions(use_cache=True)
        req_ttl = api.client.cache_manager.set.call_args[1]["ttl"]

        api.client.cache_manager.set.reset_mock()

        api.list_users(use_cache=True)
        user_ttl = api.client.cache_manager.set.call_args[1]["ttl"]

        # Users (600) should have longer TTL than requisitions (300)
        assert user_ttl > req_ttl

    def test_list_requisitions_with_unicode(self, api):
        """Test list requisitions with unicode characters"""
        api.client.get.return_value = {
            "requisitions": [
                {"id": "req_1", "title": "ソフトウェアエンジニア"},  # Japanese
                {"id": "req_2", "title": "开发工程师"},  # Chinese
            ]
        }

        result = api.list_requisitions(use_cache=False)

        # Should preserve unicode
        assert "ソフトウェア" in result[0]["title"]
        assert "开发" in result[1]["title"]

    def test_list_users_with_special_emails(self, api):
        """Test list users with special characters in emails"""
        api.client.get.return_value = {
            "users": [
                {"id": "user_1", "email": "user+test@company.com"},
                {"id": "user_2", "email": "user.name@sub.company.co.uk"},
            ]
        }

        result = api.list_users(use_cache=False)

        # Should preserve special characters
        assert "+" in result[0]["email"]
        assert ".co.uk" in result[1]["email"]
