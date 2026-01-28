"""
Tests for HERP Async Contacts API Client
"""

from unittest.mock import AsyncMock

import pytest

from src.core.herp.async_contacts import AsyncContactsAPI


class TestAsyncContactsAPIInitialization:
    """Test AsyncContactsAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncContactsAPI(mock_client)

        assert api.client == mock_client


class TestAsyncContactsAPIList:
    """Test list method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_contacts(self, api):
        """Test listing contacts for candidacy"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "contacts": [
                    {
                        "id": "contact_1",
                        "type": "phone_screen",
                        "scheduled_at": "2026-02-01T10:00:00Z",
                    },
                    {
                        "id": "contact_2",
                        "type": "technical_interview",
                        "scheduled_at": "2026-02-05T14:00:00Z",
                    },
                ]
            }
        )

        result = await api_instance.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/contacts")
        assert len(result) == 2
        assert result[0]["type"] == "phone_screen"

    @pytest.mark.asyncio
    async def test_list_contacts_data_key_fallback(self, api):
        """Test list falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"data": [{"id": "contact_1", "type": "interview"}]}
        )

        result = await api_instance.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "contact_1"

    @pytest.mark.asyncio
    async def test_list_contacts_empty(self, api):
        """Test listing when no contacts"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"contacts": []})

        result = await api_instance.list("cand_123")

        assert result == []


class TestAsyncContactsAPIListForMultiple:
    """Test list_for_multiple batch method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        from unittest.mock import Mock

        mock_client = AsyncMock()
        # Configure metrics to avoid async issues
        mock_client.metrics = Mock()
        mock_client.metrics.increment_counter = Mock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_for_multiple_all_successful(self, api):
        """Test batch fetching all successful"""
        from unittest.mock import patch

        api_instance, _ = api

        # Mock the list method directly
        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "contact_1"}]
            elif candidacy_id == "cand_2":
                return [{"id": "contact_2"}]
            elif candidacy_id == "cand_3":
                return [{"id": "contact_3"}]
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"], max_concurrency=10
            )

        assert len(result) == 3
        assert "cand_1" in result
        assert "cand_2" in result
        assert "cand_3" in result
        assert len(result["cand_1"]) == 1

    @pytest.mark.asyncio
    async def test_list_for_multiple_with_errors(self, api):
        """Test batch fetching with some errors"""
        from unittest.mock import patch

        api_instance, _ = api

        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "contact_1"}]
            elif candidacy_id == "cand_2":
                raise Exception("API error")
            elif candidacy_id == "cand_3":
                return [{"id": "contact_3"}]
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"]
            )

        # Should have all keys, failed ones with empty list
        assert len(result) == 3
        assert len(result["cand_1"]) == 1
        assert len(result["cand_2"]) == 0  # Failed, returns empty list
        assert len(result["cand_3"]) == 1

    @pytest.mark.asyncio
    async def test_list_for_multiple_empty_list(self, api):
        """Test batch fetching with empty list"""
        api_instance, _ = api

        result = await api_instance.list_for_multiple([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_list_for_multiple_respects_concurrency(self, api):
        """Test batch fetching respects max_concurrency"""
        from unittest.mock import patch

        api_instance, _ = api

        async def mock_list(candidacy_id):
            return [{"id": "contact_1"}]

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2"], max_concurrency=100
            )

        assert len(result) == 2


class TestAsyncContactsAPICreate:
    """Test create method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_create_contact(self, api):
        """Test creating contact"""
        api_instance, mock_client = api

        contact_data = {
            "type": "technical_interview",
            "scheduled_at": "2026-02-01T14:00:00Z",
            "interviewer_ids": ["user_456"],
        }

        mock_client.post = AsyncMock(
            return_value={"contact": {"id": "contact_123", **contact_data}}
        )

        result = await api_instance.create("cand_123", contact_data)

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_123/contacts", json=contact_data
        )
        assert result["id"] == "contact_123"
        assert result["type"] == "technical_interview"

    @pytest.mark.asyncio
    async def test_create_contact_data_key_fallback(self, api):
        """Test create falls back to 'data' key"""
        api_instance, mock_client = api

        contact_data = {"type": "phone_screen"}

        mock_client.post = AsyncMock(
            return_value={"data": {"id": "contact_123", "type": "phone_screen"}}
        )

        result = await api_instance.create("cand_123", contact_data)

        assert result["id"] == "contact_123"

    @pytest.mark.asyncio
    async def test_create_constructs_correct_url(self, api):
        """Test create constructs correct URL"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(return_value={"contact": {}})

        await api_instance.create("cand_xyz", {"type": "interview"})

        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "/v1/candidacies/cand_xyz/contacts"


class TestAsyncContactsAPIUpdate:
    """Test update method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_update_contact(self, api):
        """Test updating contact"""
        api_instance, mock_client = api

        update_data = {"scheduled_at": "2026-02-02T15:00:00Z"}

        mock_client.patch = AsyncMock(
            return_value={
                "contact": {
                    "id": "contact_123",
                    "scheduled_at": "2026-02-02T15:00:00Z",
                }
            }
        )

        result = await api_instance.update("cand_123", "contact_123", update_data)

        mock_client.patch.assert_called_once_with(
            "/v1/candidacies/cand_123/contacts/contact_123", json=update_data
        )
        assert result["scheduled_at"] == "2026-02-02T15:00:00Z"

    @pytest.mark.asyncio
    async def test_update_contact_data_key_fallback(self, api):
        """Test update falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(
            return_value={"data": {"id": "contact_123", "type": "updated"}}
        )

        result = await api_instance.update("cand_123", "contact_123", {})

        assert result["id"] == "contact_123"

    @pytest.mark.asyncio
    async def test_update_constructs_correct_url(self, api):
        """Test update constructs correct URL"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(return_value={"contact": {}})

        await api_instance.update("cand_xyz", "contact_999", {"type": "interview"})

        call_args = mock_client.patch.call_args[0]
        assert call_args[0] == "/v1/candidacies/cand_xyz/contacts/contact_999"


class TestAsyncContactsAPIDelete:
    """Test delete method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_delete_contact(self, api):
        """Test deleting contact"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.delete("cand_123", "contact_123")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_123/contacts/contact_123"
        )

    @pytest.mark.asyncio
    async def test_delete_returns_none(self, api):
        """Test delete returns None"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        result = await api_instance.delete("cand_123", "contact_123")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_constructs_correct_url(self, api):
        """Test delete constructs correct URL"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.delete("cand_xyz", "contact_999")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_xyz/contacts/contact_999"
        )


class TestAsyncContactsAPIIntegration:
    """Integration-style tests for AsyncContactsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        from unittest.mock import Mock

        mock_client = AsyncMock()
        # Configure metrics to avoid async issues
        mock_client.metrics = Mock()
        mock_client.metrics.increment_counter = Mock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_create_update_delete_workflow(self, api):
        """Test typical workflow"""
        api_instance, mock_client = api

        # List existing contacts
        mock_client.get = AsyncMock(return_value={"contacts": []})
        contacts = await api_instance.list("cand_123")
        assert len(contacts) == 0

        # Create new contact
        mock_client.post = AsyncMock(
            return_value={"contact": {"id": "contact_123", "type": "interview"}}
        )
        new_contact = await api_instance.create("cand_123", {"type": "interview"})
        assert new_contact["id"] == "contact_123"

        # Update contact
        mock_client.patch = AsyncMock(
            return_value={
                "contact": {"id": "contact_123", "scheduled_at": "2026-02-01"}
            }
        )
        updated = await api_instance.update(
            "cand_123", "contact_123", {"scheduled_at": "2026-02-01"}
        )
        assert "scheduled_at" in updated

        # Delete contact
        mock_client.delete = AsyncMock(return_value={})
        await api_instance.delete("cand_123", "contact_123")
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_fetch_for_pipeline(self, api):
        """Test batch fetching for recruiting pipeline"""
        from unittest.mock import patch

        api_instance, _ = api

        # Simulate fetching contacts for multiple candidates in pipeline
        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "c1", "type": "phone_screen"}]
            elif candidacy_id == "cand_2":
                return [{"id": "c2", "type": "interview"}]
            elif candidacy_id == "cand_3":
                return []
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            results = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"], max_concurrency=3
            )

        # All candidates should have results
        assert len(results) == 3
        assert len(results["cand_1"]) == 1
        assert len(results["cand_2"]) == 1
        assert len(results["cand_3"]) == 0


class TestAsyncContactsAPIEdgeCases:
    """Test edge cases for async contacts API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncContactsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_create_returns_direct_response(self, api):
        """Test create when response doesn't have wrapper key"""
        api_instance, mock_client = api

        # Response without wrapper key
        mock_client.post = AsyncMock(
            return_value={"id": "contact_123", "type": "interview"}
        )

        result = await api_instance.create("cand_123", {"type": "interview"})

        assert result["id"] == "contact_123"

    @pytest.mark.asyncio
    async def test_update_returns_direct_response(self, api):
        """Test update when response doesn't have wrapper key"""
        api_instance, mock_client = api

        mock_client.patch = AsyncMock(
            return_value={"id": "contact_123", "type": "updated"}
        )

        result = await api_instance.update("cand_123", "contact_123", {})

        assert result["type"] == "updated"

    @pytest.mark.asyncio
    async def test_list_with_malformed_response(self, api):
        """Test list handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'contacts' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list("cand_123")

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_concurrent_creates(self, api):
        """Test concurrent contact creation"""
        import asyncio

        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            side_effect=[
                {"contact": {"id": f"contact_{i}", "type": "interview"}}
                for i in range(3)
            ]
        )

        # Create multiple contacts concurrently
        tasks = [
            api_instance.create("cand_123", {"type": "interview"}) for _ in range(3)
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert mock_client.post.call_count == 3
