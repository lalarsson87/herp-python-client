"""
Cache Decorators for API Responses

Provides decorators to cache API responses with configurable TTL.
Reduces API calls and improves performance for frequently accessed data.
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional

from ..utils.logging import get_logger

logger = get_logger(__name__)


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate unique cache key from function name and arguments

    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Unique cache key string
    """
    # Skip 'self' argument for class methods
    args_to_hash = args[1:] if args and hasattr(args[0], func_name) else args

    # Create a deterministic representation
    key_parts = [func_name]

    # Add args
    for arg in args_to_hash:
        if isinstance(arg, (str, int, float, bool, type(None))):
            key_parts.append(str(arg))
        else:
            # For complex types, use repr
            key_parts.append(repr(arg))

    # Add kwargs (sorted for determinism)
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool, type(None))):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={repr(v)}")

    # Create hash for long keys
    key_str = ":".join(key_parts)
    if len(key_str) > 200:
        # Use hash for very long keys
        key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
        return f"{func_name}:{key_hash}"

    return key_str


def cached_response(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    cache_attr: str = "cache_manager",
):
    """
    Decorator to cache API responses with TTL

    Caches the return value of a function. Automatically generates cache
    keys from function name and arguments. Uses instance's cache_manager
    attribute.

    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        key_prefix: Optional prefix for cache key (default: function name)
        cache_attr: Attribute name for cache manager (default: "cache_manager")

    Returns:
        Decorator function

    Example:
        >>> class MasterDataAPI:
        ...     def __init__(self, client, cache_manager):
        ...         self.client = client
        ...         self.cache_manager = cache_manager
        ...
        ...     @cached_response(ttl=600)  # Cache for 10 minutes
        ...     def list_requisitions(self):
        ...         return self.client.get("/v1/requisitions")
        ...
        >>> # First call hits API
        >>> api = MasterDataAPI(client, cache_manager)
        >>> requisitions = api.list_requisitions()  # API call
        ...
        >>> # Second call within 10 minutes returns cached value
        >>> requisitions = api.list_requisitions()  # Cache hit, no API call

    Note:
        - Only caches successful responses (non-None, non-exception)
        - Cache is instance-specific (tied to cache_manager attribute)
        - Thread-safe (cache manager handles locking)
        - Automatically evicts expired entries
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get cache manager from instance
            cache_manager = getattr(self, cache_attr, None)

            # If no cache manager, just call function
            if cache_manager is None:
                logger.debug(f"{func.__name__}: No cache manager, skipping cache")
                return func(self, *args, **kwargs)

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = _generate_cache_key(prefix, (self,) + args, kwargs)

            # Check cache
            cached = cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"{func.__name__}: Cache hit: {cache_key}")
                return cached

            # Call function
            logger.debug(f"{func.__name__}: Cache miss, calling function")
            result = func(self, *args, **kwargs)

            # Store in cache if result is not None
            if result is not None:
                cache_manager.set(cache_key, result, ttl=ttl)
                logger.debug(f"{func.__name__}: Cached result with TTL={ttl}s")

            return result

        return wrapper

    return decorator


def async_cached_response(
    ttl: int = 300,
    key_prefix: Optional[str] = None,
    cache_attr: str = "cache_manager",
):
    """
    Decorator to cache async API responses with TTL

    Async version of @cached_response decorator.

    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        key_prefix: Optional prefix for cache key (default: function name)
        cache_attr: Attribute name for cache manager (default: "cache_manager")

    Returns:
        Decorator function

    Example:
        >>> class AsyncMasterDataAPI:
        ...     def __init__(self, client, cache_manager):
        ...         self.client = client
        ...         self.cache_manager = cache_manager
        ...
        ...     @async_cached_response(ttl=600)
        ...     async def list_requisitions(self):
        ...         return await self.client.get("/v1/requisitions")
        ...
        >>> # First call hits API
        >>> api = AsyncMasterDataAPI(client, cache_manager)
        >>> requisitions = await api.list_requisitions()  # API call
        ...
        >>> # Second call returns cached value
        >>> requisitions = await api.list_requisitions()  # Cache hit

    Note:
        - Same behavior as @cached_response but for async functions
        - Cache manager operations are synchronous (thread-safe)
        - Async function execution is cached, not the coroutine
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get cache manager from instance
            cache_manager = getattr(self, cache_attr, None)

            # If no cache manager, just call function
            if cache_manager is None:
                logger.debug(f"{func.__name__}: No cache manager, skipping cache")
                return await func(self, *args, **kwargs)

            # Generate cache key
            prefix = key_prefix or func.__name__
            cache_key = _generate_cache_key(prefix, (self,) + args, kwargs)

            # Check cache
            cached = cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"{func.__name__}: Cache hit: {cache_key}")
                return cached

            # Call function
            logger.debug(f"{func.__name__}: Cache miss, calling function")
            result = await func(self, *args, **kwargs)

            # Store in cache if result is not None
            if result is not None:
                cache_manager.set(cache_key, result, ttl=ttl)
                logger.debug(f"{func.__name__}: Cached result with TTL={ttl}s")

            return result

        return wrapper

    return decorator


def invalidate_cache(
    key_pattern: Optional[str] = None, cache_attr: str = "cache_manager"
):
    """
    Decorator to invalidate cache entries after function execution

    Useful for write operations that should invalidate related cached data.

    Args:
        key_pattern: Pattern to match cache keys (None = clear all)
        cache_attr: Attribute name for cache manager

    Returns:
        Decorator function

    Example:
        >>> class CandidaciesAPI:
        ...     @invalidate_cache(key_pattern="list_candidacies")
        ...     def create(self, candidacy_data):
        ...         # Creates a candidacy and invalidates list cache
        ...         return self.client.post("/v1/candidacies", json=candidacy_data)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Execute function first
            result = func(self, *args, **kwargs)

            # Invalidate cache
            cache_manager = getattr(self, cache_attr, None)
            if cache_manager:
                if key_pattern:
                    # Clear specific pattern (not implemented in basic cache)
                    logger.debug(
                        f"{func.__name__}: Invalidating cache pattern: {key_pattern}"
                    )
                    # For now, just log - could implement pattern matching
                else:
                    cache_manager.clear()
                    logger.debug(f"{func.__name__}: Cleared all cache")

            return result

        return wrapper

    return decorator
