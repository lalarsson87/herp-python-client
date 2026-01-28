"""
Tests for HTTP Instrumentation
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.observability.http_instrumentation import (
    _extract_endpoint,
    instrument_http_request,
    instrument_http_request_async,
)


class TestExtractEndpoint:
    """Test endpoint extraction from URLs"""

    def test_extract_from_full_url(self):
        """Test extracting endpoint from full URL"""
        url = "https://api.example.com/v1/candidacies"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/v1/candidacies"

    def test_extract_from_full_url_with_trailing_slash(self):
        """Test extracting endpoint with trailing slash"""
        url = "https://api.example.com/v1/users/"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/v1/users/"

    def test_extract_from_relative_path(self):
        """Test extracting endpoint from relative path"""
        url = "/v1/candidacies/123"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/v1/candidacies/123"

    def test_extract_from_url_with_query_params(self):
        """Test extracting endpoint strips query params"""
        url = "/v1/candidacies?limit=10&offset=20"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/v1/candidacies"

    def test_extract_from_full_url_with_query_params(self):
        """Test extracting endpoint from full URL with query params"""
        url = "https://api.example.com/v1/candidacies?limit=10"
        endpoint = _extract_endpoint(url)
        # Should extract path, query params removed by relative path logic
        assert "/v1/candidacies" in endpoint

    def test_extract_from_root_url(self):
        """Test extracting from root URL"""
        url = "https://api.example.com/"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/"

    def test_extract_from_url_without_path(self):
        """Test extracting from URL without path"""
        url = "https://api.example.com"
        endpoint = _extract_endpoint(url)
        assert endpoint == "/"


class TestInstrumentHttpRequest:
    """Test synchronous HTTP request instrumentation"""

    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_request_when_telemetry_disabled(self, mock_enabled):
        """Test request executes without instrumentation when telemetry disabled"""
        mock_enabled.return_value = False

        mock_func = Mock(return_value="result")

        result = instrument_http_request("GET", "/test", mock_func, arg1="value1")

        assert result == "result"
        mock_func.assert_called_once_with(arg1="value1")

    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_request_when_tracer_not_available(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test request executes without instrumentation when tracer unavailable"""
        mock_enabled.return_value = True
        mock_get_tracer.return_value = None

        mock_func = Mock(return_value="result")

        result = instrument_http_request("GET", "/test", mock_func)

        assert result == "result"
        mock_record_metric.assert_not_called()

    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_successful_request_instrumentation(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test successful request creates span and records metrics"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_func = Mock(return_value=mock_response)

        result = instrument_http_request("GET", "/v1/candidacies", mock_func)

        # Verify span created
        mock_tracer.start_as_current_span.assert_called_once_with("HTTP GET")

        # Verify span attributes
        mock_span.set_attribute.assert_any_call("http.method", "GET")
        mock_span.set_attribute.assert_any_call("http.url", "/v1/candidacies")
        mock_span.set_attribute.assert_any_call("http.status_code", 200)

        # Verify metrics recorded
        assert mock_record_metric.call_count == 2  # request + response

        # Verify result
        assert result == mock_response

    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_request_with_error_instrumentation(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test failed request records error in span and metrics"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock function that raises
        error = ValueError("Connection failed")
        mock_func = Mock(side_effect=error)

        with pytest.raises(ValueError, match="Connection failed"):
            instrument_http_request("POST", "/v1/candidacies", mock_func)

        # Verify error recorded in span
        mock_span.set_attribute.assert_any_call("error", True)
        mock_span.set_attribute.assert_any_call("error.type", "ValueError")
        mock_span.set_attribute.assert_any_call("error.message", "Connection failed")
        mock_span.record_exception.assert_called_once_with(error)

        # Verify error metric recorded
        error_metric_call = [
            call
            for call in mock_record_metric.call_args_list
            if call[0][0] == "herp.http.errors"
        ]
        assert len(error_metric_call) == 1

    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_request_without_response_status_code(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test request handling when response has no status_code"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock response without status_code
        mock_response = Mock(spec=[])  # No status_code attribute
        mock_func = Mock(return_value=mock_response)

        result = instrument_http_request("GET", "/test", mock_func)

        # Should not set status_code attribute
        status_code_calls = [
            call
            for call in mock_span.set_attribute.call_args_list
            if "status_code" in str(call)
        ]
        assert len(status_code_calls) == 0

        # Should still record request metric
        request_metric_calls = [
            call
            for call in mock_record_metric.call_args_list
            if call[0][0] == "herp.http.requests"
        ]
        assert len(request_metric_calls) == 1

        assert result == mock_response

    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    def test_request_with_args_and_kwargs(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test request passes args and kwargs to function"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        mock_func = Mock(return_value="result")

        result = instrument_http_request(
            "POST", "/test", mock_func, "arg1", "arg2", key1="value1", key2="value2"
        )

        mock_func.assert_called_once_with("arg1", "arg2", key1="value1", key2="value2")
        assert result == "result"


class TestInstrumentHttpRequestAsync:
    """Test asynchronous HTTP request instrumentation"""

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_request_when_telemetry_disabled(self, mock_enabled):
        """Test async request executes without instrumentation when telemetry disabled"""
        mock_enabled.return_value = False

        mock_func = AsyncMock(return_value="result")

        result = await instrument_http_request_async(
            "GET", "/test", mock_func, arg1="value1"
        )

        assert result == "result"
        mock_func.assert_called_once_with(arg1="value1")

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_request_when_tracer_not_available(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test async request executes without instrumentation when tracer unavailable"""
        mock_enabled.return_value = True
        mock_get_tracer.return_value = None

        mock_func = AsyncMock(return_value="result")

        result = await instrument_http_request_async("GET", "/test", mock_func)

        assert result == "result"
        mock_record_metric.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_successful_request_instrumentation(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test async successful request creates span and records metrics"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_func = AsyncMock(return_value=mock_response)

        result = await instrument_http_request_async(
            "POST", "/v1/candidacies", mock_func
        )

        # Verify span created
        mock_tracer.start_as_current_span.assert_called_once_with("HTTP POST")

        # Verify span attributes
        mock_span.set_attribute.assert_any_call("http.method", "POST")
        mock_span.set_attribute.assert_any_call("http.url", "/v1/candidacies")
        mock_span.set_attribute.assert_any_call("http.status_code", 201)

        # Verify metrics recorded
        assert mock_record_metric.call_count == 2  # request + response

        # Verify result
        assert result == mock_response

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_request_with_error_instrumentation(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test async failed request records error in span and metrics"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock function that raises
        error = ConnectionError("Async connection failed")
        mock_func = AsyncMock(side_effect=error)

        with pytest.raises(ConnectionError, match="Async connection failed"):
            await instrument_http_request_async("GET", "/v1/candidacies", mock_func)

        # Verify error recorded in span
        mock_span.set_attribute.assert_any_call("error", True)
        mock_span.set_attribute.assert_any_call("error.type", "ConnectionError")
        mock_span.set_attribute.assert_any_call(
            "error.message", "Async connection failed"
        )
        mock_span.record_exception.assert_called_once_with(error)

        # Verify error metric recorded
        error_metric_call = [
            call
            for call in mock_record_metric.call_args_list
            if call[0][0] == "herp.http.errors"
        ]
        assert len(error_metric_call) == 1

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_request_without_response_status_code(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test async request handling when response has no status_code"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock response without status_code
        mock_response = Mock(spec=[])  # No status_code attribute
        mock_func = AsyncMock(return_value=mock_response)

        result = await instrument_http_request_async("GET", "/test", mock_func)

        # Should not set status_code attribute
        status_code_calls = [
            call
            for call in mock_span.set_attribute.call_args_list
            if "status_code" in str(call)
        ]
        assert len(status_code_calls) == 0

        assert result == mock_response

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_async_request_with_args_and_kwargs(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test async request passes args and kwargs to function"""
        mock_enabled.return_value = True

        # Mock tracer and span
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        mock_func = AsyncMock(return_value="result")

        result = await instrument_http_request_async(
            "POST", "/test", mock_func, "arg1", "arg2", key1="value1", key2="value2"
        )

        mock_func.assert_called_once_with("arg1", "arg2", key1="value1", key2="value2")
        assert result == "result"


class TestInstrumentationIntegration:
    """Integration tests for HTTP instrumentation"""

    @pytest.mark.asyncio
    @patch("src.core.observability.http_instrumentation.record_metric")
    @patch("src.core.observability.http_instrumentation.get_tracer")
    @patch("src.core.observability.http_instrumentation.is_telemetry_enabled")
    async def test_sync_and_async_record_same_metrics(
        self, mock_enabled, mock_get_tracer, mock_record_metric
    ):
        """Test sync and async instrumentation record same metrics"""
        mock_enabled.return_value = True

        # Mock tracer
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200

        # Sync request
        mock_record_metric.reset_mock()
        mock_func_sync = Mock(return_value=mock_response)
        instrument_http_request("GET", "/v1/test", mock_func_sync)
        sync_calls = mock_record_metric.call_args_list.copy()

        # Async request
        mock_record_metric.reset_mock()
        mock_func_async = AsyncMock(return_value=mock_response)
        await instrument_http_request_async("GET", "/v1/test", mock_func_async)
        async_calls = mock_record_metric.call_args_list.copy()

        # Should have same number of metric calls
        assert len(sync_calls) == len(async_calls) == 2

        # Metric names should be the same
        sync_names = [call[0][0] for call in sync_calls]
        async_names = [call[0][0] for call in async_calls]
        assert sync_names == async_names
