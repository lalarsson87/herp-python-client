"""
Structured logging utilities using structlog

Provides machine-parseable, context-rich logging for better observability.

Usage:
    from src.core.utils.logging import get_logger

    logger = get_logger(__name__)

    # Simple log
    logger.info("candidacy.created")

    # Log with context
    logger.info(
        "candidacy.created",
        candidacy_id="cand_123",
        requisition_id="req_456",
        duration_ms=125.4
    )

    # Bind context for all subsequent logs
    logger = logger.bind(user_id="user_001", session_id="sess_abc")
    logger.info("action.performed")  # Automatically includes user_id and session_id
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog


def configure_structlog(
    log_level: str = "INFO",
    format: str = "json",  # "json" or "console"
    enable_colors: bool = True,
) -> None:
    """
    Configure structlog with sensible defaults

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format ("json" for production, "console" for development)
        enable_colors: Enable colored output (only for console format)
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if format == "console":
        # Development-friendly console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=enable_colors)
        ]
    else:
        # Production JSON output
        processors = shared_processors + [structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def get_logger(
    name: str,
    **initial_context: Any,
) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__)
        **initial_context: Initial context to bind to all log messages

    Returns:
        Configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__, service="herp-client", version="0.3.0")
        >>> logger.info(
        ...     "api.request",
        ...     method="POST",
        ...     endpoint="/v1/candidacies",
        ...     duration_ms=123.4
        ... )
    """
    logger = structlog.get_logger(name)

    if initial_context:
        logger = logger.bind(**initial_context)

    return logger


def get_request_logger(
    name: str,
    request_id: Optional[str] = None,
    **context: Any,
) -> structlog.stdlib.BoundLogger:
    """
    Get a logger with request-specific context

    Automatically includes request_id and other request metadata.

    Args:
        name: Logger name
        request_id: Unique request identifier
        **context: Additional context (user_id, tenant_id, etc.)

    Returns:
        Logger with request context bound

    Example:
        >>> logger = get_request_logger(
        ...     __name__,
        ...     request_id="req_abc123",
        ...     user_id="user_001"
        ... )
        >>> logger.info("request.started", method="GET", path="/v1/candidacies")
    """
    logger = get_logger(name)

    if request_id:
        logger = logger.bind(request_id=request_id)

    if context:
        logger = logger.bind(**context)

    return logger


# Auto-configure on import with sensible defaults
# Can be reconfigured by calling configure_structlog()
try:
    # Check if running in production (JSON logs) or development (console logs)
    import os

    log_format = os.getenv("LOG_FORMAT", "console")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    enable_colors = os.getenv("LOG_COLORS", "true").lower() in ("true", "1", "yes")

    configure_structlog(
        log_level=log_level,
        format=log_format,
        enable_colors=enable_colors,
    )
except Exception:
    # Fallback to basic configuration if anything goes wrong
    configure_structlog()


# Convenience function for backward compatibility
def get_legacy_logger(name: str) -> logging.Logger:
    """
    Get a standard library logger (for backward compatibility)

    This is provided for gradual migration from logging to structlog.
    New code should use get_logger() instead.

    Args:
        name: Logger name

    Returns:
        Standard library logger instance
    """
    return logging.getLogger(name)
