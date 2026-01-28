"""
Tests for HERP Async Candidacies API Client
"""

from unittest.mock import AsyncMock

import pytest

from src.core.herp.async_candidates import AsyncCandidaciesAPI, AsyncHerpPaginator
from src.core.herp.query_dsl import Query


class TestAsyncHerpPaginatorInitialization:
    """Test AsyncHerpPaginator initialization"""

    def test_initialization(self):
        """Test paginator initialization"""
        fetch_fn = AsyncMock()

        paginator = AsyncHerpPaginator(
            fetch_fn, limit=50, max_pages=10, param1="value1"
        )

        assert paginator.fetch_function == fetch_fn
        assert paginator.limit == 50
        assert paginator.max_pages == 10
        assert paginator.fetch_kwargs == {"param1": "value1"}


class TestAsyncHerpPaginatorIteration:
    """Test AsyncHerpPaginator iteration"""

    @pytest.mark.asyncio
    async def test_paginate_single_page(self):
        """Test paginating single page"""
        fetch_fn = AsyncMock(
            return_value=[
                {"id": "cand_1", "name": "Alice"},
                {"id": "cand_2", "name": "Bob"},
            ]
        )

        paginator = AsyncHerpPaginator(fetch_fn, limit=100)

        results = []
        async for item in paginator:
            results.append(item)

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        fetch_fn.assert_called_once_with(page=1, limit=100)

    @pytest.mark.asyncio
    async def test_paginate_multiple_pages(self):
        """Test paginating multiple pages"""
        # First page full, second page partial
        fetch_fn = AsyncMock(
            side_effect=[
                [{"id": f"cand_{i}"} for i in range(100)],  # Page 1 (full)
                [{"id": f"cand_{i}"} for i in range(50)],  # Page 2 (partial)
            ]
        )

        paginator = AsyncHerpPaginator(fetch_fn, limit=100)

        results = []
        async for item in paginator:
            results.append(item)

        assert len(results) == 150
        assert fetch_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_paginate_respects_max_pages(self):
        """Test pagination respects max_pages limit"""
        fetch_fn = AsyncMock(
            return_value=[{"id": f"cand_{i}"} for i in range(100)]  # Always full pages
        )

        paginator = AsyncHerpPaginator(fetch_fn, limit=100, max_pages=2)

        results = []
        async for item in paginator:
            results.append(item)

        assert len(results) == 200  # 2 pages * 100 items
        assert fetch_fn.call_count == 2


class TestAsyncCandidaciesAPIInitialization:
    """Test AsyncCandidaciesAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncCandidaciesAPI(mock_client)

        assert api.client == mock_client


class TestAsyncCandidaciesAPIList:
    """Test list method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_candidacies(self, api):
        """Test listing candidacies"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "candidacies": [
                    {"id": "cand_1", "name": "Alice"},
                    {"id": "cand_2", "name": "Bob"},
                ]
            }
        )

        result = await api_instance.list()

        mock_client.get.assert_called_once()
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_list_with_updated_since(self, api):
        """Test list with updated_since filter"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"candidacies": []})

        await api_instance.list(updated_since="2026-01-01T00:00:00Z")

        # Verify params
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["updatedSince"] == "2026-01-01T00:00:00Z"

    @pytest.mark.asyncio
    async def test_list_respects_limit_max(self, api):
        """Test list respects max limit of 100"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"candidacies": []})

        await api_instance.list(limit=200)

        # Should cap at 100
        call_kwargs = mock_client.get.call_args[1]
        assert call_kwargs["params"]["limit"] == 100


class TestAsyncCandidaciesAPIIter:
    """Test iter method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    def test_iter_returns_paginator(self, api):
        """Test iter returns AsyncHerpPaginator"""
        api_instance, _ = api

        paginator = api_instance.iter()

        assert isinstance(paginator, AsyncHerpPaginator)


class TestAsyncCandidaciesAPIFetchAll:
    """Test fetch_all method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_fetch_all(self, api):
        """Test fetch_all loads all pages"""
        api_instance, mock_client = api

        # Two pages
        mock_client.get = AsyncMock(
            side_effect=[
                {"candidacies": [{"id": f"cand_{i}"} for i in range(100)]},
                {"candidacies": [{"id": f"cand_{i}"} for i in range(50)]},
            ]
        )

        result = await api_instance.fetch_all()

        assert len(result) == 150


class TestAsyncCandidaciesAPIGet:
    """Test get method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_get_candidacy(self, api):
        """Test getting candidacy by ID"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"candidacy": {"id": "cand_123", "name": "Alice"}}
        )

        result = await api_instance.get("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123")
        assert result["id"] == "cand_123"


class TestAsyncCandidaciesAPICreate:
    """Test create method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_create_candidacy(self, api):
        """Test creating candidacy"""
        api_instance, mock_client = api

        candidacy_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "requisitionId": "req_001",
        }

        mock_client.post = AsyncMock(
            return_value={"candidacy": {"id": "cand_123", **candidacy_data}}
        )

        result = await api_instance.create(candidacy_data)

        mock_client.post.assert_called_once_with("/v1/candidacies", json=candidacy_data)
        assert result["id"] == "cand_123"


class TestAsyncCandidaciesAPIUpdateStep:
    """Test update_step method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_update_step(self, api):
        """Test updating candidacy step"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(
            return_value={"candidacy": {"id": "cand_123", "step": "interview"}}
        )

        result = await api_instance.update_step("cand_123", "interview")

        mock_client.patch.assert_called_once()
        assert result["step"] == "interview"

    @pytest.mark.asyncio
    async def test_update_step_with_comment(self, api):
        """Test updating step with comment"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(return_value={"candidacy": {}})

        await api_instance.update_step("cand_123", "interview", comment="Great fit")

        # Verify comment was included
        call_kwargs = mock_client.patch.call_args[1]
        assert call_kwargs["json"]["comment"] == "Great fit"


class TestAsyncCandidaciesAPITerminate:
    """Test terminate method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_terminate(self, api):
        """Test terminating candidacy"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(
            return_value={"candidacy": {"id": "cand_123", "status": "terminated"}}
        )

        result = await api_instance.terminate("cand_123", "hired")

        mock_client.patch.assert_called_once_with(
            "/v1/candidacies/cand_123/termination", json={"reason": "hired"}
        )
        assert result["status"] == "terminated"


class TestAsyncCandidaciesAPISearch:
    """Test search method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_search_with_query(self, api):
        """Test search with Query DSL"""
        api_instance, mock_client = api

        # Set up pagination for fetch_all (single page)
        mock_client.get = AsyncMock(
            return_value={
                "candidacies": [
                    {"id": "cand_1", "email": "alice@example.com"},
                    {"id": "cand_2", "email": "bob@example.com"},
                    {"id": "cand_3", "email": "charlie@example.com"},
                ]
            }
        )

        query = Query().contains("email", "alice")

        results = await api_instance.search(query)

        assert len(results) == 1
        assert results[0]["email"] == "alice@example.com"

    @pytest.mark.asyncio
    async def test_search_with_limit(self, api):
        """Test search respects limit"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "candidacies": [
                    {"id": f"cand_{i}", "name": f"User {i}"} for i in range(10)
                ]
            }
        )

        results = await api_instance.search(limit=3)

        assert len(results) == 3


class TestAsyncCandidaciesAPIEdgeCases:
    """Test edge cases"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncCandidaciesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_data_key_fallback(self, api):
        """Test list falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"data": [{"id": "cand_1", "name": "Alice"}]}
        )

        result = await api_instance.list()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_astream_is_alias_for_iter(self, api):
        """Test astream is alias for iter"""
        api_instance, _ = api

        paginator1 = api_instance.iter(limit=50)
        paginator2 = api_instance.astream(chunk_size=50)

        # Both should return AsyncHerpPaginator instances
        assert isinstance(paginator1, AsyncHerpPaginator)
        assert isinstance(paginator2, AsyncHerpPaginator)
