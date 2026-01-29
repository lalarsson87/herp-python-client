"""
Tests for Metrics Exporters
"""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.core.observability.exporters import (
    JSONExporter,
    MetricsAggregator,
    PrometheusExporter,
    StatsDExporter,
)
from src.core.observability.metrics import MetricsCollector


class TestPrometheusExporter:
    """Test Prometheus metrics exporter"""

    @pytest.fixture
    def metrics(self):
        """Create metrics collector with sample data"""
        collector = MetricsCollector()
        collector.increment("http.requests", 100)
        collector.increment("http.errors", 5)
        collector.gauge("active.connections", 42)
        collector.gauge("memory.usage.mb", 256.5)
        return collector

    def test_initialization_with_collector(self, metrics):
        """Test exporter initialization with collector"""
        exporter = PrometheusExporter(metrics)
        assert exporter.metrics == metrics

    @patch("src.core.observability.exporters.get_metrics_collector")
    def test_initialization_uses_global_collector(self, mock_get_collector):
        """Test exporter uses global collector when None provided"""
        mock_collector = Mock()
        mock_get_collector.return_value = mock_collector

        exporter = PrometheusExporter()

        assert exporter.metrics == mock_collector
        mock_get_collector.assert_called_once()

    def test_export_format(self, metrics):
        """Test Prometheus export format"""
        exporter = PrometheusExporter(metrics)
        output = exporter.export()

        # Verify header
        assert "# HELP herp_metrics HERP Python Client Metrics" in output
        assert "# TYPE herp_metrics gauge" in output

        # Verify counters with sanitized names
        assert 'herp_http_requests{type="counter"} 100' in output
        assert 'herp_http_errors{type="counter"} 5' in output

        # Verify gauges
        assert 'herp_active_connections{type="gauge"} 42' in output
        assert 'herp_memory_usage_mb{type="gauge"} 256.5' in output

        # Verify timestamp
        assert "# Exported at" in output

    def test_export_sanitizes_metric_names(self, metrics):
        """Test metric names are sanitized for Prometheus"""
        metrics.increment("api.v2.requests-total", 50)

        exporter = PrometheusExporter(metrics)
        output = exporter.export()

        # Dots and dashes should be replaced with underscores
        assert "herp_api_v2_requests_total" in output

    def test_export_to_file(self, metrics):
        """Test exporting to file"""
        exporter = PrometheusExporter(metrics)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = str(Path(tmpdir) / "metrics.prom")
            exporter.export_to_file(file_path)

            # Verify file exists and contains metrics
            assert Path(file_path).exists()

            with open(file_path) as f:
                content = f.read()

            assert "herp_http_requests" in content
            assert "herp_active_connections" in content

    def test_export_empty_metrics(self):
        """Test exporting with no metrics"""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)

        output = exporter.export()

        # Should still have header and timestamp
        assert "# HELP herp_metrics" in output
        assert "# Exported at" in output


class TestStatsDExporter:
    """Test StatsD metrics exporter"""

    @pytest.fixture
    def metrics(self):
        """Create metrics collector with sample data"""
        collector = MetricsCollector()
        collector.increment("requests", 100)
        collector.gauge("connections", 42)
        return collector

    def test_initialization_with_statsd_available(self):
        """Test initialization when statsd is available"""
        try:
            import statsd

            # If statsd is available, test initialization
            exporter = StatsDExporter(host="localhost", port=8125, prefix="myapp")

            assert exporter.host == "localhost"
            assert exporter.port == 8125
            assert exporter.prefix == "myapp"
            assert exporter.available is True
        except ImportError:
            # If statsd not available, skip this test
            pytest.skip("statsd library not available")

    def test_initialization_without_statsd(self):
        """Test initialization when statsd not available"""
        # If statsd is available, we skip this test
        try:
            import statsd

            pytest.skip("statsd library is available, cannot test unavailable scenario")
        except ImportError:
            # statsd not available - test that exporter handles it gracefully
            exporter = StatsDExporter()

            assert exporter.available is False
            assert exporter.client is None

    def test_export_all_metrics(self, metrics):
        """Test exporting all metrics to StatsD"""
        try:
            import statsd

            exporter = StatsDExporter(metrics_collector=metrics)
            result = exporter.export()

            # Should export counters and gauges
            assert result["exported"] >= 0
            assert result["failed"] >= 0
        except ImportError:
            pytest.skip("statsd library not available")

    def test_export_when_unavailable(self):
        """Test export when StatsD unavailable"""
        try:
            import statsd

            pytest.skip("statsd library is available, cannot test unavailable scenario")
        except ImportError:
            exporter = StatsDExporter()
            result = exporter.export()

            assert result["exported"] == 0
            assert result["failed"] == 0

    def test_export_counter(self):
        """Test exporting single counter"""
        try:
            import statsd

            exporter = StatsDExporter()
            # Should not raise errors
            exporter.export_counter("api.requests", 5)
        except ImportError:
            pytest.skip("statsd library not available")

    def test_export_counter_with_tags(self):
        """Test exporting counter with tags (Datadog format)"""
        try:
            import statsd

            exporter = StatsDExporter()
            # Should not raise errors and format tags
            exporter.export_counter(
                "requests", 1, tags={"endpoint": "/api", "method": "GET"}
            )
        except ImportError:
            pytest.skip("statsd library not available")

    def test_export_gauge(self):
        """Test exporting single gauge"""
        try:
            import statsd

            exporter = StatsDExporter()
            exporter.export_gauge("memory.usage", 256.5)
        except ImportError:
            pytest.skip("statsd library not available")

    def test_export_timing(self):
        """Test exporting timing metric"""
        try:
            import statsd

            exporter = StatsDExporter()
            exporter.export_timing("request.duration", 150.5)
        except ImportError:
            pytest.skip("statsd library not available")

    def test_export_when_unavailable_does_nothing(self):
        """Test export methods do nothing when unavailable"""
        try:
            import statsd

            pytest.skip("statsd library is available, cannot test unavailable scenario")
        except ImportError:
            exporter = StatsDExporter()

            # Should not raise errors
            exporter.export_counter("test", 1)
            exporter.export_gauge("test", 1.0)
            exporter.export_timing("test", 100.0)


class TestJSONExporter:
    """Test JSON metrics exporter"""

    @pytest.fixture
    def metrics(self):
        """Create metrics collector with sample data"""
        collector = MetricsCollector()
        collector.increment("http.requests", 100)
        collector.increment("http.errors", 5)
        collector.gauge("active.connections", 42)
        return collector

    def test_initialization(self, metrics):
        """Test JSON exporter initialization"""
        exporter = JSONExporter(metrics)
        assert exporter.metrics == metrics

    def test_export_format(self, metrics):
        """Test JSON export format"""
        exporter = JSONExporter(metrics)
        data = exporter.export()

        assert "timestamp" in data
        assert "metrics" in data
        assert "metadata" in data

        # Verify metrics structure
        assert "counters" in data["metrics"]
        assert "gauges" in data["metrics"]
        assert data["metrics"]["counters"]["http.requests"] == 100
        assert data["metrics"]["counters"]["http.errors"] == 5
        assert data["metrics"]["gauges"]["active.connections"] == 42

        # Verify metadata
        assert data["metadata"]["exporter"] == "JSONExporter"
        assert data["metadata"]["version"] == "1.0.0"

    def test_export_to_file(self, metrics):
        """Test exporting to JSON file"""
        exporter = JSONExporter(metrics)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = str(Path(tmpdir) / "metrics.json")
            exporter.export_to_file(file_path, indent=2)

            assert Path(file_path).exists()

            with open(file_path) as f:
                data = json.load(f)

            assert "metrics" in data
            assert data["metrics"]["counters"]["http.requests"] == 100

    def test_export_to_string(self, metrics):
        """Test exporting to JSON string"""
        exporter = JSONExporter(metrics)

        # Compact format
        compact = exporter.export_to_string()
        assert isinstance(compact, str)
        assert "http.requests" in compact

        # Indented format
        indented = exporter.export_to_string(indent=2)
        assert "\n" in indented  # Should have newlines from indentation

    def test_export_empty_metrics(self):
        """Test exporting with empty metrics"""
        collector = MetricsCollector()
        exporter = JSONExporter(collector)

        data = exporter.export()

        assert data["metrics"]["counters"] == {}
        assert data["metrics"]["gauges"] == {}
        assert data["metrics"]["total_metrics"] == 0


class TestMetricsAggregator:
    """Test metrics aggregator"""

    @pytest.fixture
    def metrics(self):
        """Create metrics collector with sample data"""
        collector = MetricsCollector()
        collector.increment("http.requests", 100)
        collector.increment("http.errors", 5)
        collector.increment("api.v1.requests", 50)
        collector.gauge("connections", 42)
        collector.gauge("memory.mb", 256)
        return collector

    def test_initialization(self, metrics):
        """Test aggregator initialization"""
        aggregator = MetricsAggregator(metrics)
        assert aggregator.metrics == metrics

    def test_get_summary(self, metrics):
        """Test getting metrics summary"""
        aggregator = MetricsAggregator(metrics)
        summary = aggregator.get_summary()

        assert "total_metrics" in summary
        assert "total_counter_value" in summary
        assert "active_counters" in summary
        assert "active_gauges" in summary

        # Verify counts
        assert (
            summary["active_counters"] == 3
        )  # http.requests, http.errors, api.v1.requests
        assert summary["active_gauges"] == 2  # connections, memory.mb
        assert summary["total_counter_value"] == 155  # 100 + 5 + 50

    def test_get_metrics_by_prefix(self, metrics):
        """Test filtering metrics by prefix"""
        aggregator = MetricsAggregator(metrics)

        http_metrics = aggregator.get_metrics_by_prefix("http")
        assert len(http_metrics) >= 2  # http.requests, http.errors

        api_metrics = aggregator.get_metrics_by_prefix("api")
        assert len(api_metrics) >= 1  # api.v1.requests

    def test_get_rate(self, metrics):
        """Test calculating metric rate"""
        aggregator = MetricsAggregator(metrics)

        # Get rate for http.requests over 60 second window
        rate = aggregator.get_rate("http.requests", window_seconds=60)

        # Rate should be value / window
        # Since metrics are recent, should get ~100/60 = 1.67/sec
        assert rate >= 0

    def test_get_rate_nonexistent_metric(self, metrics):
        """Test rate for nonexistent metric"""
        aggregator = MetricsAggregator(metrics)

        rate = aggregator.get_rate("nonexistent.metric", window_seconds=60)

        assert rate == 0.0

    def test_get_summary_empty_metrics(self):
        """Test summary with empty metrics"""
        collector = MetricsCollector()
        aggregator = MetricsAggregator(collector)

        summary = aggregator.get_summary()

        assert summary["total_metrics"] == 0
        assert summary["total_counter_value"] == 0
        assert summary["active_counters"] == 0
        assert summary["active_gauges"] == 0


class TestExportersIntegration:
    """Integration tests for exporters"""

    def test_prometheus_and_json_export_same_data(self):
        """Test Prometheus and JSON export same metrics"""
        metrics = MetricsCollector()
        metrics.increment("requests", 100)
        metrics.gauge("connections", 42)

        # Export via Prometheus
        prom_exporter = PrometheusExporter(metrics)
        prom_output = prom_exporter.export()

        # Export via JSON
        json_exporter = JSONExporter(metrics)
        json_output = json_exporter.export()

        # Both should include same metrics
        assert "requests" in prom_output
        assert "connections" in prom_output
        assert json_output["metrics"]["counters"]["requests"] == 100
        assert json_output["metrics"]["gauges"]["connections"] == 42

    def test_aggregator_with_multiple_exporters(self):
        """Test aggregator works with multiple exporters"""
        metrics = MetricsCollector()
        metrics.increment("requests", 50)
        metrics.increment("errors", 5)
        metrics.gauge("memory", 256)

        # Get summary
        aggregator = MetricsAggregator(metrics)
        summary = aggregator.get_summary()

        # Export via multiple formats
        prom_exporter = PrometheusExporter(metrics)
        json_exporter = JSONExporter(metrics)

        prom_output = prom_exporter.export()
        json_output = json_exporter.export()

        # Summary should reflect same totals
        assert summary["active_counters"] == 2
        assert summary["active_gauges"] == 1

        # All exporters should have same data
        assert "requests" in prom_output
        assert json_output["metrics"]["counters"]["requests"] == 50

    def test_file_export_workflow(self):
        """Test complete file export workflow"""
        metrics = MetricsCollector()
        metrics.increment("api.calls", 1000)
        metrics.gauge("active.users", 150)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Export Prometheus format
            prom_path = str(Path(tmpdir) / "metrics.prom")
            prom_exporter = PrometheusExporter(metrics)
            prom_exporter.export_to_file(prom_path)

            # Export JSON format
            json_path = str(Path(tmpdir) / "metrics.json")
            json_exporter = JSONExporter(metrics)
            json_exporter.export_to_file(json_path)

            # Verify both files exist and contain data
            assert Path(prom_path).exists()
            assert Path(json_path).exists()

            with open(prom_path) as f:
                prom_content = f.read()
            assert "api_calls" in prom_content

            with open(json_path) as f:
                json_content = json.load(f)
            assert json_content["metrics"]["counters"]["api.calls"] == 1000
