"""
Tests for HERP Candidacies API Client
"""

from unittest.mock import Mock, patch

import pytest

from src.core.herp.candidates import CandidaciesAPI
from src.core.herp.query_dsl import FieldFilter, FilterOperator, LogicalOperator, Query


class TestCandidaciesAPI:
    """Test CandidaciesAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create CandidaciesAPI instance"""
        return CandidaciesAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = CandidaciesAPI(mock_client)

        assert api.client == mock_client

    def test_list_default_params(self, api, mock_client):
        """Test list with default parameters"""
        mock_client.get.return_value = {"candidacies": [{"id": "1"}, {"id": "2"}]}

        result = api.list()

        mock_client.get.assert_called_once_with(
            "/v1/candidacies", params={"page": 1, "limit": 50}
        )
        assert len(result) == 2
        assert result[0]["id"] == "1"

    def test_list_with_updated_since(self, api, mock_client):
        """Test list with updated_since filter"""
        mock_client.get.return_value = {"candidacies": [{"id": "1"}]}

        api.list(updated_since="2026-01-20T00:00:00Z")

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["updatedSince"] == "2026-01-20T00:00:00Z"

    def test_list_with_custom_page_limit(self, api, mock_client):
        """Test list with custom page and limit"""
        mock_client.get.return_value = {"candidacies": []}

        api.list(page=3, limit=100)

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["page"] == 3
        assert call_args[1]["params"]["limit"] == 100

    def test_list_returns_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key if 'candidacies' not present"""
        mock_client.get.return_value = {"data": [{"id": "1"}]}

        result = api.list()

        assert len(result) == 1

    def test_list_returns_empty_on_no_data(self, api, mock_client):
        """Test list returns empty list when no data"""
        mock_client.get.return_value = {}

        result = api.list()

        assert result == []

    def test_iter_returns_paginator(self, api):
        """Test iter returns HerpPaginator"""
        from src.core.herp.pagination import HerpPaginator

        paginator = api.iter()

        assert isinstance(paginator, HerpPaginator)

    def test_iter_with_updated_since(self, api):
        """Test iter passes updated_since to paginator"""
        paginator = api.iter(updated_since="2026-01-01T00:00:00Z")

        # Paginator should have the fetch_func configured with updated_since
        assert paginator.fetch_func == api.list

    def test_iter_with_custom_limit(self, api):
        """Test iter uses custom limit"""
        paginator = api.iter(limit=200)

        assert paginator.limit == 200

    def test_iter_with_max_pages(self, api):
        """Test iter respects max_pages"""
        paginator = api.iter(max_pages=5)

        assert paginator.max_pages == 5


    def test_stream(self, api):
        """Test stream is alias for iter"""
        from src.core.herp.pagination import HerpPaginator

        stream = api.stream()

        # stream() returns HerpPaginator just like iter()
        assert isinstance(stream, HerpPaginator)

    def test_stream_uses_chunk_size_as_limit(self, api):
        """Test stream uses chunk_size parameter as limit"""
        stream = api.stream(chunk_size=50)

        assert stream.limit == 50

    def test_get_candidacy(self, api, mock_client):
        """Test getting single candidacy"""
        mock_client.get.return_value = {"id": "cand_123", "name": "John Doe"}

        result = api.get("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123")
        assert result["id"] == "cand_123"
        assert result["name"] == "John Doe"

    def test_get_candidacy_not_found(self, api, mock_client):
        """Test getting nonexistent candidacy raises error"""
        mock_client.get.side_effect = Exception("Not found")

        with pytest.raises(Exception, match="Not found"):
            api.get("nonexistent")

    def test_get_candidacy_logs_error(self, api, mock_client):
        """Test get logs error with context"""
        mock_client.get.side_effect = Exception("API Error")

        with patch("src.core.herp.candidates.logger") as mock_logger:
            with pytest.raises(Exception):
                api.get("cand_123")

            # Should log error
            assert mock_logger.error.called

    def test_create_candidacy(self, api, mock_client):
        """Test creating candidacy"""
        candidacy_data = {"name": "John Doe", "email": "john@example.com"}
        mock_client.post.return_value = {"id": "cand_new", **candidacy_data}

        result = api.create(candidacy_data)

        mock_client.post.assert_called_once_with(
            "/v1/candidacies", json=candidacy_data
        )
        assert result["id"] == "cand_new"
        assert result["name"] == "John Doe"

    def test_update_step(self, api, mock_client):
        """Test updating candidacy step"""
        mock_client.patch.return_value = {"id": "cand_123", "step": "interview"}

        result = api.update_step("cand_123", "interview")

        mock_client.patch.assert_called_once_with(
            "/v1/candidacies/cand_123/step", json={"step": "interview"}
        )
        assert result["step"] == "interview"

    def test_terminate_candidacy(self, api, mock_client):
        """Test terminating candidacy"""
        mock_client.patch.return_value = {
            "id": "cand_123",
            "terminated": True,
            "terminationReason": "withdrew",
        }

        result = api.terminate("cand_123", "withdrew")

        mock_client.patch.assert_called_once_with(
            "/v1/candidacies/cand_123/termination",
            json={"terminationReason": "withdrew"},
        )
        assert result["terminated"] is True


class TestCandidaciesSearch:
    """Test search functionality"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return CandidaciesAPI(mock_client)

    @pytest.fixture
    def sample_candidacies(self):
        """Sample candidacies for testing"""
        return [
            {
                "id": "1",
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
                "createdAt": "2026-01-15T00:00:00Z",
            },
            {
                "id": "2",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "status": "inactive",
                "createdAt": "2026-01-20T00:00:00Z",
            },
            {
                "id": "3",
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "status": "active",
                "createdAt": "2026-01-25T00:00:00Z",
            },
        ]

    def test_search_with_query_dsl(self, api, mock_client, sample_candidacies):
        """Test search with Query DSL"""
        # Mock fetch_all to return sample data
        with patch.object(api, 'fetch_all', return_value=sample_candidacies):
            query = Query().equals("status", "active")

            results = api.search(query)

            # Should return only active candidacies
            assert len(results) == 2
            assert all(c["status"] == "active" for c in results)

    def test_search_with_legacy_filters(self, api, mock_client, sample_candidacies):
        """Test search with legacy filters"""
        with patch.object(api, 'fetch_all', return_value=sample_candidacies):
            results = api.search(name="John")

            # Should return candidacies with "John" in name
            assert len(results) == 2  # John Doe and Bob Johnson
            assert any("John" in c["name"] for c in results)

    def test_search_with_limit(self, api, mock_client, sample_candidacies):
        """Test search respects limit"""
        with patch.object(api, 'fetch_all', return_value=sample_candidacies):
            results = api.search(status="active", limit=1)

            # Should return only 1 result
            assert len(results) == 1

    def test_search_no_results(self, api, mock_client, sample_candidacies):
        """Test search with no matching results"""
        with patch.object(api, 'fetch_all', return_value=sample_candidacies):
            query = Query().equals("status", "deleted")

            results = api.search(query)

            assert len(results) == 0

    def test_search_logs_result_count(self, api, mock_client, sample_candidacies):
        """Test search logs number of results"""
        with patch.object(api, 'fetch_all', return_value=sample_candidacies):
            with patch("src.core.herp.candidates.logger") as mock_logger:
                api.search(status="active")

                # Should log info about result count
                assert mock_logger.info.called


class TestQueryMatching:
    """Test query matching logic"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return CandidaciesAPI(Mock())

    def test_matches_query_empty(self, api):
        """Test empty query matches everything"""
        query = Query()
        candidacy = {"id": "1", "name": "Test"}

        assert api._matches_query(query, candidacy) is True

    def test_matches_query_and_operator(self, api):
        """Test AND logical operator"""
        query = Query()
        query.logical_operator = LogicalOperator.AND
        query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "active"))
        query.filters.append(FieldFilter("name", FilterOperator.CONTAINS, "John"))

        candidacy1 = {"status": "active", "name": "John Doe"}
        candidacy2 = {"status": "active", "name": "Jane Smith"}

        assert api._matches_query(query, candidacy1) is True
        assert api._matches_query(query, candidacy2) is False

    def test_matches_query_or_operator(self, api):
        """Test OR logical operator"""
        query = Query()
        query.logical_operator = LogicalOperator.OR
        query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "active"))
        query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "pending"))

        candidacy1 = {"status": "active"}
        candidacy2 = {"status": "pending"}
        candidacy3 = {"status": "inactive"}

        assert api._matches_query(query, candidacy1) is True
        assert api._matches_query(query, candidacy2) is True
        assert api._matches_query(query, candidacy3) is False

    def test_matches_query_negation(self, api):
        """Test query negation"""
        query = Query()
        query.negated = True
        query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "active"))

        candidacy1 = {"status": "active"}
        candidacy2 = {"status": "inactive"}

        assert api._matches_query(query, candidacy1) is False
        assert api._matches_query(query, candidacy2) is True

    def test_matches_query_nested(self, api):
        """Test nested query"""
        inner_query = Query()
        inner_query.logical_operator = LogicalOperator.OR
        inner_query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "active"))
        inner_query.filters.append(FieldFilter("status", FilterOperator.EQUALS, "pending"))

        outer_query = Query()
        outer_query.logical_operator = LogicalOperator.AND
        outer_query.filters.append(inner_query)
        outer_query.filters.append(FieldFilter("name", FilterOperator.CONTAINS, "John"))

        candidacy = {"status": "active", "name": "John Doe"}

        assert api._matches_query(outer_query, candidacy) is True


class TestFilterMatching:
    """Test filter matching operators"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return CandidaciesAPI(Mock())

    def test_filter_equals(self, api):
        """Test EQUALS operator"""
        filter = FieldFilter("status", FilterOperator.EQUALS, "active")
        candidacy = {"status": "active"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_not_equals(self, api):
        """Test NOT_EQUALS operator"""
        filter = FieldFilter("status", FilterOperator.NOT_EQUALS, "active")
        candidacy = {"status": "inactive"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_contains(self, api):
        """Test CONTAINS operator"""
        filter = FieldFilter("name", FilterOperator.CONTAINS, "John")
        candidacy = {"name": "John Doe"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_not_contains(self, api):
        """Test NOT_CONTAINS operator"""
        filter = FieldFilter("name", FilterOperator.NOT_CONTAINS, "Jane")
        candidacy = {"name": "John Doe"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_starts_with(self, api):
        """Test STARTS_WITH operator"""
        filter = FieldFilter("name", FilterOperator.STARTS_WITH, "John")
        candidacy = {"name": "John Doe"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_ends_with(self, api):
        """Test ENDS_WITH operator"""
        filter = FieldFilter("email", FilterOperator.ENDS_WITH, "@example.com")
        candidacy = {"email": "test@example.com"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_in(self, api):
        """Test IN operator"""
        filter = FieldFilter("status", FilterOperator.IN, ["active", "pending"])
        candidacy = {"status": "active"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_not_in(self, api):
        """Test NOT_IN operator"""
        filter = FieldFilter("status", FilterOperator.NOT_IN, ["active", "pending"])
        candidacy = {"status": "rejected"}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_greater_than(self, api):
        """Test GREATER_THAN operator"""
        filter = FieldFilter("score", FilterOperator.GREATER_THAN, 80)
        candidacy = {"score": 95}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_greater_than_or_equal(self, api):
        """Test GREATER_THAN_OR_EQUAL operator"""
        filter = FieldFilter("score", FilterOperator.GREATER_THAN_OR_EQUAL, 80)
        candidacy1 = {"score": 80}
        candidacy2 = {"score": 95}

        assert api._matches_filter(filter, candidacy1) is True
        assert api._matches_filter(filter, candidacy2) is True

    def test_filter_less_than(self, api):
        """Test LESS_THAN operator"""
        filter = FieldFilter("score", FilterOperator.LESS_THAN, 50)
        candidacy = {"score": 30}

        assert api._matches_filter(filter, candidacy) is True

    def test_filter_less_than_or_equal(self, api):
        """Test LESS_THAN_OR_EQUAL operator"""
        filter = FieldFilter("score", FilterOperator.LESS_THAN_OR_EQUAL, 50)
        candidacy1 = {"score": 50}
        candidacy2 = {"score": 30}

        assert api._matches_filter(filter, candidacy1) is True
        assert api._matches_filter(filter, candidacy2) is True

    def test_filter_between(self, api):
        """Test BETWEEN operator"""
        filter = FieldFilter("score", FilterOperator.BETWEEN, [70, 90])
        candidacy1 = {"score": 80}
        candidacy2 = {"score": 60}

        assert api._matches_filter(filter, candidacy1) is True
        assert api._matches_filter(filter, candidacy2) is False

    def test_filter_is_null(self, api):
        """Test IS_NULL operator"""
        filter = FieldFilter("terminationReason", FilterOperator.IS_NULL, None)
        candidacy1 = {"terminationReason": None}
        candidacy2 = {"terminationReason": ""}
        candidacy3 = {"terminationReason": "withdrew"}

        assert api._matches_filter(filter, candidacy1) is True
        assert api._matches_filter(filter, candidacy2) is True
        assert api._matches_filter(filter, candidacy3) is False

    def test_filter_is_not_null(self, api):
        """Test IS_NOT_NULL operator"""
        filter = FieldFilter("email", FilterOperator.IS_NOT_NULL, None)
        candidacy1 = {"email": "test@example.com"}
        candidacy2 = {"email": None}

        assert api._matches_filter(filter, candidacy1) is True
        assert api._matches_filter(filter, candidacy2) is False

    def test_filter_contains_none_value(self, api):
        """Test CONTAINS with None field value"""
        filter = FieldFilter("name", FilterOperator.CONTAINS, "John")
        candidacy = {"name": None}

        assert api._matches_filter(filter, candidacy) is False

    def test_filter_greater_than_none_value(self, api):
        """Test GREATER_THAN with None field value"""
        filter = FieldFilter("score", FilterOperator.GREATER_THAN, 50)
        candidacy = {"score": None}

        assert api._matches_filter(filter, candidacy) is False


class TestLegacyFilters:
    """Test legacy filter matching"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return CandidaciesAPI(Mock())

    @pytest.fixture
    def sample_candidacies(self):
        """Sample candidacies"""
        return [
            {"id": "1", "name": "John Doe", "email": "john@example.com", "status": "active"},
            {"id": "2", "name": "Jane Smith", "email": "jane@example.com", "status": "inactive"},
            {"id": "3", "name": "Bob Johnson", "email": "bob@example.com", "status": "active"},
        ]

    def test_legacy_filter_name(self, api, sample_candidacies):
        """Test legacy name filter"""
        results = api._apply_legacy_filters(sample_candidacies, {"name": "John"})

        assert len(results) == 2  # John Doe and Bob Johnson

    def test_legacy_filter_email(self, api, sample_candidacies):
        """Test legacy email filter"""
        results = api._apply_legacy_filters(sample_candidacies, {"email": "john@example.com"})

        assert len(results) == 1
        assert results[0]["name"] == "John Doe"

    def test_legacy_filter_status_single(self, api, sample_candidacies):
        """Test legacy status filter (single value)"""
        results = api._apply_legacy_filters(sample_candidacies, {"status": "active"})

        assert len(results) == 2
        assert all(c["status"] == "active" for c in results)

    def test_legacy_filter_status_list(self, api, sample_candidacies):
        """Test legacy status filter (list of values)"""
        results = api._apply_legacy_filters(
            sample_candidacies, {"status": ["active", "inactive"]}
        )

        assert len(results) == 3

    def test_legacy_filter_custom_field(self, api):
        """Test legacy filter on custom field"""
        candidacies = [
            {"id": "1", "customField": "valueA"},
            {"id": "2", "customField": "valueB"},
        ]

        results = api._apply_legacy_filters(candidacies, {"customField": "valueA"})

        assert len(results) == 1
        assert results[0]["id"] == "1"

    def test_legacy_filter_multiple(self, api, sample_candidacies):
        """Test multiple legacy filters (AND logic)"""
        results = api._apply_legacy_filters(
            sample_candidacies, {"status": "active", "name": "Doe"}
        )

        # Should match both filters (status=active AND name contains "Doe")
        assert len(results) == 1
        assert results[0]["name"] == "John Doe"

    def test_legacy_filter_no_matches(self, api, sample_candidacies):
        """Test legacy filter with no matches"""
        results = api._apply_legacy_filters(sample_candidacies, {"name": "Nonexistent"})

        assert len(results) == 0
