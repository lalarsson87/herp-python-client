"""
Unit tests for CacheManager

Tests caching functionality including TTL, eviction, and thread safety.
"""

import time
import unittest
from unittest.mock import patch

from src.core.cache import CacheManager


class TestCacheManager(unittest.TestCase):
    """Test cases for CacheManager"""

    def setUp(self):
        """Set up test cache manager"""
        self.cache = CacheManager(default_ttl=60, max_size=10)

    def tearDown(self):
        """Clean up after each test"""
        self.cache.clear()

    def test_initialization(self):
        """Test CacheManager initialization"""
        cache = CacheManager(default_ttl=120, max_size=50)
        assert cache.default_ttl == 120
        assert cache.max_size == 50
        assert cache.size() == 0

    def test_set_and_get(self):
        """Test basic set and get operations"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None"""
        assert self.cache.get("nonexistent") is None

    def test_set_with_custom_ttl(self):
        """Test setting value with custom TTL"""
        self.cache.set("key1", "value1", ttl=120)
        assert self.cache.get("key1") == "value1"

    def test_expiration(self):
        """Test cache entry expiration"""
        # Set with very short TTL
        self.cache.set("key1", "value1", ttl=1)
        assert self.cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)
        assert self.cache.get("key1") is None

    def test_delete(self):
        """Test deleting cache entry"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_delete_nonexistent_key(self):
        """Test deleting non-existent key doesn't raise error"""
        self.cache.delete("nonexistent")  # Should not raise

    def test_clear(self):
        """Test clearing all cache entries"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        assert self.cache.size() == 3

        self.cache.clear()
        assert self.cache.size() == 0

    def test_size(self):
        """Test cache size tracking"""
        assert self.cache.size() == 0

        self.cache.set("key1", "value1")
        assert self.cache.size() == 1

        self.cache.set("key2", "value2")
        assert self.cache.size() == 2

        self.cache.delete("key1")
        assert self.cache.size() == 1

    def test_max_size_eviction(self):
        """Test LRU eviction when max size is reached"""
        # Create cache with small max size
        small_cache = CacheManager(default_ttl=60, max_size=3)

        # Fill cache to max
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        small_cache.set("key3", "value3")
        assert small_cache.size() == 3

        # Add one more - should evict oldest
        small_cache.set("key4", "value4")
        assert small_cache.size() == 3

        # key1 should have been evicted
        assert small_cache.get("key1") is None
        assert small_cache.get("key4") == "value4"

    def test_overwrite_existing_key(self):
        """Test overwriting an existing cache key"""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

        self.cache.set("key1", "value2")
        assert self.cache.get("key1") == "value2"

    def test_different_data_types(self):
        """Test caching different data types"""
        # String
        self.cache.set("str", "text")
        assert self.cache.get("str") == "text"

        # Integer
        self.cache.set("int", 42)
        assert self.cache.get("int") == 42

        # List
        self.cache.set("list", [1, 2, 3])
        assert self.cache.get("list") == [1, 2, 3]

        # Dict
        self.cache.set("dict", {"key": "value"})
        assert self.cache.get("dict") == {"key": "value"}

        # None
        self.cache.set("none", None)
        # Note: Cached None is different from cache miss (both return None)
        # This is a known limitation

    def test_cleanup_expired(self):
        """Test automatic cleanup of expired entries"""
        # Set entries with short TTL
        self.cache.set("key1", "value1", ttl=1)
        self.cache.set("key2", "value2", ttl=1)
        self.cache.set("key3", "value3", ttl=100)  # Won't expire

        assert self.cache.size() == 3

        # Wait for expiration
        time.sleep(1.1)

        # Accessing size should trigger cleanup
        size = self.cache.size()
        assert size == 1
        assert self.cache.get("key3") == "value3"

    def test_get_stats(self):
        """Test cache statistics"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")

        stats = self.cache.get_stats()
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["default_ttl"] == 60

    def test_get_stats_excludes_expired(self):
        """Test stats exclude expired entries"""
        # Add entries with short TTL
        self.cache.set("key1", "value1", ttl=1)
        self.cache.set("key2", "value2", ttl=100)

        assert self.cache.get_stats()["size"] == 2

        # Wait for first entry to expire
        time.sleep(1.1)

        stats = self.cache.get_stats()
        assert stats["size"] == 1

    def test_thread_safety_basic(self):
        """Test basic thread safety of cache operations"""
        import threading

        def set_values(start, end):
            for i in range(start, end):
                self.cache.set(f"key{i}", f"value{i}")

        def get_values(start, end):
            for i in range(start, end):
                self.cache.get(f"key{i}")

        # Create threads
        threads = [
            threading.Thread(target=set_values, args=(0, 50)),
            threading.Thread(target=set_values, args=(50, 100)),
            threading.Thread(target=get_values, args=(0, 100)),
        ]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should not crash and cache should be consistent
        assert self.cache.size() <= 100


class TestCacheEntry(unittest.TestCase):
    """Test cases for CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test creating CacheEntry"""
        from src.core.cache.manager import CacheEntry

        entry = CacheEntry(value="test", expires_at=1234567890.0)
        assert entry.value == "test"
        assert entry.expires_at == 1234567890.0

    def test_cache_entry_with_complex_value(self):
        """Test CacheEntry with complex value types"""
        from src.core.cache.manager import CacheEntry

        complex_value = {"nested": {"data": [1, 2, 3]}}
        entry = CacheEntry(value=complex_value, expires_at=time.time() + 60)
        assert entry.value == complex_value
        assert entry.value["nested"]["data"] == [1, 2, 3]


if __name__ == "__main__":
    unittest.main()
