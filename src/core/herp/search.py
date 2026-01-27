#!/usr/bin/env python3
"""
HERP Search Functionality

Provides flexible search capabilities for HERP resources (candidacies, contacts, etc.)
Supports filtering, sorting, and pagination.

Example:
    >>> from src.core.herp.search import SearchQuery, SearchField
    >>>
    >>> # Search for candidacies by name
    >>> query = SearchQuery()
    >>> query.add_filter(SearchField.NAME, "contains", "John")
    >>> results = client.search_candidacies(query)
    >>>
    >>> # Complex query with multiple filters
    >>> query = SearchQuery()
    >>> query.add_filter(SearchField.EMAIL, "equals", "john@example.com")
    >>> query.add_filter(SearchField.STATUS, "in", ["active", "pending"])
    >>> query.sort_by(SearchField.CREATED_AT, descending=True)
    >>> results = client.search_candidacies(query, limit=50)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SearchField(Enum):
    """
    Searchable fields for HERP resources

    Common fields:
    - NAME: Candidate name
    - EMAIL: Email address
    - PHONE: Phone number
    - STATUS: Candidacy status
    - STAGE: Hiring stage
    - CREATED_AT: Creation timestamp
    - UPDATED_AT: Modification timestamp

    Candidacy-specific:
    - REQUISITION_ID: Job requisition ID
    - ASSIGNED_TO: Assigned recruiter/team member

    Contact-specific:
    - CONTACT_TYPE: Interview type (technical_interview, phone_screen, etc.)
    - SCHEDULED_AT: Scheduled time
    """

    # Common fields
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    STATUS = "status"
    STAGE = "stage"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

    # Candidacy-specific
    REQUISITION_ID = "requisition_id"
    ASSIGNED_TO = "assigned_to"

    # Contact-specific
    CONTACT_TYPE = "contact_type"
    SCHEDULED_AT = "scheduled_at"

    # File-specific
    FILE_TYPE = "file_type"


class SearchOperator(Enum):
    """
    Search operators

    EQUALS: Exact match (==)
    NOT_EQUALS: Not equal (!=)
    CONTAINS: Contains substring (case-insensitive)
    STARTS_WITH: Starts with substring
    ENDS_WITH: Ends with substring
    IN: Value in list
    NOT_IN: Value not in list
    GREATER_THAN: Greater than (>)
    LESS_THAN: Less than (<)
    GREATER_OR_EQUAL: Greater than or equal (>=)
    LESS_OR_EQUAL: Less than or equal (<=)
    IS_NULL: Value is null/None
    IS_NOT_NULL: Value is not null/None
    """

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class SearchFilter:
    """
    A single search filter

    Attributes:
        field: Field to filter on
        operator: Comparison operator
        value: Value to compare against
    """

    field: SearchField
    operator: SearchOperator
    value: Any

    def matches(self, record: Dict[str, Any]) -> bool:
        """
        Check if a record matches this filter

        Args:
            record: Record to check

        Returns:
            True if record matches filter
        """
        field_value = record.get(self.field.value)

        if self.operator == SearchOperator.EQUALS:
            return field_value == self.value

        elif self.operator == SearchOperator.NOT_EQUALS:
            return field_value != self.value

        elif self.operator == SearchOperator.CONTAINS:
            if field_value is None:
                return False
            return str(self.value).lower() in str(field_value).lower()

        elif self.operator == SearchOperator.STARTS_WITH:
            if field_value is None:
                return False
            return str(field_value).lower().startswith(str(self.value).lower())

        elif self.operator == SearchOperator.ENDS_WITH:
            if field_value is None:
                return False
            return str(field_value).lower().endswith(str(self.value).lower())

        elif self.operator == SearchOperator.IN:
            return field_value in self.value

        elif self.operator == SearchOperator.NOT_IN:
            return field_value not in self.value

        elif self.operator == SearchOperator.GREATER_THAN:
            return field_value is not None and field_value > self.value

        elif self.operator == SearchOperator.LESS_THAN:
            return field_value is not None and field_value < self.value

        elif self.operator == SearchOperator.GREATER_OR_EQUAL:
            return field_value is not None and field_value >= self.value

        elif self.operator == SearchOperator.LESS_OR_EQUAL:
            return field_value is not None and field_value <= self.value

        elif self.operator == SearchOperator.IS_NULL:
            return field_value is None

        elif self.operator == SearchOperator.IS_NOT_NULL:
            return field_value is not None

        else:
            raise ValueError(f"Unknown operator: {self.operator}")


@dataclass
class SortOrder:
    """
    Sort order for search results

    Attributes:
        field: Field to sort by
        descending: Sort in descending order (default: False)
    """

    field: SearchField
    descending: bool = False


@dataclass
class SearchQuery:
    """
    Search query builder

    Provides a fluent interface for building complex search queries.

    Example:
        >>> query = SearchQuery()
        >>> query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")
        >>> query.add_filter(SearchField.STATUS, SearchOperator.IN, ["active", "pending"])
        >>> query.sort_by(SearchField.CREATED_AT, descending=True)
        >>> query.limit(50)
    """

    filters: List[SearchFilter] = field(default_factory=list)
    sort_orders: List[SortOrder] = field(default_factory=list)
    max_results: Optional[int] = None

    def add_filter(
        self,
        field: SearchField,
        operator: SearchOperator,
        value: Any = None,
    ) -> "SearchQuery":
        """
        Add a filter to the query

        Args:
            field: Field to filter on
            operator: Comparison operator
            value: Value to compare against (not needed for IS_NULL/IS_NOT_NULL)

        Returns:
            Self for method chaining

        Example:
            >>> query.add_filter(SearchField.NAME, SearchOperator.CONTAINS, "John")
            >>> query.add_filter(SearchField.EMAIL, SearchOperator.EQUALS, "john@example.com")
        """
        self.filters.append(SearchFilter(field, operator, value))
        return self

    def sort_by(
        self,
        field: SearchField,
        descending: bool = False,
    ) -> "SearchQuery":
        """
        Add a sort order to the query

        Args:
            field: Field to sort by
            descending: Sort in descending order

        Returns:
            Self for method chaining

        Example:
            >>> query.sort_by(SearchField.CREATED_AT, descending=True)
        """
        self.sort_orders.append(SortOrder(field, descending))
        return self

    def limit(self, max_results: int) -> "SearchQuery":
        """
        Limit number of results

        Args:
            max_results: Maximum number of results to return

        Returns:
            Self for method chaining

        Example:
            >>> query.limit(50)
        """
        self.max_results = max_results
        return self

    def matches(self, record: Dict[str, Any]) -> bool:
        """
        Check if a record matches all filters

        Args:
            record: Record to check

        Returns:
            True if record matches all filters
        """
        return all(f.matches(record) for f in self.filters)

    def apply(
        self,
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Apply query to a list of records (filter, sort, limit)

        Args:
            records: Records to query

        Returns:
            Filtered, sorted, and limited results

        Example:
            >>> results = query.apply(all_candidacies)
        """
        # Filter
        results = [r for r in records if self.matches(r)]

        # Sort
        for sort_order in reversed(self.sort_orders):  # Apply in reverse order
            results.sort(
                key=lambda r: r.get(sort_order.field.value) or "",
                reverse=sort_order.descending,
            )

        # Limit
        if self.max_results is not None:
            results = results[: self.max_results]

        return results


class SearchHelper:
    """
    Helper class for common search operations

    Provides shortcuts for frequently used searches.
    """

    @staticmethod
    def by_name(name: str, exact: bool = False) -> SearchQuery:
        """
        Search by name

        Args:
            name: Name to search for
            exact: Exact match (default: False, uses contains)

        Returns:
            SearchQuery

        Example:
            >>> query = SearchHelper.by_name("John Doe")
            >>> query = SearchHelper.by_name("john@example.com", exact=True)
        """
        query = SearchQuery()
        operator = SearchOperator.EQUALS if exact else SearchOperator.CONTAINS
        query.add_filter(SearchField.NAME, operator, name)
        return query

    @staticmethod
    def by_email(email: str) -> SearchQuery:
        """
        Search by email (exact match)

        Args:
            email: Email address

        Returns:
            SearchQuery

        Example:
            >>> query = SearchHelper.by_email("john@example.com")
        """
        query = SearchQuery()
        query.add_filter(SearchField.EMAIL, SearchOperator.EQUALS, email)
        return query

    @staticmethod
    def by_status(statuses: List[str]) -> SearchQuery:
        """
        Search by status (multiple allowed)

        Args:
            statuses: List of statuses to match

        Returns:
            SearchQuery

        Example:
            >>> query = SearchHelper.by_status(["active", "pending"])
        """
        query = SearchQuery()
        query.add_filter(SearchField.STATUS, SearchOperator.IN, statuses)
        return query

    @staticmethod
    def created_since(timestamp: str, limit: Optional[int] = None) -> SearchQuery:
        """
        Search for records created since timestamp

        Args:
            timestamp: ISO timestamp
            limit: Optional result limit

        Returns:
            SearchQuery

        Example:
            >>> query = SearchHelper.created_since("2026-01-01T00:00:00Z", limit=100)
        """
        query = SearchQuery()
        query.add_filter(
            SearchField.CREATED_AT, SearchOperator.GREATER_OR_EQUAL, timestamp
        )
        query.sort_by(SearchField.CREATED_AT, descending=True)

        if limit is not None:
            query.limit(limit)

        return query

    @staticmethod
    def updated_since(timestamp: str, limit: Optional[int] = None) -> SearchQuery:
        """
        Search for records updated since timestamp

        Args:
            timestamp: ISO timestamp
            limit: Optional result limit

        Returns:
            SearchQuery

        Example:
            >>> query = SearchHelper.updated_since("2026-01-26T00:00:00Z", limit=50)
        """
        query = SearchQuery()
        query.add_filter(
            SearchField.UPDATED_AT, SearchOperator.GREATER_OR_EQUAL, timestamp
        )
        query.sort_by(SearchField.UPDATED_AT, descending=True)

        if limit is not None:
            query.limit(limit)

        return query
