"""
Tests for Error Classification System
"""

import time
from unittest.mock import Mock

import pytest

from src.core.errors.classification import (
    ErrorCategory,
    ErrorSeverity,
    calculate_backoff,
    classify_error,
    smart_retry,
)
from src.core.errors.exceptions import (
    HerpAuthenticationError,
    HerpNetworkError,
    HerpNotFoundError,
    HerpRateLimitError,
    HerpServerError,
    HerpValidationError,
    NotionAuthenticationError,
    NotionNetworkError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionServerError,
    NotionValidationError,
    PermanentError,
    RetryBudgetExceededError,
    RetryError,
    TransientError,
)


class TestClassifyErrorTypeBased:
    """Test error classification by exception type"""

    def test_classify_herp_rate_limit_error(self):
        """Test classifying HERP rate limit error"""
        exc = HerpRateLimitError("Rate limit exceeded")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.RATE_LIMIT

    def test_classify_notion_rate_limit_error(self):
        """Test classifying Notion rate limit error"""
        exc = NotionRateLimitError("Too many requests")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.RATE_LIMIT

    def test_classify_herp_authentication_error(self):
        """Test classifying HERP authentication error"""
        exc = HerpAuthenticationError("Invalid API token")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_notion_authentication_error(self):
        """Test classifying Notion authentication error"""
        exc = NotionAuthenticationError("Unauthorized")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_herp_validation_error(self):
        """Test classifying HERP validation error"""
        exc = HerpValidationError("Invalid request body")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.VALIDATION

    def test_classify_notion_validation_error(self):
        """Test classifying Notion validation error"""
        exc = NotionValidationError("Bad request")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.VALIDATION

    def test_classify_herp_not_found_error(self):
        """Test classifying HERP not found error"""
        exc = HerpNotFoundError("Resource not found")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.NOT_FOUND

    def test_classify_notion_not_found_error(self):
        """Test classifying Notion not found error"""
        exc = NotionNotFoundError("Page does not exist")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.NOT_FOUND

    def test_classify_herp_server_error(self):
        """Test classifying HERP server error"""
        exc = HerpServerError("Internal server error")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_notion_server_error(self):
        """Test classifying Notion server error"""
        exc = NotionServerError("Service unavailable")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_herp_network_error(self):
        """Test classifying HERP network error"""
        exc = HerpNetworkError("Connection timeout")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.NETWORK

    def test_classify_notion_network_error(self):
        """Test classifying Notion network error"""
        exc = NotionNetworkError("Connection refused")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.NETWORK

    def test_classify_generic_transient_error(self):
        """Test classifying generic transient error"""
        exc = TransientError("Temporary issue")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.UNKNOWN

    def test_classify_generic_permanent_error(self):
        """Test classifying generic permanent error"""
        exc = PermanentError("Cannot proceed")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.UNKNOWN


class TestClassifyErrorStringBased:
    """Test error classification by exception message"""

    def test_classify_rate_limit_by_message(self):
        """Test classifying rate limit by message"""
        exc = Exception("Rate limit exceeded")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.RATE_LIMIT

    def test_classify_rate_limit_by_status_code(self):
        """Test classifying rate limit by HTTP 429"""
        exc = Exception("HTTP 429 Too Many Requests")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.RATE_LIMIT

    def test_classify_authentication_by_message(self):
        """Test classifying authentication error by message"""
        exc = Exception("Unauthorized: Invalid token")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_authentication_by_status_401(self):
        """Test classifying authentication by HTTP 401"""
        exc = Exception("HTTP 401 Unauthorized")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_authentication_by_status_403(self):
        """Test classifying authentication by HTTP 403"""
        exc = Exception("403 Forbidden")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.AUTHENTICATION

    def test_classify_validation_by_message(self):
        """Test classifying validation error by message"""
        exc = Exception("Validation failed: invalid input")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.VALIDATION

    def test_classify_validation_by_status_400(self):
        """Test classifying validation by HTTP 400"""
        exc = Exception("400 Bad Request")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.VALIDATION

    def test_classify_not_found_by_message(self):
        """Test classifying not found by message"""
        exc = Exception("Resource not found")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.NOT_FOUND

    def test_classify_not_found_by_status_404(self):
        """Test classifying not found by HTTP 404"""
        exc = Exception("HTTP 404 Not Found")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.PERMANENT
        assert category == ErrorCategory.NOT_FOUND

    def test_classify_server_error_by_status_500(self):
        """Test classifying server error by HTTP 500"""
        exc = Exception("500 Internal Server Error")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_server_error_by_status_502(self):
        """Test classifying server error by HTTP 502"""
        exc = Exception("502 Bad Gateway")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_server_error_by_status_503(self):
        """Test classifying server error by HTTP 503"""
        exc = Exception("503 Service Unavailable")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_server_error_by_status_504(self):
        """Test classifying server error by HTTP 504"""
        exc = Exception("504 Gateway Timeout")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.SERVER_ERROR

    def test_classify_network_error_by_message_timeout(self):
        """Test classifying network error by timeout message"""
        exc = Exception("Connection timeout")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.NETWORK

    def test_classify_network_error_by_message_connection(self):
        """Test classifying network error by connection message"""
        exc = Exception("Connection refused")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.NETWORK

    def test_classify_network_error_by_exception_type_name(self):
        """Test classifying network error by exception type name"""

        class TimeoutError(Exception):
            pass

        exc = TimeoutError("Request timed out")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.NETWORK

    def test_classify_unknown_error_defaults_to_transient(self):
        """Test unknown errors default to transient"""
        exc = Exception("Some random error")
        severity, category = classify_error(exc)

        assert severity == ErrorSeverity.TRANSIENT
        assert category == ErrorCategory.UNKNOWN


class TestCalculateBackoff:
    """Test backoff calculation"""

    def test_rate_limit_backoff_starts_higher(self):
        """Test rate limit errors have longer initial delay"""
        delay = calculate_backoff(0, ErrorCategory.RATE_LIMIT, jitter=False)
        assert delay >= 2.0  # RETRY_RATE_LIMIT_BASE_DELAY

    def test_network_backoff_moderate(self):
        """Test network errors have moderate delay"""
        delay = calculate_backoff(0, ErrorCategory.NETWORK, jitter=False)
        assert delay >= 0.5  # RETRY_NETWORK_BASE_DELAY

    def test_server_error_backoff_exponential(self):
        """Test server errors use exponential backoff"""
        delay0 = calculate_backoff(
            0, ErrorCategory.SERVER_ERROR, base_delay=1.0, jitter=False
        )
        delay1 = calculate_backoff(
            1, ErrorCategory.SERVER_ERROR, base_delay=1.0, jitter=False
        )
        delay2 = calculate_backoff(
            2, ErrorCategory.SERVER_ERROR, base_delay=1.0, jitter=False
        )

        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0

    def test_backoff_respects_max_delay(self):
        """Test backoff is capped at max_delay"""
        delay = calculate_backoff(
            10, ErrorCategory.RATE_LIMIT, max_delay=30.0, jitter=False
        )
        assert delay <= 30.0

    def test_backoff_with_jitter(self):
        """Test backoff adds jitter"""
        # Run multiple times to verify jitter varies
        delays = [
            calculate_backoff(0, ErrorCategory.NETWORK, jitter=True) for _ in range(50)
        ]

        # All delays should be in range
        base_delay = 0.5  # RETRY_NETWORK_BASE_DELAY
        assert all(base_delay * 0.5 <= d <= base_delay for d in delays)

        # Should have some variation (not all identical with 50 samples)
        assert len(set(delays)) > 5

    def test_backoff_without_jitter_is_deterministic(self):
        """Test backoff without jitter is deterministic"""
        delay1 = calculate_backoff(2, ErrorCategory.SERVER_ERROR, jitter=False)
        delay2 = calculate_backoff(2, ErrorCategory.SERVER_ERROR, jitter=False)

        assert delay1 == delay2


class TestSmartRetrySuccess:
    """Test smart_retry decorator with successful scenarios"""

    def test_successful_on_first_attempt(self):
        """Test function succeeds on first attempt"""
        mock_func = Mock(return_value="success", __name__="test_func")
        decorated = smart_retry()(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_successful_after_retry(self):
        """Test function succeeds after retry"""
        mock_func = Mock(
            side_effect=[HerpServerError("Server error"), "success"],
            __name__="test_func",
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_retries_transient_errors(self):
        """Test transient errors are retried"""
        mock_func = Mock(
            side_effect=[
                HerpNetworkError("Network error"),
                HerpServerError("Server error"),
                "success",
            ],
            __name__="test_func",
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3


class TestSmartRetryPermanentErrors:
    """Test smart_retry with permanent errors"""

    def test_fails_fast_on_permanent_error(self):
        """Test permanent errors fail immediately without retry"""
        mock_func = Mock(
            side_effect=HerpAuthenticationError("Unauthorized"), __name__="test_func"
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        with pytest.raises(HerpAuthenticationError):
            decorated()

        # Should not retry permanent errors
        assert mock_func.call_count == 1

    def test_fails_fast_on_validation_error(self):
        """Test validation errors fail immediately"""
        mock_func = Mock(
            side_effect=HerpValidationError("Invalid input"), __name__="test_func"
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        with pytest.raises(HerpValidationError):
            decorated()

        assert mock_func.call_count == 1

    def test_fails_fast_on_not_found_error(self):
        """Test not found errors fail immediately"""
        mock_func = Mock(
            side_effect=HerpNotFoundError("Resource not found"), __name__="test_func"
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        with pytest.raises(HerpNotFoundError):
            decorated()

        assert mock_func.call_count == 1


class TestSmartRetryMaxAttempts:
    """Test smart_retry max attempts behavior"""

    def test_exhausts_max_attempts(self):
        """Test all attempts are exhausted"""
        mock_func = Mock(
            side_effect=HerpServerError("Server error"), __name__="test_func"
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        with pytest.raises(RetryError):
            decorated()

        assert mock_func.call_count == 3

    def test_raises_retry_error_after_max_attempts(self):
        """Test RetryError is raised after max attempts"""
        mock_func = Mock(
            side_effect=HerpNetworkError("Network error"), __name__="test_func"
        )
        decorated = smart_retry(max_attempts=2, base_delay=0.01)(mock_func)

        with pytest.raises(RetryError, match="Failed after 2 attempts"):
            decorated()


class TestSmartRetryBudget:
    """Test smart_retry with retry budget"""

    def test_exceeds_retry_budget(self):
        """Test retry budget is enforced"""
        mock_func = Mock(
            side_effect=HerpServerError("Server error"), __name__="test_func"
        )
        # Very long delay but short budget
        decorated = smart_retry(
            max_attempts=10, base_delay=1.0, max_total_duration=0.5, jitter=False
        )(mock_func)

        with pytest.raises(RetryBudgetExceededError, match="Retry budget"):
            decorated()

        # Should stop before max_attempts due to budget
        assert mock_func.call_count < 10

    def test_retry_budget_allows_retries_within_limit(self):
        """Test retries work within budget"""
        mock_func = Mock(
            side_effect=[
                HerpNetworkError("Network error"),
                HerpNetworkError("Network error"),
                "success",
            ],
            __name__="test_func",
        )
        # Short delays, reasonable budget
        decorated = smart_retry(
            max_attempts=5, base_delay=0.01, max_total_duration=1.0
        )(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3


class TestSmartRetryCallbacks:
    """Test smart_retry with callbacks"""

    def test_on_retry_callback_called(self):
        """Test on_retry callback is called"""
        callback = Mock()
        mock_func = Mock(
            side_effect=[HerpServerError("Error"), "success"], __name__="test_func"
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01, on_retry=callback)(
            mock_func
        )

        result = decorated()

        assert result == "success"
        callback.assert_called_once()

        # Verify callback arguments
        args = callback.call_args[0]
        assert isinstance(args[0], HerpServerError)  # exception
        assert args[1] == 0  # attempt
        assert args[2] == ErrorSeverity.TRANSIENT  # severity
        assert args[3] == ErrorCategory.SERVER_ERROR  # category

    def test_on_retry_callback_not_called_on_success(self):
        """Test callback not called if first attempt succeeds"""
        callback = Mock()
        mock_func = Mock(return_value="success", __name__="test_func")
        decorated = smart_retry(on_retry=callback)(mock_func)

        result = decorated()

        assert result == "success"
        callback.assert_not_called()


class TestSmartRetryRetryableExceptions:
    """Test smart_retry with retryable_exceptions filter"""

    def test_only_retries_specified_exception_types(self):
        """Test only retries exceptions in retryable_exceptions"""
        mock_func = Mock(side_effect=ValueError("Not retryable"), __name__="test_func")
        decorated = smart_retry(
            max_attempts=3, base_delay=0.01, retryable_exceptions=(HerpServerError,)
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        # Should not retry ValueError
        assert mock_func.call_count == 1

    def test_retries_matching_exception_types(self):
        """Test retries exceptions in retryable_exceptions"""
        mock_func = Mock(
            side_effect=[HerpServerError("Error"), "success"], __name__="test_func"
        )
        decorated = smart_retry(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=(HerpServerError, HerpNetworkError),
        )(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2


class TestSmartRetryIntegration:
    """Integration tests for smart_retry"""

    def test_retry_with_multiple_error_types(self):
        """Test retry handles multiple error types correctly"""
        mock_func = Mock(
            side_effect=[
                HerpRateLimitError("Rate limit"),  # Transient
                HerpServerError("Server error"),  # Transient
                HerpNetworkError("Network error"),  # Transient
                "success",
            ],
            __name__="test_func",
        )
        decorated = smart_retry(max_attempts=5, base_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 4

    def test_retry_preserves_function_metadata(self):
        """Test decorator preserves function metadata"""

        @smart_retry()
        def my_function():
            """My function docstring"""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My function docstring"

    def test_retry_with_function_args_and_kwargs(self):
        """Test retry passes args and kwargs correctly"""
        mock_func = Mock(
            side_effect=[HerpNetworkError("Network error"), "success"],
            __name__="test_func",
        )
        decorated = smart_retry(max_attempts=3, base_delay=0.01)(mock_func)

        result = decorated("arg1", "arg2", key1="value1", key2="value2")

        assert result == "success"
        assert mock_func.call_count == 2

        # Verify args/kwargs passed correctly on both attempts
        mock_func.assert_called_with("arg1", "arg2", key1="value1", key2="value2")
