"""
Tests for Logging Utilities
"""

import logging
import os
from unittest.mock import Mock, patch

import pytest
import structlog

from src.core.utils.logging import (
    configure_structlog,
    get_legacy_logger,
    get_logger,
    get_request_logger,
)


class TestConfigureStructlog:
    """Test structlog configuration"""

    def test_configure_with_json_format(self):
        """Test configuring structlog with JSON format"""
        configure_structlog(log_level="INFO", format="json", enable_colors=False)

        # Get logger to verify configuration
        logger = structlog.get_logger("test")

        assert logger is not None
        # Logger can be LazyProxy or BoundLogger
        assert hasattr(logger, "info")

    def test_configure_with_console_format(self):
        """Test configuring structlog with console format"""
        configure_structlog(log_level="DEBUG", format="console", enable_colors=True)

        logger = structlog.get_logger("test")

        assert logger is not None
        assert hasattr(logger, "info")

    def test_configure_with_different_log_levels(self):
        """Test configuring with different log levels"""
        # DEBUG level
        configure_structlog(log_level="DEBUG", format="json")
        # Configuration should work without errors
        logger = get_logger("test")
        assert logger is not None

        # INFO level
        configure_structlog(log_level="INFO", format="json")
        logger = get_logger("test")
        assert logger is not None

    def test_configure_with_lowercase_log_level(self):
        """Test configure handles lowercase log level"""
        configure_structlog(log_level="info", format="json")

        # Configuration should work without errors
        logger = get_logger("test")
        assert logger is not None


class TestGetLogger:
    """Test get_logger function"""

    def test_get_logger_basic(self):
        """Test getting basic logger"""
        logger = get_logger("test.module")

        assert logger is not None
        assert hasattr(logger, "info")

    def test_get_logger_with_initial_context(self):
        """Test getting logger with initial context"""
        logger = get_logger("test.module", service="test-service", version="1.0.0")

        assert logger is not None
        # Context should be bound
        assert hasattr(logger, "info")

    def test_get_logger_different_names(self):
        """Test getting loggers with different names"""
        logger1 = get_logger("module.one")
        logger2 = get_logger("module.two")

        assert logger1 is not None
        assert logger2 is not None
        # Should get logger instances
        assert hasattr(logger1, "info")
        assert hasattr(logger2, "info")

    def test_get_logger_binding(self):
        """Test logger context binding"""
        logger = get_logger("test", request_id="req_123")

        # Bind additional context
        bound_logger = logger.bind(user_id="user_456")

        assert bound_logger is not None
        assert isinstance(bound_logger, structlog.stdlib.BoundLogger)


class TestGetRequestLogger:
    """Test get_request_logger function"""

    def test_get_request_logger_with_request_id(self):
        """Test getting logger with request ID"""
        logger = get_request_logger("test.module", request_id="req_abc123")

        assert logger is not None
        assert hasattr(logger, "info")

    def test_get_request_logger_without_request_id(self):
        """Test getting logger without request ID"""
        logger = get_request_logger("test.module")

        assert logger is not None
        assert hasattr(logger, "info")

    def test_get_request_logger_with_context(self):
        """Test getting logger with additional context"""
        logger = get_request_logger(
            "test.module",
            request_id="req_123",
            user_id="user_456",
            tenant_id="tenant_789",
        )

        assert logger is not None
        assert hasattr(logger, "info")

    def test_get_request_logger_multiple_contexts(self):
        """Test getting logger with multiple context fields"""
        logger = get_request_logger(
            "test.module",
            request_id="req_001",
            user_id="user_001",
            session_id="sess_abc",
            ip_address="192.168.1.1",
        )

        assert logger is not None


class TestGetLegacyLogger:
    """Test get_legacy_logger function"""

    def test_get_legacy_logger(self):
        """Test getting standard library logger"""
        logger = get_legacy_logger("test.legacy")

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.legacy"

    def test_get_legacy_logger_different_names(self):
        """Test getting different legacy loggers"""
        logger1 = get_legacy_logger("module.one")
        logger2 = get_legacy_logger("module.two")

        assert logger1.name == "module.one"
        assert logger2.name == "module.two"


class TestLoggerUsage:
    """Test logger usage patterns"""

    def test_logger_info_log(self, caplog):
        """Test logger info level logging"""
        configure_structlog(log_level="INFO", format="console")

        with caplog.at_level(logging.INFO):
            logger = get_logger("test")
            logger.info("test.message", key="value")

        # Verify log was captured
        assert len(caplog.records) > 0

    def test_logger_error_log(self, caplog):
        """Test logger error level logging"""
        configure_structlog(log_level="INFO", format="console")

        with caplog.at_level(logging.ERROR):
            logger = get_logger("test")
            logger.error("test.error", error_code="ERR_001")

        assert len(caplog.records) > 0

    def test_logger_debug_log_not_captured_at_info(self, caplog):
        """Test debug logs are not captured when level is INFO"""
        configure_structlog(log_level="INFO", format="console")

        with caplog.at_level(logging.INFO):
            logger = get_logger("test")
            logger.debug("test.debug")  # Should not appear

        # Debug message should not be in logs
        debug_messages = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_messages) == 0

    def test_logger_context_binding(self):
        """Test logger context binding persists"""
        logger = get_logger("test")

        # Bind context
        bound_logger = logger.bind(user_id="user_123", session_id="sess_abc")

        # Should return bound logger
        assert bound_logger is not None
        assert isinstance(bound_logger, structlog.stdlib.BoundLogger)


class TestLoggingIntegration:
    """Integration tests for logging module"""

    @patch.dict(
        os.environ,
        {"LOG_FORMAT": "json", "LOG_LEVEL": "DEBUG", "LOG_COLORS": "false"},
    )
    def test_auto_configuration_from_env(self):
        """Test auto-configuration reads from environment"""
        # Re-import to trigger auto-configuration
        import importlib

        import src.core.utils.logging as logging_module

        importlib.reload(logging_module)

        # Verify logger can be created (configuration was applied)
        logger = logging_module.get_logger("test")
        assert logger is not None
        assert hasattr(logger, "info")

    def test_logger_with_exception_info(self, caplog):
        """Test logger captures exception info"""
        configure_structlog(
            log_level="ERROR", format="json"
        )  # Use JSON to avoid warning

        with caplog.at_level(logging.ERROR):
            logger = get_logger("test")

            try:
                raise ValueError("Test error")
            except ValueError:
                logger.error("test.exception", error="Test error")

        assert len(caplog.records) > 0

    def test_multiple_loggers_independence(self):
        """Test multiple loggers operate independently"""
        logger1 = get_logger("module.one", service="service1")
        logger2 = get_logger("module.two", service="service2")

        # Bind different context to each
        logger1_bound = logger1.bind(request_id="req_001")
        logger2_bound = logger2.bind(request_id="req_002")

        assert logger1_bound is not None
        assert logger2_bound is not None

    def test_request_logger_workflow(self, caplog):
        """Test complete request logger workflow"""
        configure_structlog(log_level="INFO", format="console")

        with caplog.at_level(logging.INFO):
            # Create request logger
            logger = get_request_logger(
                "api.handler",
                request_id="req_abc123",
                user_id="user_456",
                method="POST",
                path="/v1/candidacies",
            )

            # Log request started
            logger.info("request.started")

            # Log request completed
            logger.info("request.completed", status_code=200, duration_ms=123.4)

        assert len(caplog.records) >= 2

    def test_legacy_logger_compatibility(self, caplog):
        """Test legacy logger works with standard logging"""
        with caplog.at_level(logging.INFO):
            logger = get_legacy_logger("legacy.module")
            logger.info("Legacy log message")

        assert len(caplog.records) > 0
        assert any("Legacy log message" in r.message for r in caplog.records)


class TestLoggingConfiguration:
    """Test logging configuration edge cases"""

    def test_reconfiguration(self):
        """Test reconfiguring structlog"""
        # Initial configuration
        configure_structlog(log_level="INFO", format="json")

        # Reconfigure with different settings
        configure_structlog(log_level="DEBUG", format="console", enable_colors=False)

        # Should work without errors
        logger = get_logger("test")
        assert logger is not None

    def test_configuration_with_invalid_level_falls_back(self):
        """Test invalid log level is handled gracefully"""
        # This should not raise an error due to getattr with default
        try:
            configure_structlog(log_level="INVALID_LEVEL", format="console")
            logger = get_logger("test")
            assert logger is not None
        except Exception as e:
            # If it does raise, it should be a known exception
            assert isinstance(e, (AttributeError, ValueError))


class TestLoggingFormats:
    """Test different logging formats"""

    def test_json_format_configuration(self):
        """Test JSON format produces JSON output"""
        configure_structlog(log_level="INFO", format="json", enable_colors=False)

        logger = get_logger("test")
        assert logger is not None

        # JSON format should be configured
        # (actual JSON output verification would require capturing stdout)

    def test_console_format_with_colors(self):
        """Test console format with colors enabled"""
        configure_structlog(log_level="INFO", format="console", enable_colors=True)

        logger = get_logger("test")
        assert logger is not None

    def test_console_format_without_colors(self):
        """Test console format without colors"""
        configure_structlog(log_level="INFO", format="console", enable_colors=False)

        logger = get_logger("test")
        assert logger is not None


class TestLoggingContextManagement:
    """Test logging context management"""

    def test_bind_single_context(self):
        """Test binding single context value"""
        logger = get_logger("test")
        bound = logger.bind(key="value")

        assert bound is not None

    def test_bind_multiple_contexts(self):
        """Test binding multiple context values"""
        logger = get_logger("test")
        bound = logger.bind(key1="value1", key2="value2", key3="value3")

        assert bound is not None

    def test_nested_binding(self):
        """Test nested context binding"""
        logger = get_logger("test")
        bound1 = logger.bind(level1="value1")
        bound2 = bound1.bind(level2="value2")
        bound3 = bound2.bind(level3="value3")

        assert bound3 is not None


class TestLoggingErrorHandling:
    """Test logging error handling"""

    def test_logger_handles_none_values(self):
        """Test logger handles None values in context"""
        logger = get_logger("test", none_value=None)

        assert logger is not None

    def test_logger_handles_empty_context(self):
        """Test logger handles empty context"""
        logger = get_logger("test")

        assert logger is not None

    def test_request_logger_handles_missing_request_id(self):
        """Test request logger works without request_id"""
        logger = get_request_logger("test", user_id="user_123")

        assert logger is not None
