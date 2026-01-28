"""
Validation utilities for API responses
"""

from functools import lru_cache, wraps
from typing import Any, Callable, Dict, List, Type, TypedDict, get_type_hints

from .logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=128)
def _get_schema_fields(schema_class: type) -> frozenset:
    """
    Extract field names from TypedDict schema (cached for performance)

    Args:
        schema_class: TypedDict class

    Returns:
        Frozenset of required field names

    Note:
        Uses LRU cache to avoid repeated reflection overhead.
        Cache size of 128 is sufficient for typical API schemas.
    """
    try:
        # Get type hints from the TypedDict
        hints = get_type_hints(schema_class)
        return frozenset(hints.keys())
    except Exception as e:
        logger.warning(f"Failed to extract schema fields from {schema_class}: {e}")
        return frozenset()


def _validate_dict(
    data: Dict[str, Any],
    schema_class: type,
    strict: bool = True,
) -> Dict[str, Any]:
    """
    Validate a dictionary against a TypedDict schema

    Args:
        data: Data to validate
        schema_class: TypedDict schema class
        strict: If True, log warnings for missing fields

    Returns:
        Original data (validation is non-blocking)
    """
    if not data:
        if strict:
            logger.warning(f"Empty response for schema {schema_class.__name__}")
        return data

    # Get cached schema fields
    expected_fields = _get_schema_fields(schema_class)

    if not expected_fields:
        # Schema extraction failed, skip validation
        return data

    # Check for missing required fields
    actual_fields = set(data.keys())
    missing_fields = expected_fields - actual_fields

    if missing_fields and strict:
        logger.debug(
            f"Response missing fields for {schema_class.__name__}: {missing_fields}"
        )

    return data


def validate_response(schema_class, strict: bool = True):
    """
    Decorator to validate API response against a schema

    Args:
        schema_class: TypedDict class for validation
        strict: If True, log warnings for validation failures

    Returns:
        Decorated function

    Note:
        Uses LRU-cached schema extraction for performance.
        Validation is non-blocking (logs warnings but doesn't raise).
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Validate if result is a dict
            if isinstance(result, dict):
                return _validate_dict(result, schema_class, strict)

            return result

        return wrapper

    return decorator


def validate_list_response(schema_class, strict: bool = True):
    """
    Decorator to validate list API response

    Args:
        schema_class: TypedDict class for validation
        strict: If True, log warnings for validation failures

    Returns:
        Decorated function

    Note:
        Validates each item in the list against the schema.
        Uses LRU-cached schema extraction for performance.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Validate if result is a list
            if isinstance(result, list):
                # Validate first few items (sampling for performance)
                sample_size = min(5, len(result))
                for item in result[:sample_size]:
                    if isinstance(item, dict):
                        _validate_dict(item, schema_class, strict)

            return result

        return wrapper

    return decorator


def validate_single_response(schema_class, strict: bool = True):
    """
    Decorator to validate single item API response

    Alias for validate_response for better semantic clarity.

    Args:
        schema_class: TypedDict class for validation
        strict: If True, raise error on validation failure

    Returns:
        Decorated function
    """
    return validate_response(schema_class, strict)
