#!/usr/bin/env python3
"""
HERP Query DSL

Provides a fluent, type-safe query builder for complex searches.

Supports:
- Field filters (equals, contains, in, range, etc.)
- Logical operators (AND, OR, NOT)
- Nested queries
- Type-safe with autocomplete
- Serialization to REST params, GraphQL, etc.
"""

from typing import Dict, Any, List, Optional, Union, Literal
from datetime import datetime
from enum import Enum


class FilterOperator(str, Enum):
    """Filter operators for field comparisons"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class LogicalOperator(str, Enum):
    """Logical operators for combining filters"""
    AND = "and"
    OR = "or"
    NOT = "not"


class FieldFilter:
    """
    Represents a single field filter

    Usage:
        FieldFilter("email", FilterOperator.EQUALS, "jane@example.com")
        FieldFilter("name", FilterOperator.CONTAINS, "Doe")
        FieldFilter("created_at", FilterOperator.BETWEEN, ["2026-01-01", "2026-12-31"])
    """

    def __init__(
        self,
        field: str,
        operator: FilterOperator,
        value: Any = None
    ):
        """
        Initialize field filter

        Args:
            field: Field name
            operator: Filter operator
            value: Value to compare (not needed for IS_NULL, IS_NOT_NULL)
        """
        self.field = field
        self.operator = operator
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "field": self.field,
            "operator": self.operator.value,
        }

        if self.value is not None:
            result["value"] = self.value

        return result

    def __repr__(self) -> str:
        return f"FieldFilter({self.field} {self.operator.value} {self.value})"


class Query:
    """
    Fluent query builder for complex searches

    Usage:
        # Simple filter
        query = Query().equals("email", "jane@example.com")

        # Multiple filters (AND by default)
        query = (
            Query()
            .equals("requisition_id", "req_001")
            .contains("name", "Engineer")
            .in_list("step", ["interview", "offer"])
        )

        # Logical operators
        query = (
            Query()
            .or_(
                Query().equals("step", "interview"),
                Query().equals("step", "offer")
            )
            .equals("status", "active")
        )

        # Complex nested query
        query = (
            Query()
            .and_(
                Query().contains("name", "Engineer"),
                Query().or_(
                    Query().equals("email", "jane@example.com"),
                    Query().equals("email", "john@example.com")
                )
            )
            .not_(Query().equals("status", "terminated"))
        )

        # Range queries
        query = (
            Query()
            .between("created_at", "2026-01-01", "2026-12-31")
            .greater_than("years_experience", 5)
        )

        # Null checks
        query = Query().is_not_null("email").is_null("termination_date")

        # Execute query
        results = client.candidacies.search(query)

        # Or use async
        results = await async_client.candidacies.search(query)
    """

    def __init__(self):
        """Initialize empty query"""
        self.filters: List[Union[FieldFilter, "Query"]] = []
        self.logical_operator: LogicalOperator = LogicalOperator.AND
        self.negated: bool = False

    # Field filter methods

    def equals(self, field: str, value: Any) -> "Query":
        """
        Add equals filter

        Args:
            field: Field name
            value: Value to match

        Returns:
            Query for chaining
        """
        self.filters.append(FieldFilter(field, FilterOperator.EQUALS, value))
        return self

    def not_equals(self, field: str, value: Any) -> "Query":
        """Add not equals filter"""
        self.filters.append(FieldFilter(field, FilterOperator.NOT_EQUALS, value))
        return self

    def contains(self, field: str, value: str) -> "Query":
        """Add contains filter (substring match)"""
        self.filters.append(FieldFilter(field, FilterOperator.CONTAINS, value))
        return self

    def not_contains(self, field: str, value: str) -> "Query":
        """Add not contains filter"""
        self.filters.append(FieldFilter(field, FilterOperator.NOT_CONTAINS, value))
        return self

    def starts_with(self, field: str, value: str) -> "Query":
        """Add starts with filter"""
        self.filters.append(FieldFilter(field, FilterOperator.STARTS_WITH, value))
        return self

    def ends_with(self, field: str, value: str) -> "Query":
        """Add ends with filter"""
        self.filters.append(FieldFilter(field, FilterOperator.ENDS_WITH, value))
        return self

    def in_list(self, field: str, values: List[Any]) -> "Query":
        """
        Add in list filter

        Args:
            field: Field name
            values: List of values to match

        Returns:
            Query for chaining
        """
        self.filters.append(FieldFilter(field, FilterOperator.IN, values))
        return self

    def not_in_list(self, field: str, values: List[Any]) -> "Query":
        """Add not in list filter"""
        self.filters.append(FieldFilter(field, FilterOperator.NOT_IN, values))
        return self

    def greater_than(self, field: str, value: Any) -> "Query":
        """Add greater than filter"""
        self.filters.append(FieldFilter(field, FilterOperator.GREATER_THAN, value))
        return self

    def greater_than_or_equal(self, field: str, value: Any) -> "Query":
        """Add greater than or equal filter"""
        self.filters.append(FieldFilter(field, FilterOperator.GREATER_THAN_OR_EQUAL, value))
        return self

    def less_than(self, field: str, value: Any) -> "Query":
        """Add less than filter"""
        self.filters.append(FieldFilter(field, FilterOperator.LESS_THAN, value))
        return self

    def less_than_or_equal(self, field: str, value: Any) -> "Query":
        """Add less than or equal filter"""
        self.filters.append(FieldFilter(field, FilterOperator.LESS_THAN_OR_EQUAL, value))
        return self

    def between(self, field: str, min_value: Any, max_value: Any) -> "Query":
        """
        Add between filter (inclusive)

        Args:
            field: Field name
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)

        Returns:
            Query for chaining
        """
        self.filters.append(FieldFilter(field, FilterOperator.BETWEEN, [min_value, max_value]))
        return self

    def is_null(self, field: str) -> "Query":
        """Add is null filter"""
        self.filters.append(FieldFilter(field, FilterOperator.IS_NULL))
        return self

    def is_not_null(self, field: str) -> "Query":
        """Add is not null filter"""
        self.filters.append(FieldFilter(field, FilterOperator.IS_NOT_NULL))
        return self

    # Logical operators

    def and_(self, *queries: "Query") -> "Query":
        """
        Combine queries with AND

        Args:
            *queries: Queries to combine with AND

        Returns:
            Query for chaining
        """
        for query in queries:
            self.filters.append(query)
        self.logical_operator = LogicalOperator.AND
        return self

    def or_(self, *queries: "Query") -> "Query":
        """
        Combine queries with OR

        Args:
            *queries: Queries to combine with OR

        Returns:
            Query for chaining
        """
        for query in queries:
            self.filters.append(query)
        self.logical_operator = LogicalOperator.OR
        return self

    def not_(self, query: "Query") -> "Query":
        """
        Negate a query

        Args:
            query: Query to negate

        Returns:
            Query for chaining
        """
        query.negated = True
        self.filters.append(query)
        return self

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert query to dictionary representation

        Returns:
            Dictionary representation of query
        """
        result = {
            "logical_operator": self.logical_operator.value,
            "filters": [
                f.to_dict() if isinstance(f, FieldFilter) else f.to_dict()
                for f in self.filters
            ]
        }

        if self.negated:
            result["negated"] = True

        return result

    def to_rest_params(self) -> Dict[str, Any]:
        """
        Convert query to REST API query parameters

        Returns:
            Dictionary of query parameters for REST API
        """
        params = {}

        # Simple case: only field filters with AND
        if all(isinstance(f, FieldFilter) for f in self.filters) and self.logical_operator == LogicalOperator.AND:
            for filter in self.filters:
                if isinstance(filter, FieldFilter):
                    param_key = f"{filter.field}__{filter.operator.value}"
                    params[param_key] = filter.value

        # Complex case: serialize to JSON
        else:
            params["query"] = self.to_dict()

        return params

    def __repr__(self) -> str:
        return f"Query({self.logical_operator.value}, {len(self.filters)} filters)"


class CandidacyQuery(Query):
    """
    Specialized query for candidacies with typed field methods

    Provides type-safe field accessors for candidacy fields.

    Usage:
        query = (
            CandidacyQuery()
            .by_email("jane@example.com")
            .by_requisition("req_001")
            .by_step("interview")
            .active_only()
        )
    """

    def by_email(self, email: str) -> "CandidacyQuery":
        """Filter by candidate email"""
        return self.equals("email", email)

    def by_name(self, name: str) -> "CandidacyQuery":
        """Filter by candidate name"""
        return self.contains("name", name)

    def by_exact_name(self, name: str) -> "CandidacyQuery":
        """Filter by exact candidate name"""
        return self.equals("name", name)

    def by_requisition(self, requisition_id: str) -> "CandidacyQuery":
        """Filter by requisition ID"""
        return self.equals("requisition_id", requisition_id)

    def by_step(self, step: str) -> "CandidacyQuery":
        """Filter by hiring step"""
        return self.equals("step", step)

    def by_steps(self, steps: List[str]) -> "CandidacyQuery":
        """Filter by multiple hiring steps (OR)"""
        return self.in_list("step", steps)

    def by_status(self, status: Literal["active", "hired", "terminated"]) -> "CandidacyQuery":
        """Filter by status"""
        return self.equals("status", status)

    def active_only(self) -> "CandidacyQuery":
        """Filter for active candidacies only"""
        return self.equals("status", "active")

    def hired_only(self) -> "CandidacyQuery":
        """Filter for hired candidacies only"""
        return self.equals("status", "hired")

    def terminated_only(self) -> "CandidacyQuery":
        """Filter for terminated candidacies only"""
        return self.equals("status", "terminated")

    def with_tags(self, tags: List[str]) -> "CandidacyQuery":
        """Filter by tags (must have all tags)"""
        for tag in tags:
            self.contains("tags", tag)
        return self

    def with_any_tag(self, tags: List[str]) -> "CandidacyQuery":
        """Filter by tags (must have at least one tag)"""
        # Create OR query for tags
        tag_queries = [Query().contains("tags", tag) for tag in tags]
        return self.or_(*tag_queries)

    def created_after(self, date: Union[str, datetime]) -> "CandidacyQuery":
        """Filter by creation date (after)"""
        if isinstance(date, datetime):
            date = date.isoformat()
        return self.greater_than_or_equal("created_at", date)

    def created_before(self, date: Union[str, datetime]) -> "CandidacyQuery":
        """Filter by creation date (before)"""
        if isinstance(date, datetime):
            date = date.isoformat()
        return self.less_than_or_equal("created_at", date)

    def created_between(
        self,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime]
    ) -> "CandidacyQuery":
        """Filter by creation date range"""
        if isinstance(start_date, datetime):
            start_date = start_date.isoformat()
        if isinstance(end_date, datetime):
            end_date = end_date.isoformat()
        return self.between("created_at", start_date, end_date)

    def updated_after(self, date: Union[str, datetime]) -> "CandidacyQuery":
        """Filter by update date (after)"""
        if isinstance(date, datetime):
            date = date.isoformat()
        return self.greater_than_or_equal("updated_at", date)

    def has_email(self) -> "CandidacyQuery":
        """Filter for candidacies with email"""
        return self.is_not_null("email")

    def no_email(self) -> "CandidacyQuery":
        """Filter for candidacies without email"""
        return self.is_null("email")


# Convenience functions

def query() -> Query:
    """Create a new generic query"""
    return Query()


def candidacy_query() -> CandidacyQuery:
    """Create a new candidacy query"""
    return CandidacyQuery()
