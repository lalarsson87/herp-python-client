"""
Metrics Exporters

Provides exporters for metrics to various monitoring systems.
Supports Prometheus, StatsD, and custom formats.
"""

import time
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from .metrics import MetricsCollector, get_metrics_collector

logger = get_logger(__name__)


class PrometheusExporter:
    """
    Export metrics in Prometheus format

    Generates Prometheus-compatible text format for scraping.

    Usage:
        >>> exporter = PrometheusExporter(metrics_collector)
        >>> metrics_text = exporter.export()
        >>> # Serve via HTTP endpoint
    """

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize Prometheus exporter

        Args:
            metrics_collector: Metrics collector (uses global if None)
        """
        self.metrics = metrics_collector or get_metrics_collector()

    def export(self) -> str:
        """
        Export metrics in Prometheus text format

        Returns:
            Prometheus-formatted metrics string
        """
        stats = self.metrics.get_stats()
        lines = []

        # Add header
        lines.append("# HELP herp_metrics HERP Python Client Metrics")
        lines.append("# TYPE herp_metrics gauge")

        # Export counters
        for name, value in stats.get("counters", {}).items():
            safe_name = name.replace(".", "_").replace("-", "_")
            lines.append(f'herp_{safe_name}{{type="counter"}} {value}')

        # Export gauges
        for name, value in stats.get("gauges", {}).items():
            safe_name = name.replace(".", "_").replace("-", "_")
            lines.append(f'herp_{safe_name}{{type="gauge"}} {value}')

        # Add timestamp
        lines.append(f"# Exported at {int(time.time())}")

        return "\n".join(lines) + "\n"

    def export_to_file(self, file_path: str) -> None:
        """
        Export metrics to file

        Args:
            file_path: Path to output file
        """
        metrics_text = self.export()
        with open(file_path, "w") as f:
            f.write(metrics_text)

        logger.info(f"Exported Prometheus metrics to {file_path}")


class StatsDExporter:
    """
    Export metrics to StatsD

    Sends metrics to StatsD daemon for aggregation.

    Usage:
        >>> exporter = StatsDExporter(host="localhost", port=8125)
        >>> exporter.export()  # Send all metrics
        >>> exporter.export_counter("requests", 1, tags={"endpoint": "/api"})
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8125,
        prefix: str = "herp",
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize StatsD exporter

        Args:
            host: StatsD host
            port: StatsD port
            prefix: Metric name prefix
            metrics_collector: Metrics collector (uses global if None)
        """
        self.host = host
        self.port = port
        self.prefix = prefix
        self.metrics = metrics_collector or get_metrics_collector()

        # Try to import statsd client
        try:
            import statsd

            self.client = statsd.StatsClient(host, port, prefix=prefix)
            self.available = True
            logger.info(f"StatsD client initialized ({host}:{port})")
        except ImportError:
            self.client = None
            self.available = False
            logger.warning(
                "statsd library not available. " "Install with: pip install statsd"
            )

    def export(self) -> Dict[str, int]:
        """
        Export all metrics to StatsD

        Returns:
            Dictionary with export statistics
        """
        if not self.available:
            logger.warning("StatsD not available, skipping export")
            return {"exported": 0, "failed": 0}

        stats = self.metrics.get_stats()
        exported = 0
        failed = 0

        # Export counters
        for name, value in stats.get("counters", {}).items():
            try:
                self.client.gauge(name, value)
                exported += 1
            except Exception as e:
                logger.error(f"Failed to export counter {name}: {e}")
                failed += 1

        # Export gauges
        for name, value in stats.get("gauges", {}).items():
            try:
                self.client.gauge(name, value)
                exported += 1
            except Exception as e:
                logger.error(f"Failed to export gauge {name}: {e}")
                failed += 1

        logger.info(f"Exported {exported} metrics to StatsD ({failed} failed)")
        return {"exported": exported, "failed": failed}

    def export_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Export single counter metric

        Args:
            name: Metric name
            value: Counter value
            tags: Optional metric tags
        """
        if not self.available:
            return

        # StatsD doesn't natively support tags in standard protocol
        # For Datadog StatsD, we can add tags
        metric_name = name
        if tags:
            tag_str = ",".join(f"{k}:{v}" for k, v in tags.items())
            metric_name = f"{name}#{tag_str}"

        try:
            self.client.incr(metric_name, value)
        except Exception as e:
            logger.error(f"Failed to export counter {name}: {e}")

    def export_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Export single gauge metric

        Args:
            name: Metric name
            value: Gauge value
            tags: Optional metric tags
        """
        if not self.available:
            return

        metric_name = name
        if tags:
            tag_str = ",".join(f"{k}:{v}" for k, v in tags.items())
            metric_name = f"{name}#{tag_str}"

        try:
            self.client.gauge(metric_name, value)
        except Exception as e:
            logger.error(f"Failed to export gauge {name}: {e}")

    def export_timing(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Export timing metric

        Args:
            name: Metric name
            value: Duration in milliseconds
            tags: Optional metric tags
        """
        if not self.available:
            return

        metric_name = name
        if tags:
            tag_str = ",".join(f"{k}:{v}" for k, v in tags.items())
            metric_name = f"{name}#{tag_str}"

        try:
            self.client.timing(metric_name, value)
        except Exception as e:
            logger.error(f"Failed to export timing {name}: {e}")


class JSONExporter:
    """
    Export metrics in JSON format

    Exports metrics as structured JSON for custom integrations.

    Usage:
        >>> exporter = JSONExporter(metrics_collector)
        >>> metrics_json = exporter.export()
        >>> exporter.export_to_file("metrics.json")
    """

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize JSON exporter

        Args:
            metrics_collector: Metrics collector (uses global if None)
        """
        self.metrics = metrics_collector or get_metrics_collector()

    def export(self) -> Dict[str, Any]:
        """
        Export metrics as JSON

        Returns:
            Dictionary with metrics data
        """
        import json

        stats = self.metrics.get_stats()

        return {
            "timestamp": int(time.time()),
            "metrics": {
                "counters": stats.get("counters", {}),
                "gauges": stats.get("gauges", {}),
                "total_metrics": stats.get("total_metrics", 0),
            },
            "metadata": {
                "enabled": stats.get("enabled", True),
                "exporter": "JSONExporter",
                "version": "1.0.0",
            },
        }

    def export_to_file(self, file_path: str, indent: int = 2) -> None:
        """
        Export metrics to JSON file

        Args:
            file_path: Path to output file
            indent: JSON indentation
        """
        import json

        metrics_data = self.export()

        with open(file_path, "w") as f:
            json.dump(metrics_data, f, indent=indent)

        logger.info(f"Exported JSON metrics to {file_path}")

    def export_to_string(self, indent: Optional[int] = None) -> str:
        """
        Export metrics as JSON string

        Args:
            indent: JSON indentation (None for compact)

        Returns:
            JSON string
        """
        import json

        metrics_data = self.export()
        return json.dumps(metrics_data, indent=indent)


class MetricsAggregator:
    """
    Aggregate and summarize metrics

    Provides statistical aggregations over metric data.

    Usage:
        >>> aggregator = MetricsAggregator(metrics_collector)
        >>> summary = aggregator.get_summary()
        >>> percentiles = aggregator.get_percentiles("request_duration")
    """

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize metrics aggregator

        Args:
            metrics_collector: Metrics collector (uses global if None)
        """
        self.metrics = metrics_collector or get_metrics_collector()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metrics summary

        Returns:
            Summary statistics
        """
        stats = self.metrics.get_stats()
        all_metrics = self.metrics.get_all_metrics()

        counter_total = sum(stats.get("counters", {}).values())
        gauge_count = len(stats.get("gauges", {}))

        return {
            "total_metrics": len(all_metrics),
            "total_counter_value": counter_total,
            "active_counters": len(stats.get("counters", {})),
            "active_gauges": gauge_count,
            "enabled": stats.get("enabled", True),
        }

    def get_metrics_by_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """
        Get metrics matching prefix

        Args:
            prefix: Metric name prefix

        Returns:
            List of matching metrics
        """
        all_metrics = self.metrics.get_all_metrics()
        return [m for m in all_metrics if m.name.startswith(prefix)]

    def get_rate(self, metric_name: str, window_seconds: int = 60) -> float:
        """
        Calculate metric rate

        Args:
            metric_name: Metric name
            window_seconds: Time window in seconds

        Returns:
            Metric rate (events per second)
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        all_metrics = self.metrics.get_all_metrics()
        matching = [
            m
            for m in all_metrics
            if m.name == metric_name and m.timestamp >= window_start
        ]

        if not matching:
            return 0.0

        total_value = sum(m.value for m in matching)
        return total_value / window_seconds
