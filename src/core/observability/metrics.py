"""
Metrics Collection

Provides metrics collection for API calls, cache operations, and performance tracking.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from threading import Lock
import time

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MetricData:
    """Individual metric data point"""

    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """
    Metrics collector for tracking API performance and usage

    Collects metrics like request counts, latencies, error rates, etc.
    Thread-safe for concurrent metric recording.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize metrics collector

        Args:
            enabled: Whether metrics collection is enabled
        """
        self.enabled = enabled
        self._metrics: list[MetricData] = []
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._lock = Lock()
        logger.info(f"MetricsCollector initialized (enabled={enabled})")

    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric

        Args:
            metric_name: Name of the metric
            value: Amount to increment (default: 1)
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return

        with self._lock:
            self._counters[metric_name] = self._counters.get(metric_name, 0) + value
            self._metrics.append(
                MetricData(name=metric_name, value=value, tags=tags or {})
            )

    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric

        Args:
            metric_name: Name of the metric
            value: Current value
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return

        with self._lock:
            self._gauges[metric_name] = value
            self._metrics.append(
                MetricData(name=metric_name, value=value, tags=tags or {})
            )

    def timing(self, metric_name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timing metric

        Args:
            metric_name: Name of the metric
            duration_ms: Duration in milliseconds
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return

        with self._lock:
            self._metrics.append(
                MetricData(name=metric_name, value=duration_ms, tags=tags or {})
            )

    def record(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a generic metric

        Args:
            metric_name: Name of the metric
            value: Metric value
            tags: Optional tags for the metric
        """
        if not self.enabled:
            return

        with self._lock:
            self._metrics.append(
                MetricData(name=metric_name, value=value, tags=tags or {})
            )

    def get_counter(self, metric_name: str) -> int:
        """
        Get current value of a counter metric

        Args:
            metric_name: Name of the metric

        Returns:
            Current counter value
        """
        with self._lock:
            return self._counters.get(metric_name, 0)

    def get_gauge(self, metric_name: str) -> Optional[float]:
        """
        Get current value of a gauge metric

        Args:
            metric_name: Name of the metric

        Returns:
            Current gauge value or None if not set
        """
        with self._lock:
            return self._gauges.get(metric_name)

    def get_all_metrics(self) -> list[MetricData]:
        """
        Get all recorded metrics

        Returns:
            List of all metric data points
        """
        with self._lock:
            return self._metrics.copy()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get metrics statistics

        Returns:
            Dictionary with metrics stats
        """
        with self._lock:
            return {
                "total_metrics": len(self._metrics),
                "counters": self._counters.copy(),
                "gauges": self._gauges.copy(),
                "enabled": self.enabled,
            }

    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._gauges.clear()
            logger.debug("Metrics reset")


# Global metrics collector instance
_global_metrics_collector: Optional[MetricsCollector] = None
_global_lock = Lock()


def get_metrics_collector(enabled: bool = True) -> MetricsCollector:
    """
    Get or create the global metrics collector instance

    Args:
        enabled: Whether metrics collection is enabled (only used on first call)

    Returns:
        Global MetricsCollector instance
    """
    global _global_metrics_collector

    if _global_metrics_collector is None:
        with _global_lock:
            # Double-check locking pattern
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector(enabled=enabled)
                logger.info("Global MetricsCollector created")

    return _global_metrics_collector


def reset_global_metrics_collector() -> None:
    """
    Reset the global metrics collector

    Useful for testing and cleanup.
    """
    global _global_metrics_collector

    with _global_lock:
        if _global_metrics_collector is not None:
            _global_metrics_collector.reset()
            _global_metrics_collector = None
            logger.info("Global MetricsCollector reset")
