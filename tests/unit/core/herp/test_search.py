"""
Tests for HERP Search Functionality
"""

import pytest

from src.core.herp.search import (
    SearchField,
    SearchFilter,
    SearchHelper,
    SearchOperator,
    SearchQuery,
    SortOrder,
)


class TestSearchFilter:
    """Test SearchFilter class"""

    def test_equals_operator(self):
        """Test EQUALS operator"""
        filter_obj = SearchFilter(SearchField.NAME, SearchOperator.EQUALS, "John Doe")

        assert filter_obj.matches({"name": "John Doe"}) is True
        assert filter_obj.matches({"name": "Jane Doe"}) is False
        assert filter_obj.matches({"name": None}) is False

    def test_not_equals_operator(self):
        """Test NOT_EQUALS operator"""
        filter_obj = SearchFilter(SearchField.STATUS, SearchOperator.NOT_EQUALS, "inactive")

        assert filter_obj.matches({"status": "active"}) is True
        assert filter_obj.matches({"status": "inactive"}) is False

    def test_contains_operator(self):
        """Test CONTAINS operator (case-insensitive)"""
        filter_obj = SearchFilter(SearchField.NAME, SearchOperator.CONTAINS, "john")

        assert filter_obj.matches({"name": "John Doe"}) is True
        assert filter_obj.matches({"name": "JOHN SMITH"}) is True
        assert filter_obj.matches({"name": "Jane Doe"}) is False
        assert filter_obj.matches({"name": None}) is False

    def test_starts_with_operator(self):
        """Test STARTS_WITH operator (case-insensitive)"""
        filter_obj = SearchFilter(SearchField.NAME, SearchOperator.STARTS_WITH, "john")

        assert filter_obj.matches({"name": "John Doe"}) is True
        assert filter_obj.matches({"name": "JOHN SMITH"}) is True
        assert filter_obj.matches({"name": "Bob Johnson"}) is False
        assert filter_obj.matches({"name": None}) is False

    def test_ends_with_operator(self):
        """Test ENDS_WITH operator (case-insensitive)"""
        filter_obj = SearchFilter(SearchField.EMAIL, SearchOperator.ENDS_WITH, "@company.com")

        assert filter_obj.matches({"email": "john@company.com"}) is True
        assert filter_obj.matches({"email": "JANE@COMPANY.COM"}) is True
        assert filter_obj.matches({"email": "john@other.com"}) is False
        assert filter_obj.matches({"email": None}) is False

    def test_in_operator(self):
        """Test IN operator"""
        filter_obj = SearchFilter(SearchField.STATUS, SearchOperator.IN, ["active", "pending"])

        assert filter_obj.matches({"status": "active"}) is True
        assert filter_obj.matches({"status": "pending"}) is True
        assert filter_obj.matches({"status": "inactive"}) is False

    def test_not_in_operator(self):
        """Test NOT_IN operator"""
        filter_obj = SearchFilter(SearchField.STATUS, SearchOperator.NOT_IN, ["inactive", "rejected"])

        assert filter_obj.matches({"status": "active"}) is True
        assert filter_obj.matches({"status": "inactive"}) is False

    def test_greater_than_operator(self):
        """Test GREATER_THAN operator"""
        filter_obj = SearchFilter(SearchField.CREATED_AT, SearchOperator.GREATER_THAN, "2026-01-15")

        assert filter_obj.matches({"created_at": "2026-01-20"}) is True
        assert filter_obj.matches({"created_at": "2026-01-10"}) is False
        assert filter_obj.matches({"created_at": None}) is False

    def test_less_than_operator(self):
        """Test LESS_THAN operator"""
        filter_obj = SearchFilter(SearchField.CREATED_AT, SearchOperator.LESS_THAN, "2026-01-15")

        assert filter_obj.matches({"created_at": "2026-01-10"}) is True
        assert filter_obj.matches({"created_at": "2026-01-20"}) is False
        assert filter_obj.matches({"created_at": None}) is False

    def test_greater_or_equal_operator(self):
        """Test GREATER_OR_EQUAL operator"""
        filter_obj = SearchFilter(SearchField.CREATED_AT, SearchOperator.GREATER_OR_EQUAL, "2026-01-15")

        assert filter_obj.matches({"created_at": "2026-01-15"}) is True
        assert filter_obj.matches({"created_at": "2026-01-20"}) is True
        assert filter_obj.matches({"created_at": "2026-01-10"}) is False

    def test_less_or_equal_operator(self):
        """Test LESS_OR_EQUAL operator"""
        filter_obj = SearchFilter(SearchField.CREATED_AT, SearchOperator.LESS_OR_EQUAL, "2026-01-15")

        assert filter_obj.matches({"created_at": "2026-01-15"}) is True
        assert filter_obj.matches({"created_at": "2026-01-10"}) is True
        assert filter_obj.matches({"created_at": "2026-01-20"}) is False

    def test_is_null_operator(self):
        """Test IS_NULL operator"""
        filter_obj = SearchFilter(SearchField.PHONE, SearchOperator.IS_NULL, None)

        assert filter_obj.matches({"phone": None}) is True
        assert filter_obj.matches({"phone": "555-1234"}) is False
        assert filter_obj.matches({}) is True  # Missing field is None

    def test_is_not_null_operator(self):
        """Test IS_NOT_NULL operator"""
        filter_obj = SearchFilter(SearchField.PHONE, SearchOperator.IS_NOT_NULL, None)

        assert filter_obj.matches({"phone": "555-1234"}) is True
        assert filter_obj.matches({"phone": None}) is False
        assert filter_obj.matches({}) is False  # Missing field is None

    def test_unknown_operator_raises_error(self):
        """Test unknown operator raises ValueError"""
        # Create filter with mock operator
        filter_obj = SearchFilter(SearchField.NAME, SearchOperator.EQUALS, "test")
        filter_obj.operator = "unknown_operator"

        with pytest.raises(ValueError, match="Unknown operator"):
            filter_obj.matches({"name": "test"})


class TestSearchQuery:
    """Test SearchQuery class"""

    def test_add_filter_returns_self(self):
        """Test add_filter returns self for chaining"""
        query = SearchQuery()
        result = query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")

        assert result is query
        assert len(query.filters) == 1

    def test_sort_by_returns_self(self):
        """Test sort_by returns self for chaining"""
        query = SearchQuery()
        result = query.sort_by(SearchField.CREATED_AT, descending=True)

        assert result is query
        assert len(query.sort_orders) == 1

    def test_limit_returns_self(self):
        """Test limit returns self for chaining"""
        query = SearchQuery()
        result = query.limit(50)

        assert result is query
        assert query.max_results == 50

    def test_method_chaining(self):
        """Test fluent interface with method chaining"""
        query = (
            SearchQuery()
            .add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")
            .add_filter(SearchField.STATUS, SearchOperator.IN, ["active", "pending"])
            .sort_by(SearchField.CREATED_AT, descending=True)
            .limit(50)
        )

        assert len(query.filters) == 2
        assert len(query.sort_orders) == 1
        assert query.max_results == 50

    def test_matches_single_filter(self):
        """Test matches with single filter"""
        query = SearchQuery()
        query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")

        assert query.matches({"name": "John Doe"}) is True
        assert query.matches({"name": "Jane Doe"}) is False

    def test_matches_multiple_filters_all_must_match(self):
        """Test matches requires ALL filters to match (AND logic)"""
        query = SearchQuery()
        query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")
        query.add_filter(SearchField.STATUS, SearchOperator.EQUALS, "active")

        assert query.matches({"name": "John Doe", "status": "active"}) is True
        assert query.matches({"name": "John Doe", "status": "inactive"}) is False
        assert query.matches({"name": "Jane Doe", "status": "active"}) is False

    def test_apply_filters_records(self):
        """Test apply filters records correctly"""
        records = [
            {"name": "John Doe", "status": "active"},
            {"name": "Jane Doe", "status": "active"},
            {"name": "Bob Smith", "status": "inactive"},
        ]

        query = SearchQuery()
        query.add_filter(SearchField.STATUS, SearchOperator.EQUALS, "active")

        results = query.apply(records)

        assert len(results) == 2
        assert results[0]["name"] == "John Doe"
        assert results[1]["name"] == "Jane Doe"

    def test_apply_sorts_results(self):
        """Test apply sorts results"""
        records = [
            {"name": "Charlie", "created_at": "2026-01-20"},
            {"name": "Alice", "created_at": "2026-01-15"},
            {"name": "Bob", "created_at": "2026-01-25"},
        ]

        query = SearchQuery()
        query.sort_by(SearchField.CREATED_AT, descending=True)

        results = query.apply(records)

        assert results[0]["name"] == "Bob"  # 2026-01-25
        assert results[1]["name"] == "Charlie"  # 2026-01-20
        assert results[2]["name"] == "Alice"  # 2026-01-15

    def test_apply_sorts_ascending(self):
        """Test apply sorts ascending by default"""
        records = [
            {"name": "Charlie"},
            {"name": "Alice"},
            {"name": "Bob"},
        ]

        query = SearchQuery()
        query.sort_by(SearchField.NAME)

        results = query.apply(records)

        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
        assert results[2]["name"] == "Charlie"

    def test_apply_multiple_sort_orders(self):
        """Test apply with multiple sort orders"""
        records = [
            {"status": "active", "name": "Charlie"},
            {"status": "active", "name": "Alice"},
            {"status": "inactive", "name": "Bob"},
        ]

        query = SearchQuery()
        query.sort_by(SearchField.STATUS)  # First by status
        query.sort_by(SearchField.NAME)  # Then by name

        results = query.apply(records)

        # Should be sorted by status first, then name
        assert results[0]["status"] == "active"
        assert results[0]["name"] == "Alice"
        assert results[1]["status"] == "active"
        assert results[1]["name"] == "Charlie"

    def test_apply_limits_results(self):
        """Test apply limits number of results"""
        records = [{"id": i} for i in range(100)]

        query = SearchQuery()
        query.limit(10)

        results = query.apply(records)

        assert len(results) == 10

    def test_apply_filter_sort_limit_together(self):
        """Test apply with filter, sort, and limit together"""
        records = [
            {"name": "John", "status": "active", "created_at": "2026-01-20"},
            {"name": "Jane", "status": "active", "created_at": "2026-01-15"},
            {"name": "Bob", "status": "active", "created_at": "2026-01-25"},
            {"name": "Alice", "status": "inactive", "created_at": "2026-01-30"},
        ]

        query = SearchQuery()
        query.add_filter(SearchField.STATUS, SearchOperator.EQUALS, "active")
        query.sort_by(SearchField.CREATED_AT, descending=True)
        query.limit(2)

        results = query.apply(records)

        assert len(results) == 2
        assert results[0]["name"] == "Bob"  # Most recent active
        assert results[1]["name"] == "John"  # Second most recent active

    def test_apply_empty_records(self):
        """Test apply with empty records list"""
        query = SearchQuery()
        query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")

        results = query.apply([])

        assert results == []

    def test_apply_no_filters(self):
        """Test apply with no filters returns all records"""
        records = [{"id": 1}, {"id": 2}, {"id": 3}]

        query = SearchQuery()

        results = query.apply(records)

        assert len(results) == 3

    def test_apply_handles_missing_sort_fields(self):
        """Test apply handles records with missing sort fields"""
        records = [
            {"name": "Alice", "created_at": "2026-01-15"},
            {"name": "Bob"},  # Missing created_at
            {"name": "Charlie", "created_at": "2026-01-20"},
        ]

        query = SearchQuery()
        query.sort_by(SearchField.CREATED_AT)

        results = query.apply(records)

        # Record with missing field should be treated as empty string
        assert results[0]["name"] == "Bob"  # Empty string sorts first
        assert results[1]["created_at"] == "2026-01-15"


class TestSearchHelper:
    """Test SearchHelper class"""

    def test_by_name_contains(self):
        """Test by_name with contains (default)"""
        query = SearchHelper.by_name("John")

        assert len(query.filters) == 1
        assert query.filters[0].field == SearchField.NAME
        assert query.filters[0].operator == SearchOperator.CONTAINS
        assert query.filters[0].value == "John"

    def test_by_name_exact(self):
        """Test by_name with exact match"""
        query = SearchHelper.by_name("John Doe", exact=True)

        assert len(query.filters) == 1
        assert query.filters[0].operator == SearchOperator.EQUALS

    def test_by_email(self):
        """Test by_email"""
        query = SearchHelper.by_email("john@example.com")

        assert len(query.filters) == 1
        assert query.filters[0].field == SearchField.EMAIL
        assert query.filters[0].operator == SearchOperator.EQUALS
        assert query.filters[0].value == "john@example.com"

    def test_by_status(self):
        """Test by_status"""
        query = SearchHelper.by_status(["active", "pending"])

        assert len(query.filters) == 1
        assert query.filters[0].field == SearchField.STATUS
        assert query.filters[0].operator == SearchOperator.IN
        assert query.filters[0].value == ["active", "pending"]

    def test_created_since(self):
        """Test created_since"""
        query = SearchHelper.created_since("2026-01-01T00:00:00Z", limit=100)

        assert len(query.filters) == 1
        assert query.filters[0].field == SearchField.CREATED_AT
        assert query.filters[0].operator == SearchOperator.GREATER_OR_EQUAL
        assert query.filters[0].value == "2026-01-01T00:00:00Z"

        assert len(query.sort_orders) == 1
        assert query.sort_orders[0].field == SearchField.CREATED_AT
        assert query.sort_orders[0].descending is True

        assert query.max_results == 100

    def test_created_since_no_limit(self):
        """Test created_since without limit"""
        query = SearchHelper.created_since("2026-01-01T00:00:00Z")

        assert query.max_results is None

    def test_updated_since(self):
        """Test updated_since"""
        query = SearchHelper.updated_since("2026-01-26T00:00:00Z", limit=50)

        assert len(query.filters) == 1
        assert query.filters[0].field == SearchField.UPDATED_AT
        assert query.filters[0].operator == SearchOperator.GREATER_OR_EQUAL

        assert len(query.sort_orders) == 1
        assert query.sort_orders[0].field == SearchField.UPDATED_AT
        assert query.sort_orders[0].descending is True

        assert query.max_results == 50

    def test_updated_since_no_limit(self):
        """Test updated_since without limit"""
        query = SearchHelper.updated_since("2026-01-26T00:00:00Z")

        assert query.max_results is None


class TestSearchIntegration:
    """Integration-style tests for search functionality"""

    def test_complex_search_scenario(self):
        """Test complex search with multiple filters and sort"""
        records = [
            {"name": "John Doe", "email": "john@company.com", "status": "active", "created_at": "2026-01-20"},
            {"name": "Jane Smith", "email": "jane@company.com", "status": "active", "created_at": "2026-01-15"},
            {"name": "Bob Johnson", "email": "bob@other.com", "status": "active", "created_at": "2026-01-25"},
            {"name": "Alice Brown", "email": "alice@company.com", "status": "inactive", "created_at": "2026-01-30"},
        ]

        # Search for active candidates from company.com, sorted by creation date
        query = (
            SearchQuery()
            .add_filter(SearchField.STATUS, SearchOperator.EQUALS, "active")
            .add_filter(SearchField.EMAIL, SearchOperator.ENDS_WITH, "@company.com")
            .sort_by(SearchField.CREATED_AT, descending=True)
        )

        results = query.apply(records)

        assert len(results) == 2  # John and Jane
        assert results[0]["name"] == "John Doe"  # Most recent
        assert results[1]["name"] == "Jane Smith"

    def test_helper_methods_work_with_apply(self):
        """Test helper methods create queries that work with apply"""
        records = [
            {"name": "John Doe", "created_at": "2026-01-20"},
            {"name": "Jane Smith", "created_at": "2026-01-15"},
            {"name": "Bob Johnson", "created_at": "2026-01-10"},
        ]

        query = SearchHelper.created_since("2026-01-12T00:00:00Z", limit=2)
        results = query.apply(records)

        assert len(results) == 2
        assert results[0]["name"] == "John Doe"  # Most recent
        assert results[1]["name"] == "Jane Smith"


class TestSearchEdgeCases:
    """Test edge cases for search functionality"""

    def test_filter_with_unicode_values(self):
        """Test filter with unicode characters"""
        filter_obj = SearchFilter(SearchField.NAME, SearchOperator.CONTAINS, "José")

        assert filter_obj.matches({"name": "José García"}) is True
        assert filter_obj.matches({"name": "John Doe"}) is False

    def test_filter_with_numeric_values(self):
        """Test filter with numeric comparisons"""
        filter_obj = SearchFilter(SearchField.CREATED_AT, SearchOperator.GREATER_THAN, 100)

        assert filter_obj.matches({"created_at": 150}) is True
        assert filter_obj.matches({"created_at": 50}) is False

    def test_query_with_no_sort_orders(self):
        """Test query without sort orders"""
        records = [{"id": 3}, {"id": 1}, {"id": 2}]

        query = SearchQuery()

        results = query.apply(records)

        # Should maintain original order
        assert results[0]["id"] == 3
        assert results[1]["id"] == 1
        assert results[2]["id"] == 2

    def test_empty_filter_value_for_in_operator(self):
        """Test IN operator with empty list"""
        filter_obj = SearchFilter(SearchField.STATUS, SearchOperator.IN, [])

        assert filter_obj.matches({"status": "active"}) is False
        assert filter_obj.matches({"status": "anything"}) is False

    def test_sort_order_dataclass(self):
        """Test SortOrder dataclass"""
        sort_order = SortOrder(SearchField.NAME, descending=True)

        assert sort_order.field == SearchField.NAME
        assert sort_order.descending is True

    def test_sort_order_default_ascending(self):
        """Test SortOrder defaults to ascending"""
        sort_order = SortOrder(SearchField.NAME)

        assert sort_order.descending is False

    def test_search_field_enum_values(self):
        """Test SearchField enum has expected values"""
        assert SearchField.NAME.value == "name"
        assert SearchField.EMAIL.value == "email"
        assert SearchField.STATUS.value == "status"
        assert SearchField.CREATED_AT.value == "created_at"

    def test_search_operator_enum_values(self):
        """Test SearchOperator enum has expected values"""
        assert SearchOperator.EQUALS.value == "equals"
        assert SearchOperator.CONTAINS.value == "contains"
        assert SearchOperator.IN.value == "in"
        assert SearchOperator.GREATER_THAN.value == "greater_than"
