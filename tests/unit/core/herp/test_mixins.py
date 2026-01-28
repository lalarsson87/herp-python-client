"""
Tests for HERP API mixins
"""

from unittest.mock import Mock, patch

import pytest

from src.core.herp.mixins import (
    BatchFetchMixin,
    CacheMixin,
    MetricsMixin,
    PaginationMixin,
    ValidationMixin,
)


class TestBatchFetchMixin:
    """Test BatchFetchMixin"""

    def test_batch_fetch_successful(self):
        """Test successful batch fetch"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()

        def fetch_func(item_id):
            return [{"id": f"{item_id}_1"}, {"id": f"{item_id}_2"}]

        results = api._batch_fetch(
            ids=["id1", "id2", "id3"],
            fetch_function=fetch_func,
            max_workers=2,
            resource_name="items",
        )

        assert len(results) == 3
        assert results["id1"] == [{"id": "id1_1"}, {"id": "id1_2"}]
        assert results["id2"] == [{"id": "id2_1"}, {"id": "id2_2"}]
        assert results["id3"] == [{"id": "id3_1"}, {"id": "id3_2"}]

    def test_batch_fetch_with_errors(self):
        """Test batch fetch with some errors"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()

        def fetch_func(item_id):
            if item_id == "id2":
                raise ValueError("Fetch failed")
            return [{"id": item_id}]

        results = api._batch_fetch(
            ids=["id1", "id2", "id3"], fetch_function=fetch_func, max_workers=2
        )

        # All IDs should be in results
        assert len(results) == 3
        assert results["id1"] == [{"id": "id1"}]
        assert results["id2"] == []  # Error returns empty list
        assert results["id3"] == [{"id": "id3"}]

    def test_batch_fetch_empty_ids(self):
        """Test batch fetch with empty ID list"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()

        def fetch_func(item_id):
            return [{"id": item_id}]

        results = api._batch_fetch(ids=[], fetch_function=fetch_func)

        assert results == {}

    def test_batch_fetch_single_id(self):
        """Test batch fetch with single ID"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()

        def fetch_func(item_id):
            return [{"id": item_id}]

        results = api._batch_fetch(ids=["id1"], fetch_function=fetch_func)

        assert len(results) == 1
        assert results["id1"] == [{"id": "id1"}]

    def test_batch_fetch_with_metrics(self):
        """Test batch fetch records metrics when available"""

        class TestAPI(BatchFetchMixin):
            def __init__(self):
                self.client = Mock()
                self.client.metrics = Mock()

        api = TestAPI()

        def fetch_func(item_id):
            if item_id == "id2":
                raise ValueError("Error")
            return [{"id": item_id}]

        api._batch_fetch(
            ids=["id1", "id2", "id3"],
            fetch_function=fetch_func,
            resource_name="contacts",
        )

        # Check metrics were recorded
        assert api.client.metrics.increment_counter.called

    def test_batch_fetch_max_workers(self):
        """Test batch fetch respects max_workers"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()
        call_count = [0]

        def fetch_func(item_id):
            call_count[0] += 1
            return [{"id": item_id}]

        results = api._batch_fetch(
            ids=["id1", "id2", "id3", "id4", "id5"],
            fetch_function=fetch_func,
            max_workers=2,
        )

        # All should be fetched
        assert len(results) == 5
        assert call_count[0] == 5


class TestPaginationMixin:
    """Test PaginationMixin"""

    def test_iterate_pages(self):
        """Test iterating over pages"""

        class TestAPI(PaginationMixin):
            pass

        api = TestAPI()

        def fetch_func(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}]
            elif offset == 2:
                return [{"id": "3"}]  # Partial page
            return []

        # Note: HerpPaginator expects 'fetch_func' not 'fetch_function'
        # So _iterate_pages creates it correctly
        items = list(api._iterate_pages(fetch_function=fetch_func, limit=2))

        assert len(items) == 3
        assert items[0] == {"id": "1"}
        assert items[1] == {"id": "2"}
        assert items[2] == {"id": "3"}

    def test_iterate_pages_with_max_pages(self):
        """Test iterate_pages respects max_pages"""

        class TestAPI(PaginationMixin):
            pass

        api = TestAPI()

        def fetch_func(offset, limit):
            # Always return full pages
            return [{"id": str(i)} for i in range(offset, offset + limit)]

        items = list(
            api._iterate_pages(fetch_function=fetch_func, limit=5, max_pages=2)
        )

        # Should only fetch 2 pages
        assert len(items) == 10  # 2 pages * 5 items

    def test_iterate_pages_empty(self):
        """Test iterate_pages with empty results"""

        class TestAPI(PaginationMixin):
            pass

        api = TestAPI()

        def fetch_func(offset, limit):
            return []

        items = list(api._iterate_pages(fetch_function=fetch_func, limit=10))

        assert items == []

    def test_iterate_pages_with_kwargs(self):
        """Test iterate_pages passes kwargs to fetch function"""

        class TestAPI(PaginationMixin):
            pass

        api = TestAPI()
        captured_kwargs = {}

        def fetch_func(offset, limit, **kwargs):
            captured_kwargs.update(kwargs)
            if offset == 0:
                return [{"id": "1"}]
            return []

        items = list(
            api._iterate_pages(
                fetch_function=fetch_func, limit=10, filter_type="active", status="open"
            )
        )

        assert len(items) == 1
        assert captured_kwargs["filter_type"] == "active"
        assert captured_kwargs["status"] == "open"


class TestValidationMixin:
    """Test ValidationMixin"""

    def test_validate_required_fields_all_present(self):
        """Test validation passes when all fields present"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"name": "Test", "email": "test@example.com", "age": 30}

        # Should not raise
        api._validate_required_fields(
            data, required_fields=["name", "email"], entity_name="user"
        )

    def test_validate_required_fields_missing(self):
        """Test validation fails with missing fields"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"name": "Test"}  # Missing 'email'

        with pytest.raises(ValueError, match="Missing required fields"):
            api._validate_required_fields(
                data, required_fields=["name", "email"], entity_name="user"
            )

    def test_validate_required_fields_multiple_missing(self):
        """Test validation error message includes all missing fields"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"name": "Test"}  # Missing 'email' and 'age'

        with pytest.raises(ValueError) as exc_info:
            api._validate_required_fields(
                data, required_fields=["name", "email", "age"], entity_name="user"
            )

        error_msg = str(exc_info.value)
        assert "email" in error_msg
        assert "age" in error_msg

    def test_validate_required_fields_empty_data(self):
        """Test validation with empty data"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()

        with pytest.raises(ValueError):
            api._validate_required_fields(
                {}, required_fields=["name"], entity_name="user"
            )

    def test_validate_field_values_valid(self):
        """Test field value validation with valid value"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"status": "active"}

        # Should not raise
        api._validate_field_values(
            data,
            field="status",
            allowed_values=["active", "inactive", "pending"],
            entity_name="user",
        )

    def test_validate_field_values_invalid(self):
        """Test field value validation with invalid value"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"status": "deleted"}

        with pytest.raises(ValueError, match="Invalid status"):
            api._validate_field_values(
                data,
                field="status",
                allowed_values=["active", "inactive"],
                entity_name="user",
            )

    def test_validate_field_values_field_not_present(self):
        """Test field value validation when field not present"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"name": "Test"}  # No 'status' field

        # Should not raise when field is not present
        api._validate_field_values(
            data, field="status", allowed_values=["active"], entity_name="user"
        )

    def test_validate_field_values_error_message(self):
        """Test validation error message shows allowed values"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"type": "unknown"}

        with pytest.raises(ValueError) as exc_info:
            api._validate_field_values(
                data, field="type", allowed_values=["A", "B", "C"], entity_name="item"
            )

        error_msg = str(exc_info.value)
        assert "A" in error_msg
        assert "B" in error_msg
        assert "C" in error_msg


class TestMetricsMixin:
    """Test MetricsMixin"""

    def test_record_operation_metric_success(self):
        """Test recording successful operation metric"""

        class TestAPI(MetricsMixin):
            def __init__(self):
                self.client = Mock()
                self.client.metrics = Mock()

        api = TestAPI()

        api._record_operation_metric(operation="create", success=True, resource="user")

        # Check metric was recorded
        assert api.client.metrics.increment_counter.called
        call_args = api.client.metrics.increment_counter.call_args
        labels = call_args.kwargs["labels"]
        assert labels["operation"] == "create"
        assert labels["status"] == "success"
        assert labels["resource"] == "user"

    def test_record_operation_metric_error(self):
        """Test recording error operation metric"""

        class TestAPI(MetricsMixin):
            def __init__(self):
                self.client = Mock()
                self.client.metrics = Mock()

        api = TestAPI()

        api._record_operation_metric(
            operation="update", success=False, error="NotFound", resource="user"
        )

        call_args = api.client.metrics.increment_counter.call_args
        labels = call_args.kwargs["labels"]
        assert labels["operation"] == "update"
        assert labels["status"] == "error"
        assert labels["error"] == "NotFound"
        assert labels["resource"] == "user"

    def test_record_operation_metric_no_client(self):
        """Test metric recording when no client available"""

        class TestAPI(MetricsMixin):
            pass

        api = TestAPI()

        # Should not raise
        api._record_operation_metric(operation="create", success=True)

    def test_record_operation_metric_no_metrics(self):
        """Test metric recording when client has no metrics"""

        class TestAPI(MetricsMixin):
            def __init__(self):
                self.client = Mock(spec=[])  # No metrics attribute

        api = TestAPI()

        # Should not raise
        api._record_operation_metric(operation="create", success=True)


class TestCacheMixin:
    """Test CacheMixin"""

    def test_cached_fetch_cache_hit(self):
        """Test cached fetch returns cached data"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock()
                self.client.cache_manager = Mock()
                self.client.cache_manager.get = Mock(return_value={"cached": True})

        api = TestAPI()
        fetch_func = Mock(return_value={"fresh": True})

        result = api._cached_fetch(
            cache_key="test_key", fetch_function=fetch_func, ttl=300
        )

        # Should return cached data
        assert result == {"cached": True}
        # Should not call fetch function
        assert not fetch_func.called

    def test_cached_fetch_cache_miss(self):
        """Test cached fetch on cache miss"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock()
                self.client.cache_manager = Mock()
                self.client.cache_manager.get = Mock(return_value=None)
                self.client.cache_manager.set = Mock()

        api = TestAPI()
        fetch_func = Mock(return_value={"fresh": True})

        result = api._cached_fetch(
            cache_key="test_key", fetch_function=fetch_func, ttl=300
        )

        # Should return fresh data
        assert result == {"fresh": True}
        # Should call fetch function
        assert fetch_func.called
        # Should cache the result
        api.client.cache_manager.set.assert_called_with(
            "test_key", {"fresh": True}, ttl=300
        )

    def test_cached_fetch_no_cache_manager(self):
        """Test cached fetch when no cache manager available"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock(spec=[])  # No cache_manager

        api = TestAPI()
        fetch_func = Mock(return_value={"fresh": True})

        result = api._cached_fetch(
            cache_key="test_key", fetch_function=fetch_func, ttl=300
        )

        # Should fetch directly without caching
        assert result == {"fresh": True}
        assert fetch_func.called

    def test_cached_fetch_no_client(self):
        """Test cached fetch when no client available"""

        class TestAPI(CacheMixin):
            pass

        api = TestAPI()
        fetch_func = Mock(return_value={"fresh": True})

        result = api._cached_fetch(
            cache_key="test_key", fetch_function=fetch_func, ttl=300
        )

        # Should fetch directly
        assert result == {"fresh": True}
        assert fetch_func.called

    def test_cached_fetch_custom_ttl(self):
        """Test cached fetch with custom TTL"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock()
                self.client.cache_manager = Mock()
                self.client.cache_manager.get = Mock(return_value=None)
                self.client.cache_manager.set = Mock()

        api = TestAPI()
        fetch_func = Mock(return_value={"data": "test"})

        api._cached_fetch(cache_key="test_key", fetch_function=fetch_func, ttl=600)

        # Should use custom TTL
        api.client.cache_manager.set.assert_called_with(
            "test_key", {"data": "test"}, ttl=600
        )

    def test_invalidate_cache(self):
        """Test cache invalidation"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock()
                self.client.cache_manager = Mock()

        api = TestAPI()

        api._invalidate_cache(cache_key="test_key")

        # Should call delete
        api.client.cache_manager.delete.assert_called_with("test_key")

    def test_invalidate_cache_no_cache_manager(self):
        """Test cache invalidation when no cache manager"""

        class TestAPI(CacheMixin):
            def __init__(self):
                self.client = Mock(spec=[])

        api = TestAPI()

        # Should not raise
        api._invalidate_cache(cache_key="test_key")

    def test_invalidate_cache_no_client(self):
        """Test cache invalidation when no client"""

        class TestAPI(CacheMixin):
            pass

        api = TestAPI()

        # Should not raise
        api._invalidate_cache(cache_key="test_key")


class TestMixinsEdgeCases:
    """Test edge cases for mixins"""

    def test_batch_fetch_all_errors(self):
        """Test batch fetch when all requests error"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()

        def fetch_func(item_id):
            raise RuntimeError("Always fails")

        results = api._batch_fetch(
            ids=["id1", "id2"], fetch_function=fetch_func, max_workers=2
        )

        # All should have empty results
        assert results["id1"] == []
        assert results["id2"] == []

    def test_validation_mixin_with_none_values(self):
        """Test validation with None values"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"name": None, "email": "test@example.com"}

        # name is present (even if None)
        api._validate_required_fields(data, required_fields=["name", "email"])

    def test_validation_field_values_with_numbers(self):
        """Test field value validation with numeric values"""

        class TestAPI(ValidationMixin):
            pass

        api = TestAPI()
        data = {"priority": 1}

        api._validate_field_values(
            data, field="priority", allowed_values=[1, 2, 3], entity_name="task"
        )

    def test_batch_fetch_duplicate_ids(self):
        """Test batch fetch with duplicate IDs"""

        class TestAPI(BatchFetchMixin):
            pass

        api = TestAPI()
        call_count = [0]

        def fetch_func(item_id):
            call_count[0] += 1
            return [{"id": item_id}]

        results = api._batch_fetch(
            ids=["id1", "id1", "id2"],  # Duplicate id1
            fetch_function=fetch_func,
            max_workers=2,
        )

        # Dictionary can only have unique keys, so only 2 entries
        assert len(results) == 2
        # But all 3 fetches should have been called
        assert call_count[0] == 3
        # Last fetch for id1 overwrites previous
        assert results["id1"] == [{"id": "id1"}]
        assert results["id2"] == [{"id": "id2"}]
