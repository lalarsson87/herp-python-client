# OpenTelemetry Integration Guide

## Overview

The HERP Python Client includes optional OpenTelemetry support for distributed tracing and metrics export. This enables:

- **Distributed Tracing**: Track requests across services
- **Performance Monitoring**: Identify bottlenecks and slow operations
- **Error Tracking**: Capture and analyze errors with context
- **Metrics Export**: Send metrics to observability platforms

## Installation

OpenTelemetry is an optional dependency. Install it separately:

```bash
# Install with OpenTelemetry support
pip install herp-python-client[telemetry]

# Or install OpenTelemetry packages manually
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

## Quick Start

### Basic Setup

```python
from src.core.observability import setup_telemetry
from src.core.herp import HerpClient
from src.core.utils.config import load_herp_config

# Initialize OpenTelemetry
tracer, meter = setup_telemetry(
    service_name="my-herp-app",
    endpoint="http://localhost:4318"  # OTLP collector endpoint
)

# Use client as normal - requests are automatically traced
config = load_herp_config()
client = HerpClient(config)

# This request will be automatically traced!
candidacy = client.candidacies.get("cand_123")
```

### Environment Variables

Configure OpenTelemetry via environment variables:

```bash
# Service identification
export OTEL_SERVICE_NAME="my-herp-app"

# OTLP endpoint (HTTP)
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"

# Enable/disable features
export OTEL_TRACES_ENABLED="true"
export OTEL_METRICS_ENABLED="true"
```

## Distributed Tracing

### Automatic HTTP Tracing

All HTTP requests made through the HERP client are automatically traced when OpenTelemetry is enabled:

```python
from src.core.observability import setup_telemetry
from src.core.herp import HerpClient

# Setup telemetry
setup_telemetry()

# All these operations will create spans
client = HerpClient(config)
candidacy = client.candidacies.get("cand_123")          # Span: "HTTP GET"
contacts = client.contacts.list("cand_123")             # Span: "HTTP GET"
comment = client.timeline.add_comment("cand_123", "...") # Span: "HTTP POST"
```

Each span includes:
- HTTP method and URL
- Response status code
- Request duration
- Error information (if applicable)

### Custom Spans

Add custom spans for business logic:

```python
from src.core.observability import trace_span

def process_candidacy(candidacy_id: str):
    with trace_span("process_candidacy", {"candidacy_id": candidacy_id}) as span:
        # Fetch candidacy
        candidacy = client.candidacies.get(candidacy_id)

        # Process data
        result = analyze_candidate(candidacy)

        # Add attributes to span
        if span:
            span.set_attribute("candidate_name", candidacy["name"])
            span.set_attribute("analysis_score", result["score"])

        return result
```

### Function Decorators

Automatically trace functions with decorators:

```python
from src.core.observability import trace_function

@trace_function(name="sync_to_notion", attributes={"operation": "sync"})
def sync_candidacy_to_notion(candidacy_id: str):
    candidacy = client.candidacies.get(candidacy_id)
    notion_page = create_notion_page(candidacy)
    return notion_page["id"]

# Async functions
from src.core.observability import async_trace_function

@async_trace_function(name="async_sync_to_notion")
async def async_sync_candidacy(candidacy_id: str):
    candidacy = await async_client.candidacies.get(candidacy_id)
    return candidacy
```

## Metrics Export

### Automatic HTTP Metrics

When OpenTelemetry is enabled, the client automatically exports metrics:

- `herp.http.requests` - Total HTTP requests (counter)
- `herp.http.responses` - HTTP responses by status code (counter)
- `herp.http.errors` - HTTP errors by type (counter)
- `herp.api.request.duration` - Request latency (histogram)

All metrics include labels:
- `method` - HTTP method (GET, POST, etc.)
- `endpoint` - API endpoint (/v1/candidacies, etc.)
- `status` - HTTP status code (200, 404, etc.)
- `error_type` - Exception type (for errors)

### Custom Metrics

Record custom metrics:

```python
from src.core.observability import record_metric

# Counter
record_metric(
    "candidacies.processed",
    1,
    attributes={"status": "success", "source": "api"}
)

# Histogram (for distributions)
record_metric(
    "candidacy.processing_time",
    duration_ms,
    attributes={"operation": "sync"},
    metric_type="histogram"
)

# Gauge (for current values)
record_metric(
    "candidacies.queue_size",
    queue_length,
    metric_type="gauge"
)
```

## Integration with Observability Platforms

### Jaeger (Local Development)

```bash
# Run Jaeger all-in-one
docker run -d --name jaeger \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Configure client
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME="herp-client-dev"

# View traces at http://localhost:16686
```

### Grafana Cloud

```bash
# Set endpoint to Grafana Cloud
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-prod-<region>.grafana.net/otlp"

# Add authentication headers (requires custom configuration)
```

### Datadog

```bash
# Run Datadog agent with OTLP receiver
docker run -d --name datadog-agent \
  -e DD_API_KEY=<your-api-key> \
  -e DD_OTLP_CONFIG_RECEIVER_PROTOCOLS_HTTP_ENDPOINT="0.0.0.0:4318" \
  -p 4318:4318 \
  datadog/agent:latest

export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
```

### Honeycomb

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.honeycomb.io:443"
export OTEL_EXPORTER_OTLP_HEADERS="x-honeycomb-team=<your-api-key>"
```

## Advanced Usage

### Conditional Telemetry

Enable telemetry only in production:

```python
import os
from src.core.observability import setup_telemetry, is_telemetry_enabled

# Only enable in production
if os.getenv("ENVIRONMENT") == "production":
    setup_telemetry(
        service_name="herp-client-prod",
        endpoint=os.getenv("OTEL_ENDPOINT")
    )

# Code works with or without telemetry
client = HerpClient(config)
candidacy = client.candidacies.get("cand_123")

# Check if telemetry is active
if is_telemetry_enabled():
    print("Telemetry is active")
```

### Span Context Propagation

Propagate trace context across services:

```python
from opentelemetry import trace

def handle_webhook(request):
    # Extract trace context from incoming request
    # (implementation depends on your web framework)

    with trace_span("process_webhook") as span:
        # This span will be part of the distributed trace
        candidacy = client.candidacies.get(request.json["candidacy_id"])
        process_candidacy(candidacy)
```

### Custom Resource Attributes

Add service metadata:

```python
from opentelemetry.sdk.resources import Resource
from src.core.observability import setup_telemetry

# This would require modifying setup_telemetry() to accept resource
resource = Resource.create({
    "service.name": "herp-sync-service",
    "service.version": "1.2.3",
    "deployment.environment": "production",
    "service.namespace": "recruiting",
})
```

## Performance Considerations

### Sampling

For high-traffic applications, consider sampling:

```python
# In production, sample 10% of traces
# (requires custom TracerProvider configuration)
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

sampler = TraceIdRatioBased(0.1)  # 10% sampling rate
```

### Batch Export

Traces and metrics are batched by default:
- **Traces**: Batched with `BatchSpanProcessor`
- **Metrics**: Exported every 60 seconds

### Overhead

OpenTelemetry adds minimal overhead:
- ~0.1-0.5ms per traced operation
- ~10-50 KB memory per trace
- Async export (non-blocking)

## Troubleshooting

### Telemetry Not Working

Check if OpenTelemetry is installed:

```python
from src.core.observability import is_telemetry_available

if not is_telemetry_available():
    print("OpenTelemetry not installed")
    print("Install with: pip install herp-python-client[telemetry]")
```

### No Traces Appearing

1. **Check endpoint**: Verify OTLP endpoint is correct
   ```bash
   curl http://localhost:4318/v1/traces
   ```

2. **Check logs**: Enable debug logging
   ```bash
   export LOG_LEVEL=DEBUG
   ```

3. **Verify setup**: Ensure `setup_telemetry()` is called
   ```python
   from src.core.observability import is_telemetry_enabled
   print(f"Telemetry enabled: {is_telemetry_enabled()}")
   ```

### High Memory Usage

If memory usage is high:

1. **Increase export frequency**: Reduce metric export interval
2. **Enable sampling**: Sample traces in high-traffic scenarios
3. **Limit span attributes**: Avoid adding large payloads to spans

## Best Practices

1. **Use Semantic Naming**: Name spans clearly (e.g., "fetch_candidacy" not "func1")

2. **Add Context**: Include relevant attributes in spans
   ```python
   span.set_attribute("candidacy_id", candidacy_id)
   span.set_attribute("operation", "sync")
   ```

3. **Don't Over-Instrument**: Trace significant operations, not every function call

4. **Handle Errors**: Record exceptions in spans
   ```python
   try:
       result = risky_operation()
   except Exception as e:
       if span:
           span.record_exception(e)
       raise
   ```

5. **Use Labels Consistently**: Use consistent metric labels across services

## Examples

### Complete Trace Example

```python
from src.core.observability import setup_telemetry, trace_span
from src.core.herp import HerpClient

# Setup
setup_telemetry(service_name="herp-analytics")
client = HerpClient(config)

def generate_report(start_date: str, end_date: str):
    with trace_span("generate_report", {
        "start_date": start_date,
        "end_date": end_date
    }) as span:

        # Fetch candidacies (auto-traced)
        candidacies = client.candidacies.fetch_all()

        # Filter
        filtered = [c for c in candidacies
                    if start_date <= c["appliedAt"] <= end_date]

        # Add metrics
        span.set_attribute("candidacies_count", len(filtered))

        # Generate report
        report = create_report(filtered)

        return report
```

### Metrics Dashboard Example

Monitor key metrics:

```python
from src.core.observability import setup_telemetry, record_metric

setup_telemetry()

def sync_candidacies():
    total = 0
    errors = 0

    for candidacy_id in candidacy_ids:
        try:
            sync_candidacy(candidacy_id)
            total += 1
            record_metric("sync.success", 1)
        except Exception:
            errors += 1
            record_metric("sync.failure", 1)

    # Record summary metrics
    record_metric("sync.total", total)
    record_metric("sync.error_rate", errors / total if total > 0 else 0)
```

## References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [OTLP Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
