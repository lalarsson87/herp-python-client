"""
Metrics module - Alias for observability.metrics

This module provides backward compatibility for imports.
"""

from ..observability.metrics import MetricsCollector, get_metrics_collector

__all__ = ["MetricsCollector", "get_metrics_collector"]
