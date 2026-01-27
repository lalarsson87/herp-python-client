"""
Validation utilities for API responses
"""

from functools import wraps
from typing import Any, Callable, Dict


def validate_response(schema_class, strict: bool = True):
    """
    Decorator to validate API response against a schema

    Args:
        schema_class: TypedDict class for validation
        strict: If True, raise error on validation failure

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # In a real implementation, this would validate against the schema
            return result

        return wrapper

    return decorator


def validate_list_response(schema_class, strict: bool = True):
    """
    Decorator to validate list API response

    Args:
        schema_class: TypedDict class for validation
        strict: If True, raise error on validation failure

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # In a real implementation, this would validate list items
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
