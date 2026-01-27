#!/usr/bin/env python3
"""
Unit tests for Exception Hierarchy

Tests exception types and error classification.
"""

import pytest

from src.core.errors.exceptions import (
    CacheError,
    CacheFullError,
    CacheSerializationError,
    CircuitBreakerError,
    HerpAPIError,
    HerpAuthenticationError,
    HerpNetworkError,
    HerpNotFoundError,
    HerpNotionError,
    HerpRateLimitError,
    HerpServerError,
    HerpValidationError,
    NotionAPIError,
    NotionAuthenticationError,
    NotionNetworkError,
    NotionNotFoundError,
    NotionRateLimitError,
    NotionServerError,
    NotionValidationError,
    PermanentError,
    RetryBudgetExceededError,
    RetryError,
    SyncDataError,
    SyncError,
    SyncTimeoutError,
    SyncValidationError,
    TransientError,
    exception_from_http_status,
    is_permanent_error,
    is_transient_error,
)


class TestBaseExceptions:
    """Tests for base exception classes"""

    def test_herp_notion_error_is_base(self):
        """Test HerpNotionError is the base exception"""
        error = HerpNotionError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_transient_error_inherits_from_base(self):
        """Test TransientError inherits from HerpNotionError"""
        error = TransientError("Test transient")
        assert isinstance(error, HerpNotionError)
        assert isinstance(error, TransientError)

    def test_permanent_error_inherits_from_base(self):
        """Test PermanentError inherits from HerpNotionError"""
        error = PermanentError("Test permanent")
        assert isinstance(error, HerpNotionError)
        assert isinstance(error, PermanentError)


class TestHerpAPIExceptions:
    """Tests for HERP API exceptions"""

    def test_herp_api_error(self):
        """Test HerpAPIError"""
        error = HerpAPIError("API error")
        assert isinstance(error, HerpNotionError)
        assert str(error) == "API error"

    def test_herp_rate_limit_error_is_transient(self):
        """Test HerpRateLimitError is transient"""
        error = HerpRateLimitError("Rate limit exceeded")
        assert isinstance(error, TransientError)
        assert isinstance(error, HerpAPIError)
        assert is_transient_error(error)
        assert not is_permanent_error(error)

    def test_herp_authentication_error_is_permanent(self):
        """Test HerpAuthenticationError is permanent"""
        error = HerpAuthenticationError("Invalid token")
        assert isinstance(error, PermanentError)
        assert isinstance(error, HerpAPIError)
        assert is_permanent_error(error)
        assert not is_transient_error(error)

    def test_herp_validation_error_is_permanent(self):
        """Test HerpValidationError is permanent"""
        error = HerpValidationError("Invalid input")
        assert isinstance(error, PermanentError)
        assert isinstance(error, HerpAPIError)
        assert is_permanent_error(error)

    def test_herp_not_found_error_is_permanent(self):
        """Test HerpNotFoundError is permanent"""
        error = HerpNotFoundError("Resource not found")
        assert isinstance(error, PermanentError)
        assert isinstance(error, HerpAPIError)
        assert is_permanent_error(error)

    def test_herp_server_error_is_transient(self):
        """Test HerpServerError is transient"""
        error = HerpServerError("Internal server error")
        assert isinstance(error, TransientError)
        assert isinstance(error, HerpAPIError)
        assert is_transient_error(error)

    def test_herp_network_error_is_transient(self):
        """Test HerpNetworkError is transient"""
        error = HerpNetworkError("Connection timeout")
        assert isinstance(error, TransientError)
        assert isinstance(error, HerpAPIError)
        assert is_transient_error(error)


class TestNotionAPIExceptions:
    """Tests for Notion API exceptions"""

    def test_notion_api_error(self):
        """Test NotionAPIError"""
        error = NotionAPIError("Notion API error")
        assert isinstance(error, HerpNotionError)

    def test_notion_rate_limit_error_is_transient(self):
        """Test NotionRateLimitError is transient"""
        error = NotionRateLimitError("Notion rate limit")
        assert isinstance(error, TransientError)
        assert isinstance(error, NotionAPIError)
        assert is_transient_error(error)

    def test_notion_authentication_error_is_permanent(self):
        """Test NotionAuthenticationError is permanent"""
        error = NotionAuthenticationError("Invalid Notion token")
        assert isinstance(error, PermanentError)
        assert isinstance(error, NotionAPIError)
        assert is_permanent_error(error)

    def test_notion_validation_error_is_permanent(self):
        """Test NotionValidationError is permanent"""
        error = NotionValidationError("Invalid page structure")
        assert isinstance(error, PermanentError)
        assert is_permanent_error(error)

    def test_notion_not_found_error_is_permanent(self):
        """Test NotionNotFoundError is permanent"""
        error = NotionNotFoundError("Page not found")
        assert isinstance(error, PermanentError)
        assert is_permanent_error(error)

    def test_notion_server_error_is_transient(self):
        """Test NotionServerError is transient"""
        error = NotionServerError("Notion server down")
        assert isinstance(error, TransientError)
        assert is_transient_error(error)

    def test_notion_network_error_is_transient(self):
        """Test NotionNetworkError is transient"""
        error = NotionNetworkError("Notion connection failed")
        assert isinstance(error, TransientError)
        assert is_transient_error(error)


class TestSyncExceptions:
    """Tests for sync exceptions"""

    def test_sync_error(self):
        """Test SyncError"""
        error = SyncError("Sync failed")
        assert isinstance(error, HerpNotionError)

    def test_sync_validation_error_is_permanent(self):
        """Test SyncValidationError is permanent"""
        error = SyncValidationError("Missing required field")
        assert isinstance(error, PermanentError)
        assert isinstance(error, SyncError)
        assert is_permanent_error(error)

    def test_sync_data_error_is_permanent(self):
        """Test SyncDataError is permanent"""
        error = SyncDataError("Data transformation failed")
        assert isinstance(error, PermanentError)
        assert isinstance(error, SyncError)
        assert is_permanent_error(error)

    def test_sync_timeout_error_is_transient(self):
        """Test SyncTimeoutError is transient"""
        error = SyncTimeoutError("Sync timed out")
        assert isinstance(error, TransientError)
        assert isinstance(error, SyncError)
        assert is_transient_error(error)


class TestCacheExceptions:
    """Tests for cache exceptions"""

    def test_cache_error(self):
        """Test CacheError"""
        error = CacheError("Cache error")
        assert isinstance(error, HerpNotionError)

    def test_cache_full_error_is_transient(self):
        """Test CacheFullError is transient"""
        error = CacheFullError("Cache full")
        assert isinstance(error, TransientError)
        assert isinstance(error, CacheError)
        assert is_transient_error(error)

    def test_cache_serialization_error_is_permanent(self):
        """Test CacheSerializationError is permanent"""
        error = CacheSerializationError("Cannot serialize object")
        assert isinstance(error, PermanentError)
        assert isinstance(error, CacheError)
        assert is_permanent_error(error)


class TestCircuitBreakerExceptions:
    """Tests for circuit breaker exceptions"""

    def test_circuit_breaker_error_is_transient(self):
        """Test CircuitBreakerError is transient"""
        error = CircuitBreakerError("Circuit open")
        assert isinstance(error, TransientError)
        assert is_transient_error(error)


class TestRetryExceptions:
    """Tests for retry exceptions"""

    def test_retry_error(self):
        """Test RetryError"""
        error = RetryError("Retry failed")
        assert isinstance(error, HerpNotionError)

    def test_retry_budget_exceeded_error(self):
        """Test RetryBudgetExceededError"""
        error = RetryBudgetExceededError("Retry budget exceeded")
        assert isinstance(error, RetryError)
        assert isinstance(error, HerpNotionError)


class TestExceptionFromHttpStatus:
    """Tests for exception_from_http_status helper"""

    def test_herp_400_creates_validation_error(self):
        """Test 400 creates HerpValidationError"""
        exc = exception_from_http_status(400, "Bad request", "herp")
        assert isinstance(exc, HerpValidationError)
        assert "400" in str(exc)

    def test_herp_401_creates_authentication_error(self):
        """Test 401 creates HerpAuthenticationError"""
        exc = exception_from_http_status(401, "Unauthorized", "herp")
        assert isinstance(exc, HerpAuthenticationError)
        assert "401" in str(exc)

    def test_herp_403_creates_authentication_error(self):
        """Test 403 creates HerpAuthenticationError"""
        exc = exception_from_http_status(403, "Forbidden", "herp")
        assert isinstance(exc, HerpAuthenticationError)

    def test_herp_404_creates_not_found_error(self):
        """Test 404 creates HerpNotFoundError"""
        exc = exception_from_http_status(404, "Not found", "herp")
        assert isinstance(exc, HerpNotFoundError)

    def test_herp_429_creates_rate_limit_error(self):
        """Test 429 creates HerpRateLimitError"""
        exc = exception_from_http_status(429, "Rate limit", "herp")
        assert isinstance(exc, HerpRateLimitError)
        assert is_transient_error(exc)

    def test_herp_500_creates_server_error(self):
        """Test 500 creates HerpServerError"""
        exc = exception_from_http_status(500, "Server error", "herp")
        assert isinstance(exc, HerpServerError)
        assert is_transient_error(exc)

    def test_herp_502_creates_server_error(self):
        """Test 502 creates HerpServerError"""
        exc = exception_from_http_status(502, "Bad gateway", "herp")
        assert isinstance(exc, HerpServerError)

    def test_herp_503_creates_server_error(self):
        """Test 503 creates HerpServerError"""
        exc = exception_from_http_status(503, "Service unavailable", "herp")
        assert isinstance(exc, HerpServerError)

    def test_herp_504_creates_server_error(self):
        """Test 504 creates HerpServerError"""
        exc = exception_from_http_status(504, "Gateway timeout", "herp")
        assert isinstance(exc, HerpServerError)

    def test_herp_unknown_status_creates_generic_error(self):
        """Test unknown status creates HerpAPIError"""
        exc = exception_from_http_status(418, "I'm a teapot", "herp")
        assert isinstance(exc, HerpAPIError)

    def test_notion_400_creates_validation_error(self):
        """Test Notion 400 creates NotionValidationError"""
        exc = exception_from_http_status(400, "Bad request", "notion")
        assert isinstance(exc, NotionValidationError)

    def test_notion_401_creates_authentication_error(self):
        """Test Notion 401 creates NotionAuthenticationError"""
        exc = exception_from_http_status(401, "Unauthorized", "notion")
        assert isinstance(exc, NotionAuthenticationError)

    def test_notion_429_creates_rate_limit_error(self):
        """Test Notion 429 creates NotionRateLimitError"""
        exc = exception_from_http_status(429, "Rate limit", "notion")
        assert isinstance(exc, NotionRateLimitError)
        assert is_transient_error(exc)

    def test_notion_500_creates_server_error(self):
        """Test Notion 500 creates NotionServerError"""
        exc = exception_from_http_status(500, "Server error", "notion")
        assert isinstance(exc, NotionServerError)
        assert is_transient_error(exc)

    def test_unknown_api_creates_generic_error(self):
        """Test unknown API creates HerpNotionError"""
        exc = exception_from_http_status(400, "Error", "unknown")
        assert isinstance(exc, HerpNotionError)


class TestIsTransientError:
    """Tests for is_transient_error helper"""

    def test_transient_errors_return_true(self):
        """Test transient errors return True"""
        assert is_transient_error(HerpRateLimitError("Rate limit"))
        assert is_transient_error(HerpServerError("Server error"))
        assert is_transient_error(NotionRateLimitError("Notion rate limit"))
        assert is_transient_error(CircuitBreakerError("Circuit open"))

    def test_permanent_errors_return_false(self):
        """Test permanent errors return False"""
        assert not is_transient_error(HerpAuthenticationError("Auth failed"))
        assert not is_transient_error(HerpValidationError("Validation failed"))
        assert not is_transient_error(NotionAuthenticationError("Notion auth failed"))

    def test_non_herp_errors_return_false(self):
        """Test non-HerpNotionError exceptions return False"""
        assert not is_transient_error(ValueError("Value error"))
        assert not is_transient_error(Exception("Generic error"))


class TestIsPermanentError:
    """Tests for is_permanent_error helper"""

    def test_permanent_errors_return_true(self):
        """Test permanent errors return True"""
        assert is_permanent_error(HerpAuthenticationError("Auth failed"))
        assert is_permanent_error(HerpValidationError("Validation failed"))
        assert is_permanent_error(NotionAuthenticationError("Notion auth failed"))
        assert is_permanent_error(SyncValidationError("Sync validation failed"))

    def test_transient_errors_return_false(self):
        """Test transient errors return False"""
        assert not is_permanent_error(HerpRateLimitError("Rate limit"))
        assert not is_permanent_error(HerpServerError("Server error"))
        assert not is_permanent_error(NotionServerError("Notion server error"))

    def test_non_herp_errors_return_false(self):
        """Test non-HerpNotionError exceptions return False"""
        assert not is_permanent_error(ValueError("Value error"))
        assert not is_permanent_error(Exception("Generic error"))
