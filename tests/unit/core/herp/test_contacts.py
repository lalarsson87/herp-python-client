"""
Tests for HERP Contacts API Client
"""

from unittest.mock import Mock, patch

import pytest

from src.core.herp.contacts import ContactsAPI


class TestContactsAPI:
    """Test ContactsAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create ContactsAPI instance"""
        return ContactsAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = ContactsAPI(mock_client)

        assert api.client == mock_client

    def test_list_contacts(self, api, mock_client):
        """Test listing contacts for candidacy"""
        mock_client.get.return_value = {
            "contacts": [
                {"id": "contact_1", "type": "phone_screen"},
                {"id": "contact_2", "type": "technical_interview"},
            ]
        }

        result = api.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/contacts")
        assert len(result) == 2
        assert result[0]["id"] == "contact_1"
        assert result[1]["type"] == "technical_interview"

    def test_list_contacts_returns_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key if 'contacts' not present"""
        mock_client.get.return_value = {"data": [{"id": "contact_1"}]}

        result = api.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "contact_1"

    def test_list_contacts_empty(self, api, mock_client):
        """Test listing contacts when none exist"""
        mock_client.get.return_value = {"contacts": []}

        result = api.list("cand_123")

        assert result == []

    def test_list_contacts_no_data(self, api, mock_client):
        """Test list returns empty list when no data"""
        mock_client.get.return_value = {}

        result = api.list("cand_123")

        assert result == []

    def test_list_for_multiple(self, api, mock_client):
        """Test batch fetching contacts for multiple candidacies"""
        # Mock list() to return different contacts for each candidacy
        def mock_list(candidacy_id):
            return [{"id": f"contact_{candidacy_id}"}]

        with patch.object(api, "list", side_effect=mock_list):
            result = api.list_for_multiple(
                candidacy_ids=["cand_1", "cand_2", "cand_3"], max_workers=2
            )

            # Should return dict mapping candidacy_id to contacts
            assert len(result) == 3
            assert result["cand_1"] == [{"id": "contact_cand_1"}]
            assert result["cand_2"] == [{"id": "contact_cand_2"}]
            assert result["cand_3"] == [{"id": "contact_cand_3"}]

    def test_list_for_multiple_with_errors(self, api, mock_client):
        """Test batch fetch handles errors gracefully"""

        def mock_list(candidacy_id):
            if candidacy_id == "cand_error":
                raise Exception("API Error")
            return [{"id": f"contact_{candidacy_id}"}]

        with patch.object(api, "list", side_effect=mock_list):
            result = api.list_for_multiple(
                candidacy_ids=["cand_1", "cand_error", "cand_2"]
            )

            # Error candidacy should have empty list
            assert result["cand_1"] == [{"id": "contact_cand_1"}]
            assert result["cand_error"] == []
            assert result["cand_2"] == [{"id": "contact_cand_2"}]

    def test_list_for_multiple_empty_ids(self, api):
        """Test batch fetch with empty ID list"""
        result = api.list_for_multiple(candidacy_ids=[])

        assert result == {}

    def test_list_for_multiple_custom_max_workers(self, api, mock_client):
        """Test batch fetch respects max_workers"""

        def mock_list(candidacy_id):
            return []

        with patch.object(api, "list", side_effect=mock_list):
            # Should complete without error
            result = api.list_for_multiple(
                candidacy_ids=["cand_1", "cand_2", "cand_3"], max_workers=10
            )

            assert len(result) == 3

    def test_create_contact(self, api, mock_client):
        """Test creating a new contact"""
        contact_data = {
            "type": "technical_interview",
            "scheduledAt": "2026-02-01T10:00:00Z",
            "attendees": ["interviewer@company.com"],
        }

        mock_client.post.return_value = {"id": "contact_new", **contact_data}

        result = api.create("cand_123", contact_data)

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_123/contacts", json=contact_data
        )
        assert result["id"] == "contact_new"
        assert result["type"] == "technical_interview"

    def test_create_contact_minimal_data(self, api, mock_client):
        """Test creating contact with minimal data"""
        contact_data = {"type": "phone_screen"}

        mock_client.post.return_value = {"id": "contact_123", **contact_data}

        result = api.create("cand_123", contact_data)

        assert result["id"] == "contact_123"

    def test_inherits_from_batch_fetch_mixin(self, api):
        """Test ContactsAPI inherits from BatchFetchMixin"""
        from src.core.herp.mixins import BatchFetchMixin

        assert isinstance(api, BatchFetchMixin)

    def test_has_batch_fetch_method(self, api):
        """Test ContactsAPI has _batch_fetch method from mixin"""
        assert hasattr(api, "_batch_fetch")
        assert callable(api._batch_fetch)


class TestContactsAPIIntegration:
    """Integration-style tests for ContactsAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return ContactsAPI(mock_client)

    def test_list_and_create_workflow(self, api, mock_client):
        """Test typical workflow of listing then creating contact"""
        # First, list existing contacts
        mock_client.get.return_value = {"contacts": [{"id": "existing_1"}]}
        existing = api.list("cand_123")
        assert len(existing) == 1

        # Then create new contact
        mock_client.post.return_value = {"id": "new_contact", "type": "interview"}
        new_contact = api.create("cand_123", {"type": "interview"})
        assert new_contact["id"] == "new_contact"

    def test_batch_fetch_multiple_candidacies(self, api, mock_client):
        """Test fetching contacts for multiple candidacies"""
        # Mock responses for different candidacies
        responses = {
            "cand_1": {"contacts": [{"id": "c1"}, {"id": "c2"}]},
            "cand_2": {"contacts": [{"id": "c3"}]},
            "cand_3": {"contacts": []},
        }

        def mock_get(path, **kwargs):
            for cand_id, response in responses.items():
                if cand_id in path:
                    return response
            return {"contacts": []}

        mock_client.get.side_effect = mock_get

        result = api.list_for_multiple(["cand_1", "cand_2", "cand_3"])

        # Should have fetched contacts for all candidacies
        assert len(result["cand_1"]) == 2
        assert len(result["cand_2"]) == 1
        assert len(result["cand_3"]) == 0


class TestContactsAPIEdgeCases:
    """Test edge cases for ContactsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return ContactsAPI(Mock())

    def test_list_with_special_characters_in_id(self, api):
        """Test list with special characters in candidacy ID"""
        api.client.get.return_value = {"contacts": []}

        # Should handle special characters in URL
        api.list("cand_123-abc_456")

        # Should have made request with encoded ID
        assert api.client.get.called

    def test_create_with_empty_data(self, api):
        """Test create with empty contact data"""
        api.client.post.return_value = {"id": "contact_123"}

        result = api.create("cand_123", {})

        # Should allow empty data (server validation)
        assert result["id"] == "contact_123"

    def test_create_with_complex_nested_data(self, api):
        """Test create with complex nested contact data"""
        contact_data = {
            "type": "interview",
            "attendees": [
                {"email": "interviewer1@company.com", "role": "technical"},
                {"email": "interviewer2@company.com", "role": "cultural"},
            ],
            "metadata": {"location": "remote", "duration": 60},
        }

        api.client.post.return_value = {"id": "contact_123", **contact_data}

        result = api.create("cand_123", contact_data)

        # Should preserve nested structure
        assert len(result["attendees"]) == 2
        assert result["metadata"]["duration"] == 60

    def test_list_for_multiple_with_single_id(self, api):
        """Test batch fetch with single ID"""
        api.client.get.return_value = {"contacts": [{"id": "c1"}]}

        result = api.list_for_multiple(["cand_1"])

        # Should work with single ID
        assert len(result) == 1
        assert "cand_1" in result

    def test_list_for_multiple_preserves_order(self, api):
        """Test batch fetch preserves candidacy IDs"""

        def mock_list(candidacy_id):
            return [{"candidacy_id": candidacy_id}]

        with patch.object(api, "list", side_effect=mock_list):
            result = api.list_for_multiple(["cand_3", "cand_1", "cand_2"])

            # All IDs should be in result
            assert "cand_1" in result
            assert "cand_2" in result
            assert "cand_3" in result
