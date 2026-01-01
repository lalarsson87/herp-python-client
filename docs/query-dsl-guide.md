# HERP Query DSL Guide

## Overview

The HERP Query DSL provides a fluent, type-safe interface for building complex search queries. It supports field filters, logical operators (AND, OR, NOT), nested queries, and type-safe field accessors.

## Benefits

✅ **Type-Safe**: Full IDE autocomplete with CandidacyQuery
✅ **Readable**: Fluent interface reads like natural language
✅ **Powerful**: Supports complex nested queries with logical operators
✅ **Flexible**: Works with both sync and async clients
✅ **Backward Compatible**: Legacy filter syntax still works

## Quick Start

### Simple Query

```python
from src.core.herp import HerpClient, CandidacyQuery
from src.core.utils.config import HerpConfig

client = HerpClient(config)

# Simple filter
query = CandidacyQuery().by_email("jane@example.com")
results = client.candidacies.search(query)

# Multiple filters (AND by default)
query = (
    CandidacyQuery()
    .by_requisition("req_001")
    .by_step("interview")
    .active_only()
)
results = client.candidacies.search(query)
```

### Complex Query

```python
# OR queries
query = (
    CandidacyQuery()
    .or_(
        CandidacyQuery().by_email("jane@example.com"),
        CandidacyQuery().by_email("john@example.com")
    )
    .by_step("interview")
)
results = client.candidacies.search(query)

# Nested queries with NOT
query = (
    CandidacyQuery()
    .by_name("Engineer")
    .not_(CandidacyQuery().by_status("terminated"))
)
results = client.candidacies.search(query)
```

## API Reference

### FilterOperator

Available filter operators for field comparisons:

| Operator | Description | Example |
|----------|-------------|---------|
| `EQUALS` | Exact match | `equals("step", "interview")` |
| `NOT_EQUALS` | Not equal | `not_equals("status", "terminated")` |
| `CONTAINS` | Substring match | `contains("name", "Engineer")` |
| `NOT_CONTAINS` | Doesn't contain | `not_contains("email", "@competitor.com")` |
| `STARTS_WITH` | Starts with | `starts_with("name", "Jane")` |
| `ENDS_WITH` | Ends with | `ends_with("email", "@example.com")` |
| `IN` | In list | `in_list("step", ["interview", "offer"])` |
| `NOT_IN` | Not in list | `not_in_list("status", ["terminated", "rejected"])` |
| `GREATER_THAN` | Greater than | `greater_than("created_at", "2026-01-01")` |
| `GREATER_THAN_OR_EQUAL` | >= | `greater_than_or_equal("years_exp", 5)` |
| `LESS_THAN` | Less than | `less_than("created_at", "2026-12-31")` |
| `LESS_THAN_OR_EQUAL` | <= | `less_than_or_equal("age", 65)` |
| `BETWEEN` | Range (inclusive) | `between("created_at", "2026-01-01", "2026-12-31")` |
| `IS_NULL` | Is null/empty | `is_null("termination_date")` |
| `IS_NOT_NULL` | Not null/empty | `is_not_null("email")` |

### LogicalOperator

Logical operators for combining filters:

| Operator | Description | Example |
|----------|-------------|---------|
| `AND` | All must match (default) | `and_(query1, query2)` |
| `OR` | At least one must match | `or_(query1, query2)` |
| `NOT` | Negate query | `not_(query)` |

### Query

Generic query builder for any entity.

**Constructor**:
```python
from src.core.herp import Query
query = Query()
```

**Field Filter Methods**:

```python
# Comparison
query.equals(field, value)
query.not_equals(field, value)
query.contains(field, value)
query.not_contains(field, value)
query.starts_with(field, value)
query.ends_with(field, value)

# List operations
query.in_list(field, [value1, value2, ...])
query.not_in_list(field, [value1, value2, ...])

# Numeric/date comparisons
query.greater_than(field, value)
query.greater_than_or_equal(field, value)
query.less_than(field, value)
query.less_than_or_equal(field, value)
query.between(field, min_value, max_value)

# Null checks
query.is_null(field)
query.is_not_null(field)
```

**Logical Operators**:

```python
# AND (default when chaining)
query = (
    Query()
    .equals("field1", "value1")
    .equals("field2", "value2")
)
# Explicit AND
query = Query().and_(
    Query().equals("field1", "value1"),
    Query().equals("field2", "value2")
)

# OR
query = Query().or_(
    Query().equals("field1", "value1"),
    Query().equals("field1", "value2")
)

# NOT
query = Query().not_(Query().equals("status", "terminated"))
```

### CandidacyQuery

Specialized query for candidacies with typed field methods.

**Constructor**:
```python
from src.core.herp import CandidacyQuery
query = CandidacyQuery()

# Or use convenience function
from src.core.herp import candidacy_query
query = candidacy_query()
```

**Type-Safe Methods**:

```python
# Basic filters
query.by_email(email: str)
query.by_name(name: str)  # Contains match
query.by_exact_name(name: str)  # Exact match
query.by_requisition(requisition_id: str)
query.by_step(step: str)
query.by_steps(steps: List[str])  # Multiple steps (OR)
query.by_status(status: Literal["active", "hired", "terminated"])

# Convenience filters
query.active_only()
query.hired_only()
query.terminated_only()

# Tags
query.with_tags(tags: List[str])  # Must have all tags
query.with_any_tag(tags: List[str])  # Must have at least one tag

# Dates
query.created_after(date: Union[str, datetime])
query.created_before(date: Union[str, datetime])
query.created_between(start_date, end_date)
query.updated_after(date: Union[str, datetime])

# Null checks
query.has_email()
query.no_email()
```

## Usage Examples

### Simple Filters

```python
from src.core.herp import HerpClient, CandidacyQuery

client = HerpClient(config)

# Find active candidates in interview stage
query = CandidacyQuery().by_step("interview").active_only()
results = client.candidacies.search(query)

# Find candidates for specific requisition
query = CandidacyQuery().by_requisition("req_001")
results = client.candidacies.search(query)

# Find candidates with email
query = CandidacyQuery().has_email().active_only()
results = client.candidacies.search(query)
```

### Multiple Filters (AND)

```python
# Chaining filters (AND by default)
query = (
    CandidacyQuery()
    .by_requisition("req_001")
    .by_step("interview")
    .active_only()
    .created_after("2026-01-01")
)
results = client.candidacies.search(query)

# Find candidates with specific tags
query = (
    CandidacyQuery()
    .with_tags(["backend", "senior"])
    .active_only()
)
results = client.candidacies.search(query)
```

### OR Queries

```python
# Find candidates in interview OR offer stage
query = CandidacyQuery().by_steps(["interview", "offer"])
results = client.candidacies.search(query)

# Find candidates with specific emails (OR)
query = (
    CandidacyQuery()
    .or_(
        CandidacyQuery().by_email("jane@example.com"),
        CandidacyQuery().by_email("john@example.com")
    )
)
results = client.candidacies.search(query)

# Complex OR with AND
query = (
    CandidacyQuery()
    .or_(
        CandidacyQuery().by_step("interview"),
        CandidacyQuery().by_step("offer")
    )
    .by_requisition("req_001")  # AND this
    .active_only()  # AND this
)
results = client.candidacies.search(query)
```

### NOT Queries

```python
# Find active candidates not in terminated status
query = (
    CandidacyQuery()
    .active_only()
    .not_(CandidacyQuery().by_step("rejected"))
)
results = client.candidacies.search(query)

# Find candidates without specific tag
query = (
    CandidacyQuery()
    .active_only()
    .not_(CandidacyQuery().with_tags(["rejected"]))
)
results = client.candidacies.search(query)
```

### Date Range Queries

```python
from datetime import datetime, timedelta

# Find candidates created in last 7 days
seven_days_ago = datetime.now() - timedelta(days=7)
query = CandidacyQuery().created_after(seven_days_ago)
results = client.candidacies.search(query)

# Find candidates created in specific month
query = (
    CandidacyQuery()
    .created_between("2026-01-01", "2026-01-31")
    .active_only()
)
results = client.candidacies.search(query)

# Find candidates updated recently
query = CandidacyQuery().updated_after("2026-01-15")
results = client.candidacies.search(query)
```

### Complex Nested Queries

```python
# (Interview OR Offer) AND (Senior Backend)
query = (
    CandidacyQuery()
    .or_(
        CandidacyQuery().by_step("interview"),
        CandidacyQuery().by_step("offer")
    )
    .with_tags(["backend", "senior"])
)
results = client.candidacies.search(query)

# Active AND NOT terminated AND (Engineer OR Developer)
query = (
    CandidacyQuery()
    .active_only()
    .not_(CandidacyQuery().by_status("terminated"))
    .or_(
        CandidacyQuery().contains("name", "Engineer"),
        CandidacyQuery().contains("name", "Developer")
    )
)
results = client.candidacies.search(query)

# Complex filtering with multiple conditions
query = (
    CandidacyQuery()
    .or_(
        # Group 1: Engineering roles
        CandidacyQuery()
            .with_any_tag(["backend", "frontend", "fullstack"])
            .by_steps(["interview", "offer"]),
        # Group 2: Data roles
        CandidacyQuery()
            .with_any_tag(["data", "ml", "ai"])
            .by_steps(["interview", "offer"])
    )
    .active_only()
    .created_after("2026-01-01")
)
results = client.candidacies.search(query)
```

### Async Usage

```python
import asyncio
from src.core.herp import AsyncHerpClient, CandidacyQuery

async def main():
    config = HerpConfig.from_env()

    async with AsyncHerpClient(config) as client:
        # Same query syntax works with async
        query = (
            CandidacyQuery()
            .by_requisition("req_001")
            .active_only()
        )

        results = await client.candidacies.search(query)

        for candidacy in results:
            print(f"{candidacy['name']} - {candidacy['step']}")

asyncio.run(main())
```

### With Limit

```python
# Get top 10 active candidates
query = CandidacyQuery().active_only()
results = client.candidacies.search(query, limit=10)

# Get latest 20 candidates
query = CandidacyQuery().created_after("2026-01-01")
results = client.candidacies.search(query, limit=20)
```

## Advanced Patterns

### Building Queries Dynamically

```python
def build_query(
    requisition_id: Optional[str] = None,
    steps: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    active_only: bool = True
) -> CandidacyQuery:
    """Build query based on optional parameters"""
    query = CandidacyQuery()

    if requisition_id:
        query = query.by_requisition(requisition_id)

    if steps:
        query = query.by_steps(steps)

    if tags:
        query = query.with_tags(tags)

    if active_only:
        query = query.active_only()

    return query

# Use
query = build_query(
    requisition_id="req_001",
    steps=["interview", "offer"],
    tags=["backend"]
)
results = client.candidacies.search(query)
```

### Reusable Query Fragments

```python
# Define reusable fragments
def active_engineering_candidates():
    """Query for active engineering candidates"""
    return (
        CandidacyQuery()
        .active_only()
        .with_any_tag(["backend", "frontend", "fullstack"])
    )

def recent_candidates(days=7):
    """Query for candidates created recently"""
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    return CandidacyQuery().created_after(cutoff_date)

# Combine fragments
query = (
    active_engineering_candidates()
    .and_(recent_candidates(days=14))
    .by_steps(["interview", "offer"])
)
results = client.candidacies.search(query)
```

### Query Inspection

```python
# Convert query to dict for debugging
query = (
    CandidacyQuery()
    .by_email("jane@example.com")
    .active_only()
)

query_dict = query.to_dict()
print(query_dict)
# {
#     'logical_operator': 'and',
#     'filters': [
#         {'field': 'email', 'operator': 'eq', 'value': 'jane@example.com'},
#         {'field': 'status', 'operator': 'eq', 'value': 'active'}
#     ]
# }

# Convert to REST params
rest_params = query.to_rest_params()
print(rest_params)
# {'email__eq': 'jane@example.com', 'status__eq': 'active'}
```

## Comparison with Legacy Filters

### Before (Legacy Filters)

```python
# Limited filtering
results = client.candidacies.search(
    email="jane@example.com",
    status="active"
)

# Can't do OR queries
# Can't do NOT queries
# Can't do range queries
# Can't do nested queries
# No type safety
```

### After (Query DSL)

```python
# Powerful, type-safe filtering
query = (
    CandidacyQuery()
    .or_(
        CandidacyQuery().by_email("jane@example.com"),
        CandidacyQuery().by_email("john@example.com")
    )
    .active_only()
    .created_between("2026-01-01", "2026-12-31")
    .not_(CandidacyQuery().with_tags(["rejected"]))
)
results = client.candidacies.search(query)

# ✅ OR queries supported
# ✅ NOT queries supported
# ✅ Range queries supported
# ✅ Nested queries supported
# ✅ Full type safety with IDE autocomplete
```

## Best Practices

### 1. Use CandidacyQuery for Candidacies

```python
# ✅ Good - type-safe with autocomplete
query = CandidacyQuery().by_email("jane@example.com")

# ⭕ OK - but no type hints
query = Query().equals("email", "jane@example.com")
```

### 2. Chain Filters for Readability

```python
# ✅ Good - readable
query = (
    CandidacyQuery()
    .by_requisition("req_001")
    .by_step("interview")
    .active_only()
)

# ⭕ OK - but harder to read
query = CandidacyQuery().by_requisition("req_001").by_step("interview").active_only()
```

### 3. Use Convenience Methods

```python
# ✅ Good - use convenience method
query = CandidacyQuery().active_only()

# ⭕ OK - but more verbose
query = CandidacyQuery().by_status("active")
```

### 4. Break Complex Queries into Parts

```python
# ✅ Good - readable parts
engineering_query = CandidacyQuery().with_any_tag(["backend", "frontend"])
active_query = CandidacyQuery().active_only()
recent_query = CandidacyQuery().created_after("2026-01-01")

final_query = Query().and_(engineering_query, active_query, recent_query)

# ❌ Bad - hard to read
query = CandidacyQuery().with_any_tag(["backend", "frontend"]).active_only().created_after("2026-01-01").by_steps(["interview", "offer"])
```

## Performance Tips

1. **Add filters early**: More restrictive filters first
2. **Use limit**: Limit results if you don't need all
3. **Cache results**: Reuse query results when possible
4. **Batch queries**: Use async for multiple queries

```python
# ✅ Good - most restrictive first
query = (
    CandidacyQuery()
    .by_requisition("req_001")  # Narrow down first
    .active_only()
    .by_step("interview")
)

# Use limit
results = client.candidacies.search(query, limit=10)
```

## Troubleshooting

### Query Returns No Results

Check filter values:
```python
# Debug query
query_dict = query.to_dict()
print("Query:", query_dict)

# Check individual filters
query1 = CandidacyQuery().by_email("jane@example.com")
results1 = client.candidacies.search(query1)
print(f"Email filter: {len(results1)} results")

query2 = CandidacyQuery().active_only()
results2 = client.candidacies.search(query2)
print(f"Active filter: {len(results2)} results")
```

### Query Too Slow

Add more restrictive filters or use limit:
```python
# ⚠️ Slow - fetches all then filters
query = CandidacyQuery().contains("name", "Engineer")
results = client.candidacies.search(query)

# ✅ Faster - limit results
results = client.candidacies.search(query, limit=100)

# ✅ Faster - add more filters
query = (
    CandidacyQuery()
    .by_requisition("req_001")  # Narrow down
    .contains("name", "Engineer")
)
results = client.candidacies.search(query)
```

## Summary

✅ **Fluent, type-safe query builder**
✅ **Support for complex queries (AND, OR, NOT)**
✅ **14+ filter operators**
✅ **Nested queries**
✅ **Works with sync and async clients**
✅ **Backward compatible with legacy filters**

The Query DSL makes it easy to build complex, type-safe searches while maintaining readability and flexibility.
