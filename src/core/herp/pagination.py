"""
Pagination utilities for HERP API

Provides pagination helpers for listing and searching API resources.
"""

from typing import Any, Callable, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class HerpPaginator:
    """
    HERP API paginator

    Handles pagination for HERP API list endpoints that return paginated results.
    """

    def __init__(
        self,
        fetch_func: Callable,
        limit: Optional[int] = None,
        max_pages: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize paginator

        Args:
            fetch_func: Function to call for fetching data (should accept offset/limit)
            limit: Maximum number of items per page
            max_pages: Maximum number of pages to fetch
            **kwargs: Additional arguments to pass to fetch_func
        """
        self.fetch_func = fetch_func
        self.limit = limit or 100
        self.max_pages = max_pages
        self.kwargs = kwargs

    def fetch_all(self) -> List[Dict[str, Any]]:
        """
        Fetch all pages of results

        Returns:
            List of all items across all pages
        """
        all_items = []
        offset = 0
        page = 1

        while True:
            # Check if we've hit max pages
            if self.max_pages and page > self.max_pages:
                logger.debug(f"Reached max_pages limit: {self.max_pages}")
                break

            # Fetch current page
            logger.debug(f"Fetching page {page} (offset={offset}, limit={self.limit})")
            result = self.fetch_func(offset=offset, limit=self.limit, **self.kwargs)

            # Handle both list and dict responses
            if isinstance(result, list):
                items = result
            elif isinstance(result, dict) and "data" in result:
                items = result.get("data", [])
            else:
                items = []

            # Add items to results
            all_items.extend(items)
            logger.debug(f"Page {page}: fetched {len(items)} items")

            # Check if we're done
            if not items or len(items) < self.limit:
                logger.debug("No more items to fetch")
                break

            # Move to next page
            offset += self.limit
            page += 1

        logger.info(
            f"Pagination complete: fetched {len(all_items)} total items "
            f"across {page} pages"
        )
        return all_items

    def fetch_page(self, page_num: int = 1) -> Dict[str, Any]:
        """
        Fetch a specific page of results

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Dictionary with page data and metadata
        """
        offset = (page_num - 1) * self.limit

        logger.debug(f"Fetching page {page_num} (offset={offset}, limit={self.limit})")
        result = self.fetch_func(offset=offset, limit=self.limit, **self.kwargs)

        # Normalize response format
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict) and "data" in result:
            items = result.get("data", [])
        else:
            items = []

        return {
            "data": items,
            "page": page_num,
            "limit": self.limit,
            "offset": offset,
            "count": len(items),
            "has_more": len(items) >= self.limit,
        }

    def __iter__(self):
        """
        Make paginator iterable for use in for loops and yield from

        Yields:
            Individual items across all pages
        """
        offset = 0
        page = 1

        while True:
            # Check if we've hit max pages
            if self.max_pages and page > self.max_pages:
                logger.debug(f"Reached max_pages limit: {self.max_pages}")
                break

            # Fetch current page
            logger.debug(f"Fetching page {page} (offset={offset}, limit={self.limit})")
            result = self.fetch_func(offset=offset, limit=self.limit, **self.kwargs)

            # Handle both list and dict responses
            if isinstance(result, list):
                items = result
            elif isinstance(result, dict) and "data" in result:
                items = result.get("data", [])
            else:
                items = []

            # Yield items one by one
            for item in items:
                yield item

            # Check if we're done
            if not items or len(items) < self.limit:
                logger.debug("No more items to fetch")
                break

            # Move to next page
            offset += self.limit
            page += 1
