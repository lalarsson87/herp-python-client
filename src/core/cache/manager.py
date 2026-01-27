"""
Cache Manager Implementation

Provides in-memory caching with TTL support for API responses and master data.
"""

import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from threading import Lock

from ..constants import CACHE_DEFAULT_TTL, CACHE_MAX_SIZE
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time"""

    value: Any
    expires_at: float


class CacheManager:
    """
    In-memory cache manager with TTL support

    Provides thread-safe caching with automatic expiration.
    Implements LRU eviction when cache size limit is reached.
    """

    def __init__(
        self, default_ttl: int = CACHE_DEFAULT_TTL, max_size: int = CACHE_MAX_SIZE
    ):
        """
        Initialize cache manager

        Args:
            default_ttl: Default time-to-live in seconds
            max_size: Maximum number of cache entries
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        logger.info(
            f"CacheManager initialized with TTL={default_ttl}s, max_size={max_size}"
        )

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                logger.debug(f"Cache miss: {key}")
                return None

            # Check if expired
            if time.time() > entry.expires_at:
                logger.debug(f"Cache expired: {key}")
                del self._cache[key]
                return None

            logger.debug(f"Cache hit: {key}")
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        with self._lock:
            # Evict oldest entry if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()

            ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + ttl

            self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
            logger.debug(f"Cache set: {key} (TTL={ttl}s)")

    def delete(self, key: str) -> None:
        """
        Delete value from cache

        Args:
            key: Cache key
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")

    def size(self) -> int:
        """
        Get current cache size

        Returns:
            Number of entries in cache
        """
        with self._lock:
            # Remove expired entries first
            self._cleanup_expired()
            return len(self._cache)

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry (LRU eviction)"""
        if not self._cache:
            return

        # Find entry with earliest expiration time
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].expires_at)
        del self._cache[oldest_key]
        logger.debug(f"Cache evicted (LRU): {oldest_key}")

    def _cleanup_expired(self) -> None:
        """Remove all expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() if current_time > entry.expires_at
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats (size, max_size, default_ttl)
        """
        with self._lock:
            self._cleanup_expired()
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
            }
