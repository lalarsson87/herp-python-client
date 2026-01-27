# Structured Logging Guide

The HERP Python Client uses **structlog** for structured, machine-parseable logging.

## Why Structured Logging?

**Traditional Logging:**
```python
logger.info(f"Created candidacy {candidacy_id} for requisition {req_id} in {duration}ms")
```
Output: `2026-01-27 10:30:45 - INFO - Created candidacy cand_123 for requisition req_456 in 125.4ms`

Problems:
- Hard to parse programmatically
- Difficult to filter/search
- No standard format
- Can't aggregate metrics

**Structured Logging:**
```python
logger.info(
    "candidacy.created",
    candidacy_id="cand_123",
    requisition_id="req_456",
    duration_ms=125.4
)
```

Output (JSON):
```json
{
  "event": "candidacy.created",
  "candidacy_id": "cand_123",
  "requisition_id": "req_456",
  "duration_ms": 125.4,
  "timestamp": "2026-01-27T10:30:45.123456Z",
  "level": "info",
  "logger": "src.core.herp.client"
}
```

Benefits:
- ✅ Machine-parseable
- ✅ Easy to filter: `jq '.candidacy_id == "cand_123"'`
- ✅ Aggregate metrics: `jq '.duration_ms' | avg`
- ✅ Integration with log aggregation (Datadog, ELK, Splunk)

## Basic Usage

### Simple Logging

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

# Simple event
logger.info("server.started")

# Event with context
logger.info(
    "candidacy.created",
    candidacy_id="cand_123",
    name="Jane Doe",
    email="jane@example.com"
)

# Different log levels
logger.debug("request.details", method="GET", path="/v1/candidacies")
logger.warning("rate_limit.approaching", remaining=10, limit=100)
logger.error("api.error", status_code=500, error="Internal Server Error")
```

### Binding Context

Bind context that will be included in all subsequent log messages:

```python
from src.core.utils.logging import get_logger

# Create logger with initial context
logger = get_logger(__name__, service="herp-client", version="0.3.0")

# Bind request-specific context
request_logger = logger.bind(
    request_id="req_abc123",
    user_id="user_001",
    tenant_id="belong"
)

# All logs now include request_id, user_id, tenant_id
request_logger.info("request.started", method="POST", path="/v1/candidacies")
request_logger.info("database.query", query="SELECT * FROM candidacies", duration_ms=45.2)
request_logger.info("request.completed", status_code=201, duration_ms=125.4)
```

Output:
```json
{
  "event": "request.completed",
  "status_code": 201,
  "duration_ms": 125.4,
  "request_id": "req_abc123",
  "user_id": "user_001",
  "tenant_id": "belong",
  "service": "herp-client",
  "version": "0.3.0"
}
```

### Request Logging

Use `get_request_logger` for API request logging:

```python
from src.core.utils.logging import get_request_logger

logger = get_request_logger(
    __name__,
    request_id="req_abc123",
    user_id="user_001"
)

logger.info(
    "api.request",
    method="POST",
    endpoint="/v1/candidacies",
    headers={"Content-Type": "application/json"}
)

logger.info(
    "api.response",
    status_code=201,
    duration_ms=125.4,
    response_size_bytes=1024
)
```

## Configuration

### Environment Variables

Control logging behavior via environment variables:

```bash
# Log format: "json" (production) or "console" (development)
export LOG_FORMAT=json

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_LEVEL=INFO

# Enable colored console output (console format only)
export LOG_COLORS=true
```

### Programmatic Configuration

```python
from src.core.utils.logging import configure_structlog

# Development (colored console output)
configure_structlog(
    log_level="DEBUG",
    format="console",
    enable_colors=True
)

# Production (JSON output)
configure_structlog(
    log_level="INFO",
    format="json",
    enable_colors=False
)
```

## Common Patterns

### API Client Logging

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

def create_candidacy(self, data: Dict) -> Dict:
    logger.info(
        "candidacy.create.started",
        name=data.get("name"),
        requisition_id=data.get("requisition_id")
    )
    
    try:
        response = self.post("/v1/candidacies", json=data)
        
        logger.info(
            "candidacy.create.success",
            candidacy_id=response["id"],
            duration_ms=response.get("_duration_ms")
        )
        
        return response
        
    except HerpAPIError as e:
        logger.error(
            "candidacy.create.failed",
            error=str(e),
            status_code=e.status_code,
            error_type=type(e).__name__
        )
        raise
```

### Performance Tracking

```python
import time
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

def expensive_operation():
    start_time = time.time()
    
    logger.debug("operation.started", operation="expensive_operation")
    
    try:
        # Do work
        result = perform_work()
        
        duration_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "operation.completed",
            operation="expensive_operation",
            duration_ms=duration_ms,
            result_count=len(result)
        )
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "operation.failed",
            operation="expensive_operation",
            duration_ms=duration_ms,
            error=str(e)
        )
        raise
```

### Circuit Breaker Logging

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

class CircuitBreaker:
    def _transition_to_open(self):
        self.state = CircuitState.OPEN
        
        logger.warning(
            "circuit_breaker.opened",
            name=self.config.name,
            failure_count=self.failure_count,
            threshold=self.config.failure_threshold
        )
    
    def _transition_to_closed(self):
        self.state = CircuitState.CLOSED
        
        logger.info(
            "circuit_breaker.closed",
            name=self.config.name,
            success_count=self.success_count
        )
```

### Cache Operations

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)

class CacheManager:
    def get(self, key: str):
        value = self._cache.get(key)
        
        if value is None:
            logger.debug("cache.miss", key=key)
        else:
            logger.debug("cache.hit", key=key, ttl_remaining=value.expires_at - time.time())
        
        return value
    
    def set(self, key: str, value: Any, ttl: int):
        self._cache[key] = CacheEntry(value=value, expires_at=time.time() + ttl)
        
        logger.debug(
            "cache.set",
            key=key,
            ttl=ttl,
            cache_size=len(self._cache)
        )
```

## Log Analysis

### Filter Logs with jq

```bash
# Filter by event
cat app.log | jq 'select(.event == "candidacy.created")'

# Filter by candidacy_id
cat app.log | jq 'select(.candidacy_id == "cand_123")'

# Calculate average duration
cat app.log | jq -s '[.[] | select(.duration_ms) | .duration_ms] | add / length'

# Count errors by type
cat app.log | jq -s 'group_by(.error_type) | map({error_type: .[0].error_type, count: length})'

# Filter by time range
cat app.log | jq 'select(.timestamp > "2026-01-27T10:00:00Z")'
```

### Integration with Log Aggregation

#### Datadog

```python
from src.core.utils.logging import configure_structlog

configure_structlog(format="json")

# Logs will be automatically parsed by Datadog agent
# Filter in Datadog: @candidacy_id:cand_123
# Create metrics: avg:duration_ms
```

#### ELK Stack (Elasticsearch, Logstash, Kibana)

```json
{
  "input": {
    "file": {
      "path": "/var/log/herp-client/*.log"
    }
  },
  "filter": {
    "json": {
      "source": "message"
    }
  },
  "output": {
    "elasticsearch": {
      "hosts": ["localhost:9200"],
      "index": "herp-client-%{+YYYY.MM.dd}"
    }
  }
}
```

#### Splunk

```ini
[source::herp-client]
sourcetype = _json
INDEXED_EXTRACTIONS = json
KV_MODE = json
```

## Best Practices

### 1. Use Consistent Event Names

✅ Good:
```python
logger.info("candidacy.created")
logger.info("candidacy.updated")
logger.info("candidacy.deleted")
```

❌ Bad:
```python
logger.info("Created candidacy")
logger.info("Candidacy was updated")
logger.info("Delete candidacy")
```

### 2. Include Relevant Context

✅ Good:
```python
logger.info(
    "api.request",
    method="POST",
    endpoint="/v1/candidacies",
    duration_ms=125.4,
    status_code=201
)
```

❌ Bad:
```python
logger.info("API request completed")
```

### 3. Use Appropriate Log Levels

- **DEBUG**: Detailed diagnostic information (verbose)
- **INFO**: Informational messages (normal operations)
- **WARNING**: Warning messages (unexpected but handled)
- **ERROR**: Error messages (failures)
- **CRITICAL**: Critical errors (system failure)

### 4. Don't Log Sensitive Data

❌ Never log:
```python
logger.info("user.login", password=password)  # NEVER!
logger.info("api.request", api_key=api_key)  # NEVER!
```

✅ Redact or omit:
```python
logger.info("user.login", email=email)
logger.info("api.request", endpoint=endpoint)
```

### 5. Use Numeric Types for Metrics

✅ Good:
```python
logger.info("request.completed", duration_ms=125.4, status_code=201)
```

❌ Bad:
```python
logger.info("request.completed", duration_ms="125.4ms", status_code="201")
```

## Migration from Standard Logging

Existing code using standard `logging` module will continue to work:

```python
from src.core.utils.logging import get_legacy_logger

logger = get_legacy_logger(__name__)
logger.info("This still works")  # String-based logging
```

Gradually migrate to structured logging:

```python
from src.core.utils.logging import get_logger

logger = get_logger(__name__)
logger.info("event.name", key="value")  # Structured logging
```

## Testing

Test logs are automatically captured by pytest:

```python
def test_logging(caplog):
    from src.core.utils.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("test.event", value=42)
    
    assert "test.event" in caplog.text
```

---

For more information:
- [structlog documentation](https://www.structlog.org/)
- [Best practices for structured logging](https://www.structlog.org/en/stable/standard-library.html)
