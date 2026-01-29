"""
Tests for OpenTelemetry Instrumentation
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestTelemetryAvailability:
    """Test OpenTelemetry availability checks"""

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", True)
    def test_is_telemetry_available_when_installed(self):
        """Test availability when OpenTelemetry is installed"""
        from src.core.observability.opentelemetry import is_telemetry_available

        assert is_telemetry_available() is True

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", False)
    def test_is_telemetry_available_when_not_installed(self):
        """Test availability when OpenTelemetry not installed"""
        from src.core.observability.opentelemetry import is_telemetry_available

        assert is_telemetry_available() is False

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", True)
    @patch("src.core.observability.opentelemetry._telemetry_enabled", True)
    def test_is_telemetry_enabled_when_active(self):
        """Test enabled check when telemetry is active"""
        from src.core.observability.opentelemetry import is_telemetry_enabled

        assert is_telemetry_enabled() is True

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", True)
    @patch("src.core.observability.opentelemetry._telemetry_enabled", False)
    def test_is_telemetry_enabled_when_not_initialized(self):
        """Test enabled check when not initialized"""
        from src.core.observability.opentelemetry import is_telemetry_enabled

        assert is_telemetry_enabled() is False

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", False)
    @patch("src.core.observability.opentelemetry._telemetry_enabled", True)
    def test_is_telemetry_enabled_when_otel_not_available(self):
        """Test enabled check returns False when OTEL not available"""
        from src.core.observability.opentelemetry import is_telemetry_enabled

        # Even if _telemetry_enabled=True, should return False if OTEL_AVAILABLE=False
        assert is_telemetry_enabled() is False


class TestSetupTelemetry:
    """Test OpenTelemetry setup"""

    @patch("src.core.observability.opentelemetry.OTEL_AVAILABLE", False)
    def test_setup_when_otel_not_available(self):
        """Test setup returns None when OpenTelemetry not available"""
        from src.core.observability.opentelemetry import setup_telemetry

        tracer, meter = setup_telemetry()

        assert tracer is None
        assert meter is None

    def test_setup_requires_opentelemetry(self):
        """Test setup gracefully handles missing OpenTelemetry"""
        # When OTEL_AVAILABLE is False in actual environment
        from src.core.observability.opentelemetry import OTEL_AVAILABLE, setup_telemetry

        if not OTEL_AVAILABLE:
            tracer, meter = setup_telemetry()
            assert tracer is None
            assert meter is None
        else:
            # Skip if OpenTelemetry is actually available
            pytest.skip("OpenTelemetry is available, cannot test unavailable scenario")


class TestGetTracerMeter:
    """Test tracer and meter getters"""

    @patch("src.core.observability.opentelemetry._tracer", None)
    def test_get_tracer_when_not_initialized(self):
        """Test get_tracer returns None when not initialized"""
        from src.core.observability.opentelemetry import get_tracer

        assert get_tracer() is None

    @patch("src.core.observability.opentelemetry._tracer", MagicMock())
    def test_get_tracer_when_initialized(self):
        """Test get_tracer returns tracer when initialized"""
        from src.core.observability.opentelemetry import get_tracer

        tracer = get_tracer()
        assert tracer is not None

    @patch("src.core.observability.opentelemetry._meter", None)
    def test_get_meter_when_not_initialized(self):
        """Test get_meter returns None when not initialized"""
        from src.core.observability.opentelemetry import get_meter

        assert get_meter() is None

    @patch("src.core.observability.opentelemetry._meter", MagicMock())
    def test_get_meter_when_initialized(self):
        """Test get_meter returns meter when initialized"""
        from src.core.observability.opentelemetry import get_meter

        meter = get_meter()
        assert meter is not None


class TestTraceSpan:
    """Test trace_span context manager"""

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=False
    )
    def test_trace_span_when_disabled(self, mock_enabled):
        """Test trace_span yields None when telemetry disabled"""
        from src.core.observability.opentelemetry import trace_span

        with trace_span("test_span") as span:
            assert span is None

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_trace_span_creates_span(self, mock_tracer, mock_enabled):
        """Test trace_span creates and yields span"""
        from src.core.observability.opentelemetry import trace_span

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        with trace_span("test_span") as span:
            assert span == mock_span

        mock_tracer.start_as_current_span.assert_called_once_with("test_span")

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_trace_span_sets_attributes(self, mock_tracer, mock_enabled):
        """Test trace_span sets custom attributes"""
        from src.core.observability.opentelemetry import trace_span

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        attributes = {"key1": "value1", "key2": "value2"}

        with trace_span("test_span", attributes=attributes):
            pass

        # Verify attributes were set
        assert mock_span.set_attribute.call_count == 2
        mock_span.set_attribute.assert_any_call("key1", "value1")
        mock_span.set_attribute.assert_any_call("key2", "value2")


class TestTraceFunctionDecorator:
    """Test trace_function decorator"""

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=False
    )
    def test_decorator_when_disabled(self, mock_enabled):
        """Test decorator doesn't create span when telemetry disabled"""
        from src.core.observability.opentelemetry import trace_function

        @trace_function()
        def test_func():
            return "result"

        result = test_func()
        assert result == "result"

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_decorator_creates_span(self, mock_tracer, mock_enabled):
        """Test decorator creates span for function"""
        from src.core.observability.opentelemetry import trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        @trace_function()
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        mock_tracer.start_as_current_span.assert_called_once_with("test_func")
        mock_span.set_attribute.assert_any_call("function.name", "test_func")
        mock_span.set_attribute.assert_any_call("success", True)

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_decorator_with_custom_name(self, mock_tracer, mock_enabled):
        """Test decorator uses custom span name"""
        from src.core.observability.opentelemetry import trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        @trace_function(name="custom_span_name")
        def test_func():
            return "result"

        test_func()

        mock_tracer.start_as_current_span.assert_called_once_with("custom_span_name")

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_decorator_with_attributes(self, mock_tracer, mock_enabled):
        """Test decorator sets custom attributes"""
        from src.core.observability.opentelemetry import trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        @trace_function(attributes={"operation": "test"})
        def test_func():
            return "result"

        test_func()

        mock_span.set_attribute.assert_any_call("operation", "test")

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    def test_decorator_records_exception(self, mock_tracer, mock_enabled):
        """Test decorator records exception in span"""
        from src.core.observability.opentelemetry import trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        @trace_function()
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_func()

        # Verify error attributes
        mock_span.set_attribute.assert_any_call("success", False)
        mock_span.set_attribute.assert_any_call("error.type", "ValueError")
        mock_span.set_attribute.assert_any_call("error.message", "Test error")
        mock_span.record_exception.assert_called_once()


class TestAsyncTraceFunctionDecorator:
    """Test async_trace_function decorator"""

    @pytest.mark.asyncio
    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=False
    )
    async def test_async_decorator_when_disabled(self, mock_enabled):
        """Test async decorator doesn't create span when telemetry disabled"""
        from src.core.observability.opentelemetry import async_trace_function

        # async_trace_function is incorrectly defined as async, so we need to await it
        decorator = await async_trace_function()

        @decorator
        async def test_func():
            return "result"

        result = await test_func()
        assert result == "result"

    @pytest.mark.asyncio
    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    async def test_async_decorator_creates_span(self, mock_tracer, mock_enabled):
        """Test async decorator creates span for async function"""
        from src.core.observability.opentelemetry import async_trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        decorator = await async_trace_function()

        @decorator
        async def test_func():
            return "result"

        result = await test_func()

        assert result == "result"
        mock_tracer.start_as_current_span.assert_called_once_with("test_func")
        mock_span.set_attribute.assert_any_call("function.name", "test_func")
        mock_span.set_attribute.assert_any_call("success", True)

    @pytest.mark.asyncio
    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    async def test_async_decorator_records_exception(self, mock_tracer, mock_enabled):
        """Test async decorator records exception in span"""
        from src.core.observability.opentelemetry import async_trace_function

        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        decorator = await async_trace_function()

        @decorator
        async def test_func():
            raise ValueError("Async error")

        with pytest.raises(ValueError, match="Async error"):
            await test_func()

        # Verify error attributes
        mock_span.set_attribute.assert_any_call("success", False)
        mock_span.set_attribute.assert_any_call("error.type", "ValueError")
        mock_span.set_attribute.assert_any_call("error.message", "Async error")
        mock_span.record_exception.assert_called_once()


class TestRecordMetric:
    """Test record_metric function"""

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=False
    )
    def test_record_metric_when_disabled(self, mock_enabled):
        """Test record_metric does nothing when telemetry disabled"""
        from src.core.observability.opentelemetry import record_metric

        # Should not raise errors
        record_metric("test.metric", 1.0)

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._meter")
    def test_record_counter_metric(self, mock_meter, mock_enabled):
        """Test recording counter metric"""
        from src.core.observability.opentelemetry import record_metric

        mock_counter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        record_metric("test.counter", 5.0, metric_type="counter")

        mock_meter.create_counter.assert_called_once_with("test.counter")
        mock_counter.add.assert_called_once_with(5.0, attributes={})

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._meter")
    def test_record_histogram_metric(self, mock_meter, mock_enabled):
        """Test recording histogram metric"""
        from src.core.observability.opentelemetry import record_metric

        mock_histogram = MagicMock()
        mock_meter.create_histogram.return_value = mock_histogram

        record_metric("test.histogram", 150.5, metric_type="histogram")

        mock_meter.create_histogram.assert_called_once_with("test.histogram")
        mock_histogram.record.assert_called_once_with(150.5, attributes={})

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._meter")
    def test_record_gauge_metric(self, mock_meter, mock_enabled):
        """Test recording gauge metric (using up-down counter)"""
        from src.core.observability.opentelemetry import record_metric

        mock_gauge = MagicMock()
        mock_meter.create_up_down_counter.return_value = mock_gauge

        record_metric("test.gauge", 42.0, metric_type="gauge")

        mock_meter.create_up_down_counter.assert_called_once_with("test.gauge")
        mock_gauge.add.assert_called_once_with(42.0, attributes={})

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._meter")
    def test_record_metric_with_attributes(self, mock_meter, mock_enabled):
        """Test recording metric with attributes"""
        from src.core.observability.opentelemetry import record_metric

        mock_counter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        attributes = {"endpoint": "/api/v1", "method": "GET"}
        record_metric(
            "http.requests", 1.0, attributes=attributes, metric_type="counter"
        )

        mock_counter.add.assert_called_once_with(1.0, attributes=attributes)

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._meter")
    def test_record_metric_handles_error(self, mock_meter, mock_enabled):
        """Test record_metric handles errors gracefully"""
        from src.core.observability.opentelemetry import record_metric

        mock_counter = MagicMock()
        mock_counter.add.side_effect = Exception("Metric error")
        mock_meter.create_counter.return_value = mock_counter

        # Should not raise, but log debug message
        record_metric("test.counter", 1.0, metric_type="counter")


class TestOpenTelemetryIntegration:
    """Integration tests for OpenTelemetry module"""

    @patch(
        "src.core.observability.opentelemetry.is_telemetry_enabled", return_value=True
    )
    @patch("src.core.observability.opentelemetry._tracer")
    @patch("src.core.observability.opentelemetry._meter")
    def test_decorator_and_metric_integration(
        self, mock_meter, mock_tracer, mock_enabled
    ):
        """Test integration of decorator and metric recording"""
        from src.core.observability.opentelemetry import record_metric, trace_function

        # Setup mocks
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )

        mock_counter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        # Use decorator
        @trace_function(name="test_operation")
        def sample_operation():
            # Record metric inside traced function
            record_metric("operations.count", 1.0, metric_type="counter")
            return "completed"

        result = sample_operation()

        # Verify results
        assert result == "completed"
        mock_tracer.start_as_current_span.assert_called_once_with("test_operation")
        mock_span.set_attribute.assert_any_call("success", True)
        mock_counter.add.assert_called_once_with(1.0, attributes={})
