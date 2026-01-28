"""
Tests for metrics collector
"""

import threading
import time

import pytest

from src.core.observability.metrics import (
    MetricData,
    MetricsCollector,
    get_metrics_collector,
    reset_global_metrics_collector,
)


class TestMetricData:
    """Test MetricData dataclass"""

    def test_metric_data_creation(self):
        """Test creating MetricData"""
        metric = MetricData(name="test.metric", value=42.0, tags={"env": "test"})

        assert metric.name == "test.metric"
        assert metric.value == 42.0
        assert metric.tags == {"env": "test"}
        assert isinstance(metric.timestamp, float)

    def test_metric_data_default_tags(self):
        """Test MetricData with default empty tags"""
        metric = MetricData(name="test", value=1.0)

        assert metric.tags == {}

    def test_metric_data_timestamp_is_set(self):
        """Test MetricData timestamp is automatically set"""
        before = time.time()
        metric = MetricData(name="test", value=1.0)
        after = time.time()

        assert before <= metric.timestamp <= after


class TestMetricsCollector:
    """Test MetricsCollector"""

    def test_initialization(self):
        """Test collector initialization"""
        collector = MetricsCollector(enabled=True)

        assert collector.enabled is True
        assert len(collector._metrics) == 0
        assert len(collector._counters) == 0
        assert len(collector._gauges) == 0

    def test_initialization_disabled(self):
        """Test collector can be disabled"""
        collector = MetricsCollector(enabled=False)

        assert collector.enabled is False

    def test_increment_counter(self):
        """Test incrementing a counter"""
        collector = MetricsCollector()

        collector.increment("request.count", value=1)
        collector.increment("request.count", value=2)

        assert collector.get_counter("request.count") == 3

    def test_increment_counter_with_tags(self):
        """Test increment with tags"""
        collector = MetricsCollector()

        collector.increment("request.count", value=1, tags={"method": "GET"})

        metrics = collector.get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].tags == {"method": "GET"}

    def test_increment_counter_default_value(self):
        """Test increment with default value of 1"""
        collector = MetricsCollector()

        collector.increment("counter")
        collector.increment("counter")

        assert collector.get_counter("counter") == 2

    def test_increment_multiple_counters(self):
        """Test multiple independent counters"""
        collector = MetricsCollector()

        collector.increment("counter.a", value=5)
        collector.increment("counter.b", value=3)

        assert collector.get_counter("counter.a") == 5
        assert collector.get_counter("counter.b") == 3

    def test_gauge(self):
        """Test setting a gauge value"""
        collector = MetricsCollector()

        collector.gauge("cpu.usage", 75.5)
        collector.gauge("memory.usage", 82.3)

        assert collector.get_gauge("cpu.usage") == 75.5
        assert collector.get_gauge("memory.usage") == 82.3

    def test_gauge_with_tags(self):
        """Test gauge with tags"""
        collector = MetricsCollector()

        collector.gauge("temperature", 22.5, tags={"location": "server_room"})

        metrics = collector.get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].value == 22.5
        assert metrics[0].tags == {"location": "server_room"}

    def test_gauge_overwrites_previous_value(self):
        """Test gauge overwrites previous value"""
        collector = MetricsCollector()

        collector.gauge("cpu.usage", 50.0)
        collector.gauge("cpu.usage", 75.0)

        # Latest value should be stored
        assert collector.get_gauge("cpu.usage") == 75.0

    def test_timing_metric(self):
        """Test recording timing metric"""
        collector = MetricsCollector()

        collector.timing("request.duration", 123.45)

        metrics = collector.get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].name == "request.duration"
        assert metrics[0].value == 123.45

    def test_timing_with_tags(self):
        """Test timing with tags"""
        collector = MetricsCollector()

        collector.timing("api.latency", 50.5, tags={"endpoint": "/users"})

        metrics = collector.get_all_metrics()
        assert metrics[0].tags == {"endpoint": "/users"}

    def test_record_generic_metric(self):
        """Test recording generic metric"""
        collector = MetricsCollector()

        collector.record("custom.metric", 999.0, tags={"type": "custom"})

        metrics = collector.get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0].name == "custom.metric"
        assert metrics[0].value == 999.0

    def test_get_counter_nonexistent(self):
        """Test getting nonexistent counter returns 0"""
        collector = MetricsCollector()

        assert collector.get_counter("nonexistent") == 0

    def test_get_gauge_nonexistent(self):
        """Test getting nonexistent gauge returns None"""
        collector = MetricsCollector()

        assert collector.get_gauge("nonexistent") is None

    def test_get_all_metrics(self):
        """Test getting all metrics"""
        collector = MetricsCollector()

        collector.increment("counter", value=1)
        collector.gauge("gauge", 50.0)
        collector.timing("timer", 100.0)

        metrics = collector.get_all_metrics()

        assert len(metrics) == 3
        assert any(m.name == "counter" for m in metrics)
        assert any(m.name == "gauge" for m in metrics)
        assert any(m.name == "timer" for m in metrics)

    def test_get_all_metrics_returns_copy(self):
        """Test get_all_metrics returns a copy"""
        collector = MetricsCollector()

        collector.increment("test")

        metrics1 = collector.get_all_metrics()
        metrics2 = collector.get_all_metrics()

        # Should be different list instances
        assert metrics1 is not metrics2
        # But same content
        assert len(metrics1) == len(metrics2)

    def test_get_stats(self):
        """Test getting statistics"""
        collector = MetricsCollector()

        collector.increment("counter.a", value=5)
        collector.increment("counter.b", value=3)
        collector.gauge("gauge.x", 10.0)
        collector.gauge("gauge.y", 20.0)

        stats = collector.get_stats()

        assert stats["total_metrics"] == 4
        assert stats["enabled"] is True
        assert stats["counters"]["counter.a"] == 5
        assert stats["counters"]["counter.b"] == 3
        assert stats["gauges"]["gauge.x"] == 10.0
        assert stats["gauges"]["gauge.y"] == 20.0

    def test_reset(self):
        """Test resetting metrics"""
        collector = MetricsCollector()

        collector.increment("counter", value=10)
        collector.gauge("gauge", 50.0)
        collector.timing("timer", 100.0)

        assert len(collector.get_all_metrics()) == 3

        collector.reset()

        assert len(collector.get_all_metrics()) == 0
        assert collector.get_counter("counter") == 0
        assert collector.get_gauge("gauge") is None

    def test_disabled_collector_does_not_record(self):
        """Test disabled collector doesn't record metrics"""
        collector = MetricsCollector(enabled=False)

        collector.increment("counter")
        collector.gauge("gauge", 10.0)
        collector.timing("timer", 50.0)

        # No metrics should be recorded
        assert len(collector.get_all_metrics()) == 0
        assert collector.get_counter("counter") == 0

    def test_disabled_collector_stats(self):
        """Test stats on disabled collector"""
        collector = MetricsCollector(enabled=False)

        stats = collector.get_stats()

        assert stats["enabled"] is False
        assert stats["total_metrics"] == 0


class TestMetricsCollectorThreadSafety:
    """Test thread safety of MetricsCollector"""

    def test_concurrent_increments(self):
        """Test concurrent counter increments are thread-safe"""
        collector = MetricsCollector()
        num_threads = 10
        increments_per_thread = 100

        def increment_counter():
            for _ in range(increments_per_thread):
                collector.increment("shared.counter")

        threads = [threading.Thread(target=increment_counter) for _ in range(num_threads)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have exactly num_threads * increments_per_thread
        expected = num_threads * increments_per_thread
        assert collector.get_counter("shared.counter") == expected

    def test_concurrent_gauge_updates(self):
        """Test concurrent gauge updates are thread-safe"""
        collector = MetricsCollector()
        num_threads = 10

        def update_gauge(value):
            for _ in range(50):
                collector.gauge("shared.gauge", value)

        threads = [
            threading.Thread(target=update_gauge, args=(i,)) for i in range(num_threads)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Final value should be one of the thread values
        final_value = collector.get_gauge("shared.gauge")
        assert final_value in range(num_threads)

    def test_concurrent_read_write(self):
        """Test concurrent reads and writes"""
        collector = MetricsCollector()
        errors = []

        def writer():
            try:
                for i in range(100):
                    collector.increment("counter", value=1)
                    collector.gauge("gauge", float(i))
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for _ in range(100):
                    collector.get_all_metrics()
                    collector.get_stats()
                    collector.get_counter("counter")
                    collector.get_gauge("gauge")
            except Exception as e:
                errors.append(e)

        threads = []
        threads.extend([threading.Thread(target=writer) for _ in range(3)])
        threads.extend([threading.Thread(target=reader) for _ in range(3)])

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0


class TestGlobalMetricsCollector:
    """Test global metrics collector singleton"""

    def teardown_method(self):
        """Reset global collector after each test"""
        reset_global_metrics_collector()

    def test_get_metrics_collector_singleton(self):
        """Test get_metrics_collector returns singleton"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Should be the same instance
        assert collector1 is collector2

    def test_get_metrics_collector_creates_on_first_call(self):
        """Test global collector is created on first call"""
        reset_global_metrics_collector()

        collector = get_metrics_collector()

        assert collector is not None
        assert isinstance(collector, MetricsCollector)

    def test_get_metrics_collector_enabled_parameter(self):
        """Test enabled parameter on first call"""
        reset_global_metrics_collector()

        collector = get_metrics_collector(enabled=False)

        assert collector.enabled is False

    def test_get_metrics_collector_enabled_ignored_on_subsequent_calls(self):
        """Test enabled parameter is ignored on subsequent calls"""
        reset_global_metrics_collector()

        collector1 = get_metrics_collector(enabled=True)
        collector2 = get_metrics_collector(enabled=False)

        # Should be same instance, first call's setting wins
        assert collector1 is collector2
        assert collector1.enabled is True

    def test_reset_global_metrics_collector(self):
        """Test resetting global collector"""
        collector1 = get_metrics_collector()
        collector1.increment("test")

        reset_global_metrics_collector()

        collector2 = get_metrics_collector()

        # Should be new instance
        assert collector2 is not collector1
        # Should be clean
        assert collector2.get_counter("test") == 0

    def test_reset_clears_metrics(self):
        """Test reset clears metrics from global collector"""
        collector = get_metrics_collector()
        collector.increment("counter", value=10)
        collector.gauge("gauge", 50.0)

        reset_global_metrics_collector()

        # Get new instance
        new_collector = get_metrics_collector()

        assert new_collector.get_counter("counter") == 0
        assert new_collector.get_gauge("gauge") is None

    def test_global_collector_thread_safety(self):
        """Test global collector singleton is thread-safe"""
        reset_global_metrics_collector()

        collectors = []

        def get_collector():
            collectors.append(get_metrics_collector())

        threads = [threading.Thread(target=get_collector) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All should be the same instance
        first = collectors[0]
        assert all(c is first for c in collectors)


class TestMetricsCollectorEdgeCases:
    """Test edge cases for metrics collector"""

    def test_very_large_counter_value(self):
        """Test handling very large counter values"""
        collector = MetricsCollector()

        collector.increment("big.counter", value=1_000_000_000)

        assert collector.get_counter("big.counter") == 1_000_000_000

    def test_negative_counter_value(self):
        """Test handling negative counter values"""
        collector = MetricsCollector()

        collector.increment("counter", value=-5)

        # Should allow negative increments (decrement)
        assert collector.get_counter("counter") == -5

    def test_zero_values(self):
        """Test handling zero values"""
        collector = MetricsCollector()

        collector.increment("counter", value=0)
        collector.gauge("gauge", 0.0)
        collector.timing("timer", 0.0)

        assert collector.get_counter("counter") == 0
        assert collector.get_gauge("gauge") == 0.0

    def test_empty_metric_name(self):
        """Test handling empty metric name"""
        collector = MetricsCollector()

        collector.increment("")

        # Should allow empty names
        assert collector.get_counter("") == 1

    def test_metric_name_with_special_characters(self):
        """Test metric names with special characters"""
        collector = MetricsCollector()

        collector.increment("metric:name.with-special_chars/123")

        assert collector.get_counter("metric:name.with-special_chars/123") == 1

    def test_none_tags(self):
        """Test handling None tags"""
        collector = MetricsCollector()

        collector.increment("counter", tags=None)

        # Should use empty dict
        metrics = collector.get_all_metrics()
        assert metrics[0].tags == {}

    def test_many_metrics(self):
        """Test handling many metrics"""
        collector = MetricsCollector()

        # Record 1000 different metrics
        for i in range(1000):
            collector.increment(f"metric.{i}")

        stats = collector.get_stats()
        assert stats["total_metrics"] == 1000
