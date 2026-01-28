"""
HTTP Instrumentation for OpenTelemetry

Provides automatic tracing for HTTP requests in HERP API clients.
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from ..utils.logging import get_logger
from .opentelemetry import get_tracer, is_telemetry_enabled, record_metric

if TYPE_CHECKING:
    import requests

logger = get_logger(__name__)


def instrument_http_request(
    method: str,
    url: str,
    func: Callable,
    *args,
    **kwargs,
) -> Any:
    """
    Instrument a synchronous HTTP request with tracing

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        func: Function to execute (the actual HTTP call)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Function result

    Example:
        >>> def make_request():
        ...     return requests.get("https://api.example.com/data")
        >>>
        >>> response = instrument_http_request("GET", "/data", make_request)
    """
    if not is_telemetry_enabled():
        return func(*args, **kwargs)

    tracer = get_tracer()
    if tracer is None:
        return func(*args, **kwargs)

    # Create span for HTTP request
    span_name = f"HTTP {method}"
    with tracer.start_as_current_span(span_name) as span:
        # Add HTTP attributes
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)

        # Record metric
        record_metric(
            "herp.http.requests",
            1,
            attributes={"method": method, "endpoint": _extract_endpoint(url)},
            metric_type="counter",
        )

        try:
            # Execute request
            result = func(*args, **kwargs)

            # Extract response info if available
            if hasattr(result, "status_code"):
                span.set_attribute("http.status_code", result.status_code)
                record_metric(
                    "herp.http.responses",
                    1,
                    attributes={
                        "method": method,
                        "endpoint": _extract_endpoint(url),
                        "status": str(result.status_code),
                    },
                    metric_type="counter",
                )

            return result

        except Exception as e:
            # Record error
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.record_exception(e)

            record_metric(
                "herp.http.errors",
                1,
                attributes={
                    "method": method,
                    "endpoint": _extract_endpoint(url),
                    "error_type": type(e).__name__,
                },
                metric_type="counter",
            )

            raise


async def instrument_http_request_async(
    method: str,
    url: str,
    func: Callable,
    *args,
    **kwargs,
) -> Any:
    """
    Instrument an asynchronous HTTP request with tracing

    Args:
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        func: Async function to execute (the actual HTTP call)
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Function result

    Example:
        >>> async def make_request():
        ...     return await client.get("https://api.example.com/data")
        >>>
        >>> response = await instrument_http_request_async("GET", "/data", make_request)
    """
    if not is_telemetry_enabled():
        return await func(*args, **kwargs)

    tracer = get_tracer()
    if tracer is None:
        return await func(*args, **kwargs)

    # Create span for HTTP request
    span_name = f"HTTP {method}"
    with tracer.start_as_current_span(span_name) as span:
        # Add HTTP attributes
        span.set_attribute("http.method", method)
        span.set_attribute("http.url", url)

        # Record metric
        record_metric(
            "herp.http.requests",
            1,
            attributes={"method": method, "endpoint": _extract_endpoint(url)},
            metric_type="counter",
        )

        try:
            # Execute request
            result = await func(*args, **kwargs)

            # Extract response info if available
            if hasattr(result, "status_code"):
                span.set_attribute("http.status_code", result.status_code)
                record_metric(
                    "herp.http.responses",
                    1,
                    attributes={
                        "method": method,
                        "endpoint": _extract_endpoint(url),
                        "status": str(result.status_code),
                    },
                    metric_type="counter",
                )

            return result

        except Exception as e:
            # Record error
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.record_exception(e)

            record_metric(
                "herp.http.errors",
                1,
                attributes={
                    "method": method,
                    "endpoint": _extract_endpoint(url),
                    "error_type": type(e).__name__,
                },
                metric_type="counter",
            )

            raise


def _extract_endpoint(url: str) -> str:
    """
    Extract endpoint path from URL for labeling

    Args:
        url: Full or partial URL

    Returns:
        Endpoint path (e.g., "/v1/candidacies")
    """
    # Simple extraction - just get the path part
    if "://" in url:
        # Full URL
        parts = url.split("/", 3)
        return "/" + parts[3] if len(parts) > 3 else "/"
    else:
        # Relative path
        return url.split("?")[0]  # Remove query params
