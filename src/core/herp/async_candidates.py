#!/usr/bin/env python3
"""
HERP Async Candidacies API Client

Async version of candidacy operations including list, search, create, update, and terminate.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response, validate_single_response
from .async_base_client import AsyncHerpBaseClient
from .query_dsl import FieldFilter, FilterOperator, LogicalOperator, Query
from .schemas import (
    HerpCandidaciesListResponse,
    HerpCandidacyResponse,
)

logger = get_logger(__name__)


class AsyncHerpPaginator:
    """Async paginator for HERP API endpoints"""

    def __init__(
        self,
        fetch_function,
        limit: int = 100,
        max_pages: Optional[int] = None,
        **fetch_kwargs,
    ):
        """
        Initialize async paginator

        Args:
            fetch_function: Async function to fetch a single page
            limit: Items per page
            max_pages: Maximum pages to fetch (None = unlimited)
            **fetch_kwargs: Additional arguments for fetch_function
        """
        self.fetch_function = fetch_function
        self.limit = limit
        self.max_pages = max_pages
        self.fetch_kwargs = fetch_kwargs

    async def __aiter__(self) -> AsyncIterator[Dict[str, Any]]:
        """Async iterate over all pages"""
        page = 1
        pages_fetched = 0

        while True:
            # Check max_pages limit
            if self.max_pages and pages_fetched >= self.max_pages:
                break

            # Fetch page
            items = await self.fetch_function(
                page=page, limit=self.limit, **self.fetch_kwargs
            )

            # Yield items
            for item in items:
                yield item

            # Check if we're done
            if len(items) < self.limit:
                break

            page += 1
            pages_fetched += 1


# Note: Query moved to query_dsl.py as CandidacyQuery
# Import for backward compatibility


class AsyncCandidaciesAPI:
    """
    Async Candidacies API Client

    Provides async methods for candidacy operations.

    Usage:
        async with AsyncHerpBaseClient(config) as base_client:
            api = AsyncCandidaciesAPI(base_client)
            candidacies = await api.list()

            # Or iterate over all:
            async for candidacy in api.iter():
                print(candidacy["name"])
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async candidacies API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpCandidaciesListResponse, strict=False)
    async def list(
        self, updated_since: Optional[str] = None, page: int = 1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List candidacies (single page)

        Args:
            updated_since: ISO timestamp to filter by update time
            page: Page number (1-indexed)
            limit: Items per page (max 100)

        Returns:
            List of candidacy records
        """
        params = {"page": page, "limit": min(limit, 100)}

        if updated_since:
            params["updatedSince"] = updated_since

        data = await self.client.get("/v1/candidacies", params=params)
        return data.get("candidacies", data.get("data", []))

    def iter(
        self,
        updated_since: Optional[str] = None,
        limit: int = 100,
        max_pages: Optional[int] = None,
    ) -> AsyncHerpPaginator:
        """
        Iterate over all candidacies (memory efficient)

        Args:
            updated_since: ISO timestamp to filter by update time
            limit: Items per page
            max_pages: Maximum pages to fetch

        Returns:
            Async iterator over candidacies

        Usage:
            async for candidacy in api.iter():
                print(candidacy["name"])
        """
        return AsyncHerpPaginator(
            fetch_function=self.list,
            limit=limit,
            max_pages=max_pages,
            updated_since=updated_since,
        )

    async def fetch_all(
        self, updated_since: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch all candidacies (loads everything into memory)

        Args:
            updated_since: ISO timestamp to filter by update time
            limit: Items per page for pagination

        Returns:
            List of all candidacy records

        Warning:
            This loads all records into memory. Use iter() for large datasets.
        """
        results = []
        async for candidacy in self.iter(updated_since=updated_since, limit=limit):
            results.append(candidacy)
        return results

    async def search(
        self,
        query: Optional[Query] = None,
        limit: Optional[int] = None,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Search candidacies with flexible filtering using Query DSL

        Args:
            query: CandidacyQuery object (optional)
            limit: Maximum results to return
            **filters: Direct filter arguments (legacy support)

        Returns:
            List of matching candidacy records

        Usage:
            # Using Query DSL
            from src.core.herp.query_dsl import CandidacyQuery
            query = (
                CandidacyQuery()
                .by_email("jane@example.com")
                .by_step("interview")
                .active_only()
            )
            results = await api.search(query)

            # Complex queries
            query = (
                CandidacyQuery()
                .or_(
                    CandidacyQuery().by_email("jane@example.com"),
                    CandidacyQuery().by_email("john@example.com")
                )
                .by_step("interview")
            )
            results = await api.search(query)

            # Legacy direct filters still work
            results = await api.search(email="jane@example.com", step="interview")
        """

        # If query is provided, use it
        if query is not None:
            # Apply query to all candidacies
            all_candidacies = await self.fetch_all()
            results = self._apply_query(query, all_candidacies)
        else:
            # Legacy: use quick filters
            all_candidacies = await self.fetch_all()
            results = self._apply_legacy_filters(all_candidacies, filters)

        # Apply limit
        if limit and len(results) > limit:
            results = results[:limit]

        logger.info(f"Search found {len(results)} candidacies matching query")
        return results

    def _apply_query(
        self, query: Query, candidacies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply query DSL to candidacies"""
        results = []
        for candidacy in candidacies:
            if self._matches_query(query, candidacy):
                results.append(candidacy)
        return results

    def _matches_query(self, query: Query, candidacy: Dict[str, Any]) -> bool:
        """Check if candidacy matches query"""

        # Handle empty query
        if not query.filters:
            return True

        # Evaluate filters
        filter_results = []
        for filter_item in query.filters:
            if isinstance(filter_item, FieldFilter):
                filter_results.append(self._matches_filter(filter_item, candidacy))
            elif isinstance(filter_item, Query):
                filter_results.append(self._matches_query(filter_item, candidacy))

        # Apply logical operator
        if query.logical_operator == LogicalOperator.AND:
            result = all(filter_results) if filter_results else True
        elif query.logical_operator == LogicalOperator.OR:
            result = any(filter_results) if filter_results else False
        else:
            result = all(filter_results) if filter_results else True

        # Apply negation
        if query.negated:
            result = not result

        return result

    def _matches_filter(self, filter: FieldFilter, candidacy: Dict[str, Any]) -> bool:
        """Check if candidacy matches single filter"""

        field_value = candidacy.get(filter.field)
        operator = filter.operator
        filter_value = filter.value

        if operator == FilterOperator.EQUALS:
            return field_value == filter_value
        elif operator == FilterOperator.NOT_EQUALS:
            return field_value != filter_value
        elif operator == FilterOperator.CONTAINS:
            return filter_value in str(field_value) if field_value else False
        elif operator == FilterOperator.NOT_CONTAINS:
            return filter_value not in str(field_value) if field_value else True
        elif operator == FilterOperator.STARTS_WITH:
            return str(field_value).startswith(filter_value) if field_value else False
        elif operator == FilterOperator.ENDS_WITH:
            return str(field_value).endswith(filter_value) if field_value else False
        elif operator == FilterOperator.IN:
            return field_value in filter_value
        elif operator == FilterOperator.NOT_IN:
            return field_value not in filter_value
        elif operator == FilterOperator.GREATER_THAN:
            return field_value > filter_value if field_value else False
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= filter_value if field_value else False
        elif operator == FilterOperator.LESS_THAN:
            return field_value < filter_value if field_value else False
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return field_value <= filter_value if field_value else False
        elif operator == FilterOperator.BETWEEN:
            if (
                field_value
                and isinstance(filter_value, list)
                and len(filter_value) == 2
            ):
                return filter_value[0] <= field_value <= filter_value[1]
            return False
        elif operator == FilterOperator.IS_NULL:
            return field_value is None or field_value == ""
        elif operator == FilterOperator.IS_NOT_NULL:
            return field_value is not None and field_value != ""
        else:
            return True

    def _apply_legacy_filters(
        self, candidacies: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply legacy quick filters"""
        results = []
        for candidacy in candidacies:
            match = True

            # Check each filter
            for key, value in filters.items():
                if key == "tags":
                    # Tags filter: check if all required tags are present
                    candidacy_tags = candidacy.get("tags", [])
                    if not all(tag in candidacy_tags for tag in value):
                        match = False
                        break
                elif key in candidacy:
                    # Exact match for other fields
                    if candidacy[key] != value:
                        match = False
                        break

            if match:
                results.append(candidacy)

        return results

    @validate_single_response(HerpCandidacyResponse, strict=False)
    async def get(self, candidacy_id: str) -> Dict[str, Any]:
        """
        Get candidacy details

        Args:
            candidacy_id: Candidacy ID

        Returns:
            Candidacy record
        """
        data = await self.client.get(f"/v1/candidacies/{candidacy_id}")
        return data.get("candidacy", data.get("data", data))

    @validate_single_response(HerpCandidacyResponse, strict=False)
    async def create(self, candidacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new candidacy

        Args:
            candidacy_data: Candidacy data (name, email, requisition_id, etc.)

        Returns:
            Created candidacy record

        Usage:
            candidacy = await api.create({
                "name": "Jane Doe",
                "email": "jane@example.com",
                "requisition_id": "req_001"
            })
        """
        data = await self.client.post("/v1/candidacies", json=candidacy_data)
        return data.get("candidacy", data.get("data", data))

    @validate_single_response(HerpCandidacyResponse, strict=False)
    async def update_step(
        self, candidacy_id: str, step: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update candidacy hiring step

        Args:
            candidacy_id: Candidacy ID
            step: New step (e.g., "application", "phone_screen", "interview")
            comment: Optional comment about the step change

        Returns:
            Updated candidacy record
        """
        payload = {"step": step}
        if comment:
            payload["comment"] = comment

        data = await self.client.patch(
            f"/v1/candidacies/{candidacy_id}/step", json=payload
        )
        return data.get("candidacy", data.get("data", data))

    @validate_single_response(HerpCandidacyResponse, strict=False)
    async def terminate(
        self, candidacy_id: str, reason: str, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Terminate candidacy

        Args:
            candidacy_id: Candidacy ID
            reason: Termination reason (e.g., "hired", "rejected", "withdrawn")
            comment: Optional comment about termination

        Returns:
            Terminated candidacy record
        """
        payload = {"reason": reason}
        if comment:
            payload["comment"] = comment

        data = await self.client.patch(
            f"/v1/candidacies/{candidacy_id}/termination", json=payload
        )
        return data.get("candidacy", data.get("data", data))
