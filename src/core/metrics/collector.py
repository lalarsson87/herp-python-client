"""
Metrics Collector - Alias for observability.metrics

This module provides backward compatibility for imports.
"""

from ..observability.metrics import (
    MetricData,
    MetricsCollector,
    get_metrics_collector,
    reset_global_metrics_collector,
)

__all__ = [
    "MetricData",
    "MetricsCollector",
    "get_metrics_collector",
    "reset_global_metrics_collector",
]
