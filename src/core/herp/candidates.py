#!/usr/bin/env python3
"""
HERP Candidacies API Client

Handles all candidacy-related operations including listing, searching,
creating, updating, and managing candidate hiring stages.
"""

from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response, validate_response
from .base_client import HerpBaseClient
from .pagination import HerpPaginator
from .query_dsl import FieldFilter, FilterOperator, LogicalOperator, Query
from .schemas import (
    HerpCandidaciesListResponse,
    HerpCandidacyResponse,
)

logger = get_logger(__name__)


class CandidaciesAPI:
    """
    Candidacies API Client

    Provides methods for managing candidates in the HERP hiring system.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize candidacies API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpCandidaciesListResponse, strict=False)
    def list(
        self, updated_since: Optional[str] = None, page: int = 1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List candidacies (single page)

        Args:
            updated_since: ISO 8601 datetime to fetch only updated records
            page: Page number (1-indexed)
            limit: Results per page

        Returns:
            List of candidacy records for the requested page

        Note:
            For fetching all candidacies across all pages, use iter()
            or fetch_all() instead.
        """
        params = {"page": page, "limit": limit}
        if updated_since:
            params["updatedSince"] = updated_since

        data = self.client.get("/v1/candidacies", params=params)
        return data.get("candidacies", data.get("data", []))

    def iter(
        self,
        updated_since: Optional[str] = None,
        limit: int = 100,
        max_pages: Optional[int] = None,
    ) -> HerpPaginator:
        """
        Iterate over all candidacies across all pages (memory efficient)

        Args:
            updated_since: ISO 8601 datetime to fetch only updated records
            limit: Results per page (default: 100)
            max_pages: Maximum pages to fetch (None = unlimited)

        Returns:
            HerpPaginator iterator for memory-efficient iteration

        Example:
            >>> for candidacy in client.candidacies.iter():
            ...     process(candidacy)

            >>> # Fetch only recent updates
            >>> for candidacy in client.candidacies.iter(updated_since="2026-01-20T00:00:00Z"):
            ...     sync_to_notion(candidacy)
        """
        return HerpPaginator(
            fetch_function=self.list,
            limit=limit,
            max_pages=max_pages,
            updated_since=updated_since,
        )

    def fetch_all(
        self,
        updated_since: Optional[str] = None,
        limit: int = 100,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all candidacies across all pages (loads into memory)

        Args:
            updated_since: ISO 8601 datetime to fetch only updated records
            limit: Results per page (default: 100)
            max_pages: Maximum pages to fetch (None = unlimited)

        Returns:
            List of all candidacy records across all pages

        Warning:
            This loads all results into memory. For 7000+ candidacies, this
            will consume significant memory. Prefer iter() for
            memory-efficient iteration.

        Example:
            >>> all_candidacies = client.candidacies.fetch_all()
            >>> print(f"Total candidates: {len(all_candidacies)}")
        """
        paginator = self.iter(
            updated_since=updated_since, limit=limit, max_pages=max_pages
        )
        return paginator.fetch_all()

    def search(
        self,
        query: Optional[Query] = None,
        limit: Optional[int] = None,
        **filters,
    ) -> List[Dict[str, Any]]:
        """
        Search candidacies with flexible filtering

        Args:
            query: SearchQuery object with filters/sorts (optional)
            limit: Maximum results to return
            **filters: Quick filters (name=, email=, status=, etc.)

        Returns:
            List of matching candidacy records

        Example:
            >>> # Using Query DSL
            >>> from src.core.herp.query_dsl import CandidacyQuery
            >>> query = (
            ...     CandidacyQuery()
            ...     .by_name("John")
            ...     .by_status("active")
            ...     .created_after("2026-01-01")
            ... )
            >>> results = client.candidacies.search(query)
            >>>
            >>> # Using complex queries
            >>> query = (
            ...     CandidacyQuery()
            ...     .or_(
            ...         CandidacyQuery().by_email("jane@example.com"),
            ...         CandidacyQuery().by_email("john@example.com")
            ...     )
            ...     .by_step("interview")
            ... )
            >>> results = client.candidacies.search(query)
            >>>
            >>> # Using quick filters (legacy)
            >>> results = client.candidacies.search(name="John", status="active")
        """

        # If query is provided, use it
        if query is not None:
            # Apply query to all candidacies
            all_candidacies = self.fetch_all()
            results = self._apply_query(query, all_candidacies)
        else:
            # Legacy: use quick filters
            all_candidacies = self.fetch_all()
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
                if key == "name":
                    if value not in candidacy.get("name", ""):
                        match = False
                        break
                elif key == "email":
                    if candidacy.get("email") != value:
                        match = False
                        break
                elif key == "status":
                    if isinstance(value, list):
                        if candidacy.get("status") not in value:
                            match = False
                            break
                    else:
                        if candidacy.get("status") != value:
                            match = False
                            break
                elif key in candidacy:
                    if candidacy[key] != value:
                        match = False
                        break

            if match:
                results.append(candidacy)

        return results

    @validate_response(HerpCandidacyResponse, strict=False)
    def get(self, candidacy_id: str) -> Dict[str, Any]:
        """
        Get candidacy details

        Args:
            candidacy_id: Candidacy ID

        Returns:
            Candidacy record
        """
        return self.client.get(f"/v1/candidacies/{candidacy_id}")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new candidacy

        Args:
            data: Candidacy data

        Returns:
            Created candidacy record
        """
        return self.client.post("/v1/candidacies", json=data)

    def update_step(self, candidacy_id: str, step: str) -> Dict[str, Any]:
        """
        Update candidacy hiring step

        Args:
            candidacy_id: Candidacy ID
            step: New step value

        Returns:
            Updated candidacy record
        """
        return self.client.patch(
            f"/v1/candidacies/{candidacy_id}/step", json={"step": step}
        )

    def terminate(self, candidacy_id: str, termination_reason: str) -> Dict[str, Any]:
        """
        Terminate candidacy

        Args:
            candidacy_id: Candidacy ID
            termination_reason: Reason for termination

        Returns:
            Updated candidacy record
        """
        return self.client.patch(
            f"/v1/candidacies/{candidacy_id}/termination",
            json={"terminationReason": termination_reason},
        )
