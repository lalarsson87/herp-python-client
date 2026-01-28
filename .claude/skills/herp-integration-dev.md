# HERP Integration Development Skill

**Skill ID**: `herp-integration-dev`
**Purpose**: Guide development of HERP API integrations and workflows
**When to use**: Building new integrations, implementing features, debugging issues

## Usage

```
/herp-integration-dev [task] [context]
```

**Tasks**:
- `implement` - Implement new HERP integration feature
- `debug` - Debug integration issues
- `optimize` - Optimize performance
- `migrate` - Migrate data or upgrade integration

## What This Skill Does

1. **Guides implementation** - Provides patterns and best practices
2. **References real code** - Points to actual implementation examples
3. **Validates approach** - Checks against HERP API constraints
4. **Suggests optimizations** - Performance and reliability improvements
5. **Documents decisions** - Maintains implementation history

## Core Integration Patterns

### 1. Client Initialization

**Location**: `src/core/herp/client.py`

```python
from src.core.herp.client import HerpClient

# Basic initialization
client = HerpClient(
    api_token=os.getenv("HERP_API_TOKEN"),
    base_url="https://public-api.herp.cloud/hire/public",
    timeout=30.0
)

# Advanced configuration
from src.core.herp.config import HerpConfig

config = HerpConfig(
    api_token=token,
    rate_limit=100,  # requests per minute
    max_retries=3,
    timeout=30.0,
    user_agent="MyApp/1.0"
)
client = HerpClient(config=config)
```

### 2. Rate Limiting

**Location**: `src/core/herp/async_rate_limiter.py`

```python
from src.core.herp.async_rate_limiter import AsyncRateLimiter

# HERP API limits: 100 req/min
rate_limiter = AsyncRateLimiter(
    requests_per_minute=100,
    requests_per_second=2  # Smoothing
)

async def fetch_with_rate_limit(candidacy_id):
    await rate_limiter.acquire()
    return await client.get_candidacy(candidacy_id)
```

### 3. Error Handling

**Location**: `src/core/errors/exceptions.py`

```python
from src.core.errors.exceptions import (
    HerpAPIError,
    HerpRateLimitError,
    HerpNotFoundError,
    is_transient_error,
    is_permanent_error
)

try:
    candidacy = client.get_candidacy(id)
except HerpRateLimitError as e:
    # Transient - retry after delay
    time.sleep(e.retry_after or 60)
    candidacy = client.get_candidacy(id)
except HerpNotFoundError:
    # Permanent - don't retry
    logger.error(f"Candidacy {id} not found")
    return None
except HerpAPIError as e:
    if is_transient_error(e):
        # Retry with backoff
        retry_with_backoff()
    else:
        # Log and skip
        logger.error(f"Permanent error: {e}")
```

### 4. Retry Logic

**Location**: `src/core/retry.py`

```python
from src.core.retry import RetryConfig, retry_with_config

# Configure retry behavior
retry_config = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2,
    jitter=True
)

@retry_with_config(retry_config)
async def fetch_candidacy(id: str):
    """Automatically retries on transient errors"""
    return await client.get_candidacy(id)
```

### 5. Batch Operations

**Location**: `src/core/herp/batch_client.py`

```python
from src.core.herp.batch_client import BatchHerpClient

batch_client = BatchHerpClient(
    client,
    max_workers=10,  # Parallel requests
    rate_limit=100   # Respect API limits
)

# Fetch multiple candidacies
result = batch_client.fetch_candidacies_batch(candidacy_ids)
print(f"Success: {result.success_rate:.1f}%")

# Access results
for candidacy in result.successful:
    process(candidacy)

for error in result.failed:
    logger.error(f"Failed {error.candidacy_id}: {error.error}")
```

### 6. Pagination

**Location**: `src/core/herp/mixins.py`

```python
from src.core.herp.client import HerpClient

# Manual pagination
limit = 100
offset = 0
all_candidacies = []

while True:
    response = client.list_candidacies(limit=limit, offset=offset)
    candidacies = response.get("data", [])

    if not candidacies:
        break

    all_candidacies.extend(candidacies)
    offset += limit

# Using pagination helper
for page in client.paginate_candidacies(limit=100):
    for candidacy in page["data"]:
        process(candidacy)
```

### 7. Async Operations

**Location**: `src/core/herp/async_base_client.py`

```python
from src.core.herp.async_client import AsyncHerpClient
import asyncio

async def fetch_multiple():
    async with AsyncHerpClient(api_token=token) as client:
        # Concurrent requests
        tasks = [
            client.get_candidacy(id)
            for id in candidacy_ids
        ]
        candidacies = await asyncio.gather(*tasks)
        return candidacies

# Run async code
candidacies = asyncio.run(fetch_multiple())
```

## Common Integration Scenarios

### Scenario 1: Sync Candidates from HERP to Notion

**Approach**:

```python
# 1. Fetch candidates from HERP
from src.core.herp.client import HerpClient

client = HerpClient(api_token=herp_token)
candidacies = client.list_candidacies(limit=100)

# 2. Transform to Notion format
notion_pages = []
for candidacy in candidacies["data"]:
    notion_page = {
        "Name": {"title": [{"text": {"content": candidacy["name"]}}]},
        "Email": {"email": candidacy.get("email")},
        "Status": {"select": {"name": candidacy["status"]}},
        "HERP ID": {"rich_text": [{"text": {"content": candidacy["id"]}}]},
        "Step": {"select": {"name": candidacy.get("step", "Unknown")}},
    }
    notion_pages.append(notion_page)

# 3. Batch create in Notion
from notion_client import Client

notion = Client(auth=notion_token)
for page_data in notion_pages:
    notion.pages.create(
        parent={"database_id": database_id},
        properties=page_data
    )
```

**Optimizations**:
- Use batch operations for HERP fetching
- Cache Notion database schema
- Track sync state to skip unchanged records
- Use async operations for I/O bound tasks

**See**: `.claude/agents/herp-notion-sync.md` for complete implementation

### Scenario 2: Monitor Candidate Progress

**Approach**:

```python
# Track candidates through hiring pipeline
from src.core.herp.client import HerpClient
from datetime import datetime, timedelta

client = HerpClient(api_token=token)

# Get candidates updated in last 24h
since = (datetime.now() - timedelta(days=1)).isoformat()
recent = client.list_candidacies(updatedSince=since)

# Categorize by step
by_step = {}
for candidacy in recent["data"]:
    step = candidacy.get("step", "Unknown")
    by_step.setdefault(step, []).append(candidacy)

# Alert on bottlenecks
for step, candidates in by_step.items():
    if len(candidates) > 10:
        print(f"⚠️  Bottleneck at {step}: {len(candidates)} candidates")
```

**Event Sourcing Approach**:

```python
# Track all state changes
from src.core.herp.events.aggregate import CandidacyAggregate

aggregate = CandidacyAggregate(candidacy_id)

# Replay events
events = event_store.load_events(candidacy_id)
for event in events:
    aggregate.apply(event)

# Current state
current_state = aggregate.to_candidacy()
print(f"Current step: {current_state.step}")
print(f"Step changes: {len([e for e in events if e.event_type == 'StepChanged'])}")
```

**See**: `src/core/herp/events/` for event sourcing implementation

### Scenario 3: Automated Candidate Evaluation

**Approach**:

```python
# 1. Fetch candidate and related data
candidacy = client.get_candidacy(id)
contacts = client.list_candidacy_contacts(id)
files = client.list_candidacy_files(id)

# 2. Extract evaluation data
evaluations = []
for contact in contacts["data"]:
    if "evaluations" in contact:
        evaluations.extend(contact["evaluations"])

# 3. Calculate scores
from statistics import mean

technical_scores = [
    eval.get("technicalScore", 0)
    for eval in evaluations
]
avg_technical = mean(technical_scores) if technical_scores else 0

cultural_scores = [
    eval.get("culturalFitScore", 0)
    for eval in evaluations
]
avg_cultural = mean(cultural_scores) if cultural_scores else 0

# 4. Generate recommendation
if avg_technical >= 4 and avg_cultural >= 4:
    recommendation = "STRONG_YES"
elif avg_technical >= 3 and avg_cultural >= 3:
    recommendation = "YES"
else:
    recommendation = "NO"

# 5. Add timeline comment
client.add_timeline_comment(
    candidacy_id=id,
    comment=f"Automated evaluation: {recommendation}\n"
            f"Technical: {avg_technical:.1f}/5\n"
            f"Cultural: {avg_cultural:.1f}/5"
)
```

**See**: `.claude/agents/herp-candidate-reviewer.md` for full agent implementation

## Performance Optimization

### Caching

**Location**: `src/core/cache/cache_manager.py`

```python
from src.core.cache.cache_manager import CacheManager

cache = CacheManager(max_size=1000, default_ttl=300)

# Cache expensive API calls
def get_candidacy_cached(id: str):
    cached = cache.get(f"candidacy:{id}")
    if cached:
        return cached

    candidacy = client.get_candidacy(id)
    cache.set(f"candidacy:{id}", candidacy, ttl=60)
    return candidacy
```

### Connection Pooling

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure session with connection pooling
session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=Retry(total=3, backoff_factor=1)
)
session.mount("https://", adapter)

client = HerpClient(api_token=token, session=session)
```

### Async for I/O-Bound Operations

```python
# 10-20x faster for multiple API calls
async def fetch_candidacies_and_contacts(ids):
    async with AsyncHerpClient(api_token=token) as client:
        # Fetch candidacies
        candidacy_tasks = [client.get_candidacy(id) for id in ids]
        candidacies = await asyncio.gather(*candidacy_tasks)

        # Fetch contacts for each
        contact_tasks = [
            client.list_candidacy_contacts(id)
            for id in ids
        ]
        contacts = await asyncio.gather(*contact_tasks)

        return list(zip(candidacies, contacts))

# Results in 2 concurrent API "rounds" instead of 2*N sequential calls
```

## Testing Patterns

### VCR-Based Integration Tests

**Location**: `tests/integration/herp/`

```python
import pytest
import vcr

my_vcr = vcr.VCR(
    cassette_library_dir='tests/integration/fixtures/cassettes',
    record_mode='once',
    match_on=['method', 'scheme', 'host', 'port', 'path', 'query']
)

@pytest.mark.vcr
def test_get_candidacy():
    """Test with recorded HTTP interactions"""
    client = HerpClient(api_token="test_token")

    with my_vcr.use_cassette('get_candidacy.yaml'):
        candidacy = client.get_candidacy("candidacy_123")

    assert candidacy["id"] == "candidacy_123"
    assert candidacy["name"]
    assert candidacy["status"] in ["active", "terminated"]
```

### Unit Tests with Mocks

**Location**: `tests/unit/core/herp/`

```python
from unittest.mock import Mock, patch

def test_batch_fetch_with_rate_limiting():
    """Test batch operations respect rate limits"""
    mock_client = Mock()
    mock_client.get_candidacy.return_value = {"id": "123", "name": "Test"}

    batch_client = BatchHerpClient(mock_client, max_workers=10)

    with patch('time.sleep') as mock_sleep:
        result = batch_client.fetch_candidacies_batch(["123"] * 150)

    # Verify rate limiting was applied (150 requests > 100/min limit)
    assert mock_sleep.called
```

## Debugging Tools

### Logging

```python
import structlog

logger = structlog.get_logger()

# Structured logging
logger.info(
    "candidacy_fetched",
    candidacy_id=id,
    status=candidacy["status"],
    step=candidacy.get("step")
)

# Log with context
with structlog.contextvars.bound_contextvars(
    operation="sync",
    batch_id=batch_id
):
    logger.info("batch_started", count=len(ids))
    # ... operations ...
    logger.info("batch_completed", success_count=successful)
```

### API Response Inspection

```python
# Log raw responses for debugging
import json

response = client._request("GET", "/v1/candidacies/123")
print(json.dumps(response.json(), indent=2))

# Check headers
print(f"Rate limit remaining: {response.headers.get('x-remaining-request')}")
print(f"Request ID: {response.headers.get('x-request-id')}")
```

### Circuit Breaker Monitoring

```python
from src.core.circuit_breaker import AsyncCircuitBreaker

breaker = AsyncCircuitBreaker(
    name="herp_api",
    failure_threshold=5,
    recovery_timeout=60
)

# Monitor state
print(f"Circuit state: {breaker.state}")  # CLOSED, OPEN, HALF_OPEN
print(f"Failure count: {breaker.failure_count}")
```

## Migration Patterns

### Data Migration

```python
# Migrate candidates from old system to HERP
def migrate_candidate(old_candidate: dict):
    # Transform to HERP format
    new_candidacy = {
        "name": old_candidate["full_name"],
        "email": old_candidate["email_address"],
        "requisitionId": map_job_id(old_candidate["position_id"]),
        "channel": {
            "type": "referral" if old_candidate["referrer"] else "direct",
            "source": old_candidate.get("source", "website")
        }
    }

    # Create in HERP
    try:
        created = client.create_candidacy(new_candidacy)
        logger.info("migrated", old_id=old_candidate["id"], new_id=created["id"])
        return created
    except HerpAPIError as e:
        logger.error("migration_failed", old_id=old_candidate["id"], error=str(e))
        return None
```

### Schema Version Migration

```python
# Handle API version changes
def upgrade_candidacy_v1_to_v2(v1_data: dict) -> dict:
    """Upgrade candidacy from v1 to v2 schema"""
    v2_data = v1_data.copy()

    # Rename fields
    if "stepId" in v2_data:
        v2_data["step"] = v2_data.pop("stepId")

    # Add new fields
    v2_data.setdefault("channel", None)
    v2_data.setdefault("tags", [])

    # Convert date formats
    if "createdAt" in v2_data:
        # Convert from timestamp to ISO 8601
        from datetime import datetime
        ts = v2_data["createdAt"]
        v2_data["createdAt"] = datetime.fromtimestamp(ts).isoformat()

    return v2_data
```

## Best Practices Summary

1. **Always use rate limiting** - HERP API has strict limits
2. **Implement retry logic** - Handle transient errors gracefully
3. **Cache when possible** - Reduce API calls for frequently accessed data
4. **Use batch operations** - 10x faster for bulk operations
5. **Validate schemas** - Ensure API responses match expectations
6. **Log structured data** - Enable debugging and monitoring
7. **Test with VCR** - Record real API interactions for tests
8. **Handle camelCase** - Remember API uses camelCase, code uses snake_case
9. **Use async for I/O** - Significant performance gains
10. **Monitor metrics** - Track success rates, latency, errors

## Related Documentation

- **Core Client**: `src/core/herp/client.py`
- **Async Client**: `src/core/herp/async_base_client.py`
- **Batch Operations**: `src/core/herp/batch_client.py`
- **Error Handling**: `src/core/errors/exceptions.py`
- **Rate Limiting**: `src/core/herp/async_rate_limiter.py`
- **Schemas**: `src/core/herp/schemas.py`
- **Models**: `src/core/herp/models.py`
- **Event Sourcing**: `src/core/herp/events/`
- **Project Context**: `.claude/CLAUDE.md`

## Skills Reference

- `/herp-test` - Run test suite
- `/herp-sync` - HERP-Notion synchronization
- `/herp-batch-operations` - Bulk operations
- `/herp-api-validator` - Schema validation

## Agents Reference

- `herp-candidate-reviewer` - Automated candidate evaluation
- `herp-notion-sync` - Bidirectional HERP-Notion sync
- `recruiting-analytics-exporter` - Export analytics data

## Quick Reference Commands

```bash
# Development
make install          # Install dependencies
make test            # Run tests
make format          # Format code
make pre-push        # Pre-push verification

# Testing
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v --vcr       # Integration tests
pytest --cov=src --cov-report=html       # Coverage report

# Skills
/herp-test unit                          # Fast unit tests
/herp-batch-operations fetch --limit=100 # Fetch candidates
/herp-api-validator validate             # Validate schemas
```

## Common Gotchas

1. **CamelCase field names** - API uses `createdAt`, not `created_at`
2. **NotRequired fields** - Use `NotRequired` for optional TypedDict fields
3. **Rate limits** - 100 requests/minute, monitor headers
4. **Transient errors** - Always retry with backoff
5. **Pagination** - Don't fetch all at once, use pagination
6. **VCR cassettes** - Re-record when API changes
7. **Async context** - Always use `async with` for AsyncHerpClient
8. **Batch sizes** - Keep under 100 for optimal performance
