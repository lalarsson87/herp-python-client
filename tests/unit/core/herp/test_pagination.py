"""
Tests for pagination utilities
"""

from unittest.mock import Mock

import pytest

from src.core.herp.pagination import HerpPaginator


class TestHerpPaginator:
    """Test HerpPaginator"""

    def test_initialization(self):
        """Test paginator initialization"""

        def mock_fetch(offset, limit):
            return []

        paginator = HerpPaginator(mock_fetch, limit=50, max_pages=10)

        assert paginator.fetch_func == mock_fetch
        assert paginator.limit == 50
        assert paginator.max_pages == 10

    def test_initialization_default_limit(self):
        """Test default limit is 100"""

        def mock_fetch(offset, limit):
            return []

        paginator = HerpPaginator(mock_fetch)

        assert paginator.limit == 100
        assert paginator.max_pages is None

    def test_fetch_all_single_page(self):
        """Test fetch_all with single page of results"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}, {"id": "3"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        results = paginator.fetch_all()

        assert len(results) == 3
        assert results[0]["id"] == "1"
        assert results[2]["id"] == "3"

    def test_fetch_all_multiple_pages(self):
        """Test fetch_all across multiple pages"""
        call_count = [0]

        def mock_fetch(offset, limit):
            call_count[0] += 1
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}]
            elif offset == 2:
                return [{"id": "3"}, {"id": "4"}]
            elif offset == 4:
                return [{"id": "5"}]  # Last page (less than limit)
            return []

        paginator = HerpPaginator(mock_fetch, limit=2)
        results = paginator.fetch_all()

        assert len(results) == 5
        assert call_count[0] == 3  # Three pages fetched
        assert results[0]["id"] == "1"
        assert results[4]["id"] == "5"

    def test_fetch_all_empty_response(self):
        """Test fetch_all with empty response"""

        def mock_fetch(offset, limit):
            return []

        paginator = HerpPaginator(mock_fetch)
        results = paginator.fetch_all()

        assert results == []

    def test_fetch_all_dict_response_with_data_key(self):
        """Test fetch_all with dict response containing 'data' key"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return {"data": [{"id": "1"}, {"id": "2"}], "total": 2}
            return {"data": []}

        paginator = HerpPaginator(mock_fetch, limit=10)
        results = paginator.fetch_all()

        assert len(results) == 2
        assert results[0]["id"] == "1"

    def test_fetch_all_dict_response_without_data_key(self):
        """Test fetch_all with dict response without 'data' key"""

        def mock_fetch(offset, limit):
            return {"results": [{"id": "1"}]}  # No 'data' key

        paginator = HerpPaginator(mock_fetch)
        results = paginator.fetch_all()

        # Should return empty list when no 'data' key
        assert results == []

    def test_fetch_all_with_max_pages(self):
        """Test fetch_all respects max_pages limit"""
        call_count = [0]

        def mock_fetch(offset, limit):
            call_count[0] += 1
            # Always return full pages
            return [{"id": str(i)} for i in range(offset, offset + limit)]

        paginator = HerpPaginator(mock_fetch, limit=5, max_pages=3)
        results = paginator.fetch_all()

        # Should fetch exactly 3 pages
        assert call_count[0] == 3
        assert len(results) == 15  # 3 pages * 5 items

    def test_fetch_all_stops_on_partial_page(self):
        """Test fetch_all stops when page has fewer items than limit"""
        call_count = [0]

        def mock_fetch(offset, limit):
            call_count[0] += 1
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}, {"id": "3"}]
            elif offset == 3:
                return [{"id": "4"}]  # Partial page (1 < limit)
            # Should not reach here
            return [{"id": "5"}, {"id": "6"}, {"id": "7"}]

        paginator = HerpPaginator(mock_fetch, limit=3)
        results = paginator.fetch_all()

        assert len(results) == 4
        assert call_count[0] == 2  # Should stop after partial page

    def test_fetch_all_with_kwargs(self):
        """Test fetch_all passes additional kwargs to fetch function"""
        captured_kwargs = {}

        def mock_fetch(offset, limit, **kwargs):
            captured_kwargs.update(kwargs)
            if offset == 0:
                return [{"id": "1"}]
            return []

        paginator = HerpPaginator(
            mock_fetch, limit=10, filter_type="active", status="pending"
        )
        results = paginator.fetch_all()

        assert len(results) == 1
        assert captured_kwargs["filter_type"] == "active"
        assert captured_kwargs["status"] == "pending"

    def test_fetch_page_first_page(self):
        """Test fetch_page for first page"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}, {"id": "3"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=1)

        assert result["data"] == [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        assert result["page"] == 1
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert result["count"] == 3
        assert result["has_more"] is False  # Less than limit

    def test_fetch_page_second_page(self):
        """Test fetch_page for second page"""

        def mock_fetch(offset, limit):
            if offset == 10:
                return [{"id": "11"}, {"id": "12"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=2)

        assert result["data"] == [{"id": "11"}, {"id": "12"}]
        assert result["page"] == 2
        assert result["offset"] == 10
        assert result["count"] == 2

    def test_fetch_page_has_more_flag(self):
        """Test fetch_page sets has_more correctly"""

        def mock_fetch(offset, limit):
            # Return exactly limit items
            return [{"id": str(i)} for i in range(offset, offset + limit)]

        paginator = HerpPaginator(mock_fetch, limit=5)
        result = paginator.fetch_page(page_num=1)

        # Full page means there might be more
        assert result["has_more"] is True
        assert result["count"] == 5

    def test_fetch_page_empty_page(self):
        """Test fetch_page with empty page"""

        def mock_fetch(offset, limit):
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=1)

        assert result["data"] == []
        assert result["count"] == 0
        assert result["has_more"] is False

    def test_fetch_page_dict_response(self):
        """Test fetch_page with dict response"""

        def mock_fetch(offset, limit):
            return {"data": [{"id": "1"}], "total": 1}

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=1)

        assert result["data"] == [{"id": "1"}]
        assert result["count"] == 1

    def test_iterator_single_page(self):
        """Test paginator as iterator with single page"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}, {"id": "3"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        items = list(paginator)

        assert len(items) == 3
        assert items[0] == {"id": "1"}
        assert items[2] == {"id": "3"}

    def test_iterator_multiple_pages(self):
        """Test paginator as iterator across multiple pages"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}]
            elif offset == 2:
                return [{"id": "3"}, {"id": "4"}]
            elif offset == 4:
                return [{"id": "5"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=2)
        items = list(paginator)

        assert len(items) == 5
        assert items[0] == {"id": "1"}
        assert items[4] == {"id": "5"}

    def test_iterator_with_max_pages(self):
        """Test iterator respects max_pages"""
        call_count = [0]

        def mock_fetch(offset, limit):
            call_count[0] += 1
            return [{"id": str(i)} for i in range(offset, offset + limit)]

        paginator = HerpPaginator(mock_fetch, limit=3, max_pages=2)
        items = list(paginator)

        # Should fetch exactly 2 pages
        assert call_count[0] == 2
        assert len(items) == 6  # 2 pages * 3 items

    def test_iterator_stops_on_empty_page(self):
        """Test iterator stops on empty page"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        items = list(paginator)

        assert len(items) == 1

    def test_iterator_can_be_used_multiple_times(self):
        """Test iterator can be used multiple times"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)

        # First iteration
        items1 = list(paginator)
        assert len(items1) == 2

        # Second iteration
        items2 = list(paginator)
        assert len(items2) == 2

    def test_iterator_in_for_loop(self):
        """Test using paginator in for loop"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": "1"}, {"id": "2"}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)

        ids = []
        for item in paginator:
            ids.append(item["id"])

        assert ids == ["1", "2"]

    def test_iterator_dict_response(self):
        """Test iterator with dict response"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return {"data": [{"id": "1"}, {"id": "2"}]}
            return {"data": []}

        paginator = HerpPaginator(mock_fetch, limit=10)
        items = list(paginator)

        assert len(items) == 2


class TestHerpPaginatorEdgeCases:
    """Test edge cases for HerpPaginator"""

    def test_very_large_limit(self):
        """Test paginator with very large limit"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": str(i)} for i in range(100)]
            return []

        paginator = HerpPaginator(mock_fetch, limit=10000)
        results = paginator.fetch_all()

        assert len(results) == 100

    def test_limit_of_one(self):
        """Test paginator with limit=1"""

        def mock_fetch(offset, limit):
            if offset < 3:
                return [{"id": str(offset)}]
            return []

        paginator = HerpPaginator(mock_fetch, limit=1)
        results = paginator.fetch_all()

        assert len(results) == 3

    def test_max_pages_of_one(self):
        """Test paginator with max_pages=1"""

        def mock_fetch(offset, limit):
            return [{"id": str(i)} for i in range(offset, offset + limit)]

        paginator = HerpPaginator(mock_fetch, limit=5, max_pages=1)
        results = paginator.fetch_all()

        assert len(results) == 5  # Only first page

    def test_fetch_page_with_page_num_zero(self):
        """Test fetch_page with page_num=0 (edge case)"""

        def mock_fetch(offset, limit):
            # offset would be negative: (0-1)*10 = -10
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=0)

        # offset would be -10
        assert result["page"] == 0
        assert result["offset"] == -10

    def test_fetch_page_with_large_page_num(self):
        """Test fetch_page with large page number"""

        def mock_fetch(offset, limit):
            return []

        paginator = HerpPaginator(mock_fetch, limit=10)
        result = paginator.fetch_page(page_num=1000)

        assert result["page"] == 1000
        assert result["offset"] == 9990  # (1000-1)*10

    def test_none_response(self):
        """Test handling None response from fetch_func"""

        def mock_fetch(offset, limit):
            return None

        paginator = HerpPaginator(mock_fetch, limit=10)
        results = paginator.fetch_all()

        # Should handle None gracefully
        assert results == []

    def test_kwargs_preserved_across_pages(self):
        """Test kwargs are preserved across multiple pages"""
        captured_calls = []

        def mock_fetch(offset, limit, **kwargs):
            captured_calls.append({"offset": offset, "kwargs": kwargs.copy()})
            if offset < 6:
                return [{"id": str(i)} for i in range(offset, offset + 3)]
            return []

        paginator = HerpPaginator(mock_fetch, limit=3, filter="active", sort="name")
        results = paginator.fetch_all()

        # Check all calls had the same kwargs
        for call in captured_calls:
            assert call["kwargs"]["filter"] == "active"
            assert call["kwargs"]["sort"] == "name"

    def test_exception_in_fetch_func(self):
        """Test exception in fetch function propagates"""

        def mock_fetch(offset, limit):
            raise ValueError("API error")

        paginator = HerpPaginator(mock_fetch, limit=10)

        with pytest.raises(ValueError, match="API error"):
            paginator.fetch_all()

    def test_partial_page_exactly_at_limit(self):
        """Test behavior when last page has exactly limit items"""

        def mock_fetch(offset, limit):
            if offset == 0:
                return [{"id": str(i)} for i in range(5)]  # Exactly limit
            # Should still check next page
            return []

        paginator = HerpPaginator(mock_fetch, limit=5)
        results = paginator.fetch_all()

        assert len(results) == 5
