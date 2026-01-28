#!/usr/bin/env python3
"""
HERP API Mixins

Reusable mixins for common patterns across API clients.
Eliminates code duplication and ensures consistency.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


class BatchFetchMixin:
    """
    Mixin for batch fetching operations

    Provides a standard pattern for fetching data for multiple IDs concurrently.
    Solves N+1 query problems by fetching data in parallel with rate limiting.

    Usage:
        class ContactsAPI(BatchFetchMixin):
            def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
                # Single fetch implementation
                ...

            def list_for_multiple(self, candidacy_ids: List[str], max_workers: int = 5):
                return self._batch_fetch(
                    ids=candidacy_ids,
                    fetch_function=self.list,
                    max_workers=max_workers,
                    resource_name="contacts"
                )
    """

    def _batch_fetch(
        self,
        ids: List[str],
        fetch_function: Callable[[str], List[Dict[str, Any]]],
        max_workers: int = 5,
        resource_name: str = "items",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch fetch items for multiple IDs concurrently

        Args:
            ids: List of IDs to fetch for
            fetch_function: Function that fetches items for a single ID
            max_workers: Maximum concurrent requests (default: 5)
            resource_name: Name of resource for logging (default: "items")

        Returns:
            Dictionary mapping ID to list of items

        Example:
            >>> results = self._batch_fetch(
            ...     ids=["id1", "id2", "id3"],
            ...     fetch_function=self.list,
            ...     max_workers=5,
            ...     resource_name="contacts"
            ... )
            >>> # Returns: {"id1": [...], "id2": [...], "id3": [...]}
        """
        results = {}
        errors = {}

        def fetch_for_id(item_id: str) -> tuple:
            """Fetch items for a single ID"""
            try:
                items = fetch_function(item_id)
                return item_id, items, None
            except Exception as e:
                logger.warning(f"Failed to fetch {resource_name} for {item_id}: {e}")
                return item_id, [], str(e)

        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(fetch_for_id, item_id): item_id for item_id in ids
            }

            # Collect results as they complete
            for future in as_completed(future_to_id):
                item_id, items, error = future.result()
                results[item_id] = items
                if error:
                    errors[item_id] = error
                    # Record error metric if client has metrics
                    if hasattr(self, "client") and hasattr(self.client, "metrics"):
                        self.client.metrics.increment_counter(
                            f"herp.batch.{resource_name}.errors",
                            labels={"error": "fetch_failed"},
                        )

        # Log summary
        logger.info(
            f"Batch fetched {resource_name} for {len(ids)} IDs: "
            f"{len(results)} successful, {len(errors)} errors"
        )

        # Record metrics if available
        if hasattr(self, "client") and hasattr(self.client, "metrics"):
            self.client.metrics.increment_counter(
                f"herp.batch.{resource_name}.total", value=len(ids)
            )
            self.client.metrics.increment_counter(
                f"herp.batch.{resource_name}.success", value=len(results) - len(errors)
            )

        return results


class PaginationMixin:
    """
    Mixin for pagination support

    Provides helper methods for paginated endpoints.

    Usage:
        class CandidaciesAPI(PaginationMixin):
            def list(self, page: int = 1, limit: int = 50) -> List[Dict]:
                # Implementation
                ...

            def iter_all(self):
                return self._iterate_pages(
                    fetch_function=self.list,
                    limit=100
                )
    """

    def _iterate_pages(
        self,
        fetch_function: Callable,
        limit: int = 100,
        max_pages: Optional[int] = None,
        **kwargs,
    ):
        """
        Iterate over all pages using a fetch function

        Args:
            fetch_function: Function to fetch a single page
            limit: Items per page
            max_pages: Maximum pages to fetch (None = unlimited)
            **kwargs: Additional arguments for fetch_function

        Yields:
            Individual items across all pages
        """
        from .pagination import HerpPaginator

        paginator = HerpPaginator(
            fetch_function=fetch_function, limit=limit, max_pages=max_pages, **kwargs
        )

        yield from paginator


class ValidationMixin:
    """
    Mixin for common validation patterns

    Provides reusable validation helpers.
    """

    def _validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        entity_name: str = "entity",
    ) -> None:
        """
        Validate that required fields are present

        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            entity_name: Name of entity for error messages

        Raises:
            ValueError: If required fields are missing
        """
        missing = [field for field in required_fields if field not in data]

        if missing:
            fields_str = ", ".join(missing)
            raise ValueError(f"Missing required fields for {entity_name}: {fields_str}")

    def _validate_field_values(
        self,
        data: Dict[str, Any],
        field: str,
        allowed_values: List[Any],
        entity_name: str = "entity",
    ) -> None:
        """
        Validate that a field has an allowed value

        Args:
            data: Dictionary to validate
            field: Field name to validate
            allowed_values: List of allowed values
            entity_name: Name of entity for error messages

        Raises:
            ValueError: If field value is not allowed
        """
        if field in data and data[field] not in allowed_values:
            values_str = ", ".join(str(v) for v in allowed_values)
            raise ValueError(
                f"Invalid {field} for {entity_name}: {data[field]}. "
                f"Allowed values: {values_str}"
            )


class MetricsMixin:
    """
    Mixin for recording metrics

    Provides helper methods for consistent metric recording.
    """

    def _record_operation_metric(
        self,
        operation: str,
        success: bool = True,
        error: Optional[str] = None,
        **labels,
    ) -> None:
        """
        Record metric for an operation

        Args:
            operation: Operation name (e.g., "create", "update", "delete")
            success: Whether operation succeeded
            error: Error message if failed
            **labels: Additional metric labels
        """
        if not hasattr(self, "client") or not hasattr(self.client, "metrics"):
            return

        # Determine status
        status = "success" if success else "error"

        # Base labels
        metric_labels = {"operation": operation, "status": status, **labels}

        # Add error label if present
        if error:
            metric_labels["error"] = error

        # Record counter
        self.client.metrics.increment_counter(
            "herp.api.operations", labels=metric_labels
        )


class CacheMixin:
    """
    Mixin for caching support

    Provides helper methods for caching API responses.

    Usage:
        class MasterDataAPI(CacheMixin):
            def list_requisitions(self):
                cache_key = "requisitions:all"
                return self._cached_fetch(
                    cache_key=cache_key,
                    fetch_function=lambda: self.client.get("/v1/requisitions"),
                    ttl=300  # 5 minutes
                )
    """

    def _cached_fetch(
        self, cache_key: str, fetch_function: Callable, ttl: int = 300
    ) -> Any:
        """
        Fetch with caching

        Args:
            cache_key: Cache key
            fetch_function: Function to fetch data if not cached
            ttl: Time to live in seconds (default: 300)

        Returns:
            Cached or freshly fetched data
        """
        # Check if client has cache manager
        if not hasattr(self, "client") or not hasattr(self.client, "cache_manager"):
            # No cache available, fetch directly
            return fetch_function()

        cache_manager = self.client.cache_manager

        # Try to get from cache
        cached = cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        # Cache miss, fetch and cache
        logger.debug(f"Cache miss for {cache_key}, fetching...")
        data = fetch_function()
        cache_manager.set(cache_key, data, ttl=ttl)

        return data

    def _invalidate_cache(self, cache_key: str) -> None:
        """
        Invalidate cache entry

        Args:
            cache_key: Cache key to invalidate
        """
        if hasattr(self, "client") and hasattr(self.client, "cache_manager"):
            self.client.cache_manager.delete(cache_key)
            logger.debug(f"Invalidated cache for {cache_key}")
