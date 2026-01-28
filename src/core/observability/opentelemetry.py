"""
OpenTelemetry Instrumentation

Provides distributed tracing and metrics export using OpenTelemetry.
Gracefully degrades if OpenTelemetry is not installed.

Usage:
    >>> from src.core.observability.opentelemetry import setup_telemetry
    >>> from src.core.herp import HerpClient
    >>>
    >>> # Initialize OpenTelemetry (optional)
    >>> tracer, meter = setup_telemetry(
    ...     service_name="herp-client",
    ...     endpoint="http://localhost:4318"  # OTLP endpoint
    ... )
    >>>
    >>> # Client will automatically create spans and export metrics
    >>> client = HerpClient(config)
    >>> candidacy = client.candidacies.get("cand_123")  # Auto-traced!

Environment Variables:
    OTEL_SERVICE_NAME: Service name for tracing (default: "herp-python-client")
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4318)
    OTEL_TRACES_ENABLED: Enable tracing (default: "true")
    OTEL_METRICS_ENABLED: Enable metrics (default: "true")
"""

import functools
import os
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Tuple

from ..utils.logging import get_logger

logger = get_logger(__name__)

# OpenTelemetry availability
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore
    metrics = None  # type: ignore

# Global telemetry state
_tracer: Optional[Any] = None
_meter: Optional[Any] = None
_telemetry_enabled = False


def is_telemetry_available() -> bool:
    """
    Check if OpenTelemetry is available

    Returns:
        True if OpenTelemetry is installed and can be used
    """
    return OTEL_AVAILABLE


def is_telemetry_enabled() -> bool:
    """
    Check if telemetry is currently enabled

    Returns:
        True if telemetry has been initialized and is active
    """
    return _telemetry_enabled and OTEL_AVAILABLE


def setup_telemetry(
    service_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    enable_traces: bool = True,
    enable_metrics: bool = True,
) -> Tuple[Optional[Any], Optional[Any]]:
    """
    Setup OpenTelemetry tracing and metrics

    Args:
        service_name: Service name for telemetry (default: from env or "herp-python-client")
        endpoint: OTLP endpoint URL (default: from env or http://localhost:4318)
        enable_traces: Enable distributed tracing
        enable_metrics: Enable metrics export

    Returns:
        Tuple of (tracer, meter) or (None, None) if OpenTelemetry not available

    Example:
        >>> # Basic setup with defaults
        >>> tracer, meter = setup_telemetry()
        >>>
        >>> # Custom configuration
        >>> tracer, meter = setup_telemetry(
        ...     service_name="my-app",
        ...     endpoint="https://otel-collector.example.com:4318",
        ... )
        >>>
        >>> # Disable traces, only metrics
        >>> tracer, meter = setup_telemetry(enable_traces=False)
    """
    global _tracer, _meter, _telemetry_enabled

    if not OTEL_AVAILABLE:
        logger.warning(
            "OpenTelemetry not installed. "
            "Install with: pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-http"
        )
        return None, None

    # Get configuration from environment or arguments
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "herp-python-client")
    endpoint = endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
    )
    enable_traces = enable_traces and os.getenv(
        "OTEL_TRACES_ENABLED", "true"
    ).lower() in (
        "true",
        "1",
        "yes",
    )
    enable_metrics = enable_metrics and os.getenv(
        "OTEL_METRICS_ENABLED", "true"
    ).lower() in ("true", "1", "yes")

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",  # TODO: Get from package version
        }
    )

    # Setup tracing
    if enable_traces:
        try:
            tracer_provider = TracerProvider(resource=resource)
            span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
            span_processor = BatchSpanProcessor(span_exporter)
            tracer_provider.add_span_processor(span_processor)
            trace.set_tracer_provider(tracer_provider)
            _tracer = trace.get_tracer(__name__)
            logger.info(f"OpenTelemetry tracing enabled (endpoint: {endpoint})")
        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry tracing: {e}")
            _tracer = None

    # Setup metrics
    if enable_metrics:
        try:
            metric_exporter = OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics")
            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=60000,  # Export every 60s
            )
            meter_provider = MeterProvider(
                resource=resource, metric_readers=[metric_reader]
            )
            metrics.set_meter_provider(meter_provider)
            _meter = metrics.get_meter(__name__)
            logger.info(f"OpenTelemetry metrics enabled (endpoint: {endpoint})")
        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry metrics: {e}")
            _meter = None

    _telemetry_enabled = (_tracer is not None) or (_meter is not None)

    return _tracer, _meter


def get_tracer():
    """
    Get the global tracer instance

    Returns:
        Tracer instance or None if not initialized
    """
    return _tracer


def get_meter():
    """
    Get the global meter instance

    Returns:
        Meter instance or None if not initialized
    """
    return _meter


@contextmanager
def trace_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating a trace span

    Args:
        name: Span name
        attributes: Optional span attributes

    Yields:
        Span object or None if tracing not enabled

    Example:
        >>> with trace_span("fetch_candidacy", {"candidacy_id": "cand_123"}):
        ...     candidacy = client.candidacies.get("cand_123")
    """
    if not is_telemetry_enabled() or _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """
    Decorator to automatically trace a function

    Args:
        name: Span name (default: function name)
        attributes: Optional span attributes

    Returns:
        Decorated function

    Example:
        >>> @trace_function(name="get_candidacy")
        ... def get_candidacy(candidacy_id: str):
        ...     return client.candidacies.get(candidacy_id)
        >>>
        >>> @trace_function(attributes={"operation": "list"})
        ... def list_candidacies():
        ...     return client.candidacies.list()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not is_telemetry_enabled() or _tracer is None:
                return func(*args, **kwargs)

            span_name = name or func.__name__
            with _tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Execute function
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


async def async_trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
):
    """
    Decorator to automatically trace an async function

    Args:
        name: Span name (default: function name)
        attributes: Optional span attributes

    Returns:
        Decorated async function

    Example:
        >>> @async_trace_function(name="async_get_candidacy")
        ... async def get_candidacy(candidacy_id: str):
        ...     return await client.candidacies.get(candidacy_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_telemetry_enabled() or _tracer is None:
                return await func(*args, **kwargs)

            span_name = name or func.__name__
            with _tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Execute function
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        return wrapper

    return decorator


def record_metric(
    metric_name: str,
    value: float,
    attributes: Optional[Dict[str, str]] = None,
    metric_type: str = "counter",
) -> None:
    """
    Record a metric value

    Args:
        metric_name: Metric name
        value: Metric value
        attributes: Optional metric attributes/labels
        metric_type: Type of metric ("counter", "histogram", "gauge")

    Example:
        >>> record_metric("herp.api.requests", 1, {"endpoint": "/v1/candidacies"})
        >>> record_metric(
        ...     "herp.api.latency",
        ...     duration_ms,
        ...     {"endpoint": "/v1/candidacies"},
        ...     metric_type="histogram"
        ... )
    """
    if not is_telemetry_enabled() or _meter is None:
        return

    try:
        attrs = attributes or {}

        if metric_type == "counter":
            counter = _meter.create_counter(metric_name)
            counter.add(value, attributes=attrs)
        elif metric_type == "histogram":
            histogram = _meter.create_histogram(metric_name)
            histogram.record(value, attributes=attrs)
        elif metric_type == "gauge":
            # Note: OpenTelemetry doesn't have direct gauge support
            # Use up-down counter instead
            gauge = _meter.create_up_down_counter(metric_name)
            gauge.add(value, attributes=attrs)
    except Exception as e:
        logger.debug(f"Failed to record metric {metric_name}: {e}")
