"""
Observability components for HERP-Notion integration

Provides metrics collection, tracing, and monitoring capabilities.
"""

from .exporters import (
    JSONExporter,
    MetricsAggregator,
    PrometheusExporter,
    StatsDExporter,
)
from .http_instrumentation import (
    instrument_http_request,
    instrument_http_request_async,
)
from .metrics import MetricsCollector, get_metrics_collector
from .opentelemetry import (
    async_trace_function,
    get_meter,
    get_tracer,
    is_telemetry_available,
    is_telemetry_enabled,
    record_metric,
    setup_telemetry,
    trace_function,
    trace_span,
)

__all__ = [
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    # Exporters
    "PrometheusExporter",
    "StatsDExporter",
    "JSONExporter",
    "MetricsAggregator",
    # OpenTelemetry
    "setup_telemetry",
    "is_telemetry_available",
    "is_telemetry_enabled",
    "get_tracer",
    "get_meter",
    "trace_span",
    "trace_function",
    "async_trace_function",
    "record_metric",
    # HTTP Instrumentation
    "instrument_http_request",
    "instrument_http_request_async",
]
