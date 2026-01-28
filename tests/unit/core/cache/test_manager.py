"""
Tests for cache manager
"""

import time
from unittest.mock import patch

import pytest

from src.core.cache.manager import CacheEntry, CacheManager


class TestCacheManager:
    """Test CacheManager"""

    def test_initialization(self):
        """Test cache manager initialization"""
        manager = CacheManager(default_ttl=300, max_size=100)

        assert manager.default_ttl == 300
        assert manager.max_size == 100
        assert len(manager._cache) == 0

    def test_set_and_get(self):
        """Test setting and getting values"""
        manager = CacheManager()

        # Set a value
        manager.set("key1", "value1")

        # Get the value
        result = manager.get("key1")
        assert result == "value1"

    def test_get_missing_key(self):
        """Test getting a missing key returns None"""
        manager = CacheManager()

        result = manager.get("nonexistent")
        assert result is None

    def test_expiration(self):
        """Test that entries expire after TTL"""
        manager = CacheManager()

        # Set with 1 second TTL
        manager.set("key1", "value1", ttl=1)

        # Should be available immediately
        assert manager.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert manager.get("key1") is None

    def test_custom_ttl(self):
        """Test setting custom TTL"""
        manager = CacheManager(default_ttl=300)

        # Set with custom TTL
        manager.set("key1", "value1", ttl=10)

        # Verify it's stored
        entry = manager._cache.get("key1")
        assert entry is not None

        # TTL should be ~10 seconds
        ttl_remaining = entry.expires_at - time.time()
        assert 9 < ttl_remaining < 11

    def test_delete(self):
        """Test deleting cache entries"""
        manager = CacheManager()

        manager.set("key1", "value1")
        assert manager.get("key1") == "value1"

        manager.delete("key1")
        assert manager.get("key1") is None

    def test_delete_nonexistent(self):
        """Test deleting nonexistent key doesn't raise"""
        manager = CacheManager()

        # Should not raise
        manager.delete("nonexistent")

    def test_clear(self):
        """Test clearing all cache entries"""
        manager = CacheManager()

        # Add multiple entries
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        manager.set("key3", "value3")

        assert manager.size() == 3

        # Clear all
        manager.clear()

        assert manager.size() == 0
        assert manager.get("key1") is None
        assert manager.get("key2") is None

    def test_size(self):
        """Test getting cache size"""
        manager = CacheManager()

        assert manager.size() == 0

        manager.set("key1", "value1")
        assert manager.size() == 1

        manager.set("key2", "value2")
        assert manager.size() == 2

    def test_max_size_eviction(self):
        """Test LRU eviction when max size reached"""
        manager = CacheManager(max_size=3)

        # Fill to capacity
        manager.set("key1", "value1")
        manager.set("key2", "value2")
        manager.set("key3", "value3")

        assert manager.size() == 3

        # Add one more - should evict oldest
        manager.set("key4", "value4")

        # Should still be at max size
        assert manager.size() == 3

        # One of the old keys should be evicted
        assert manager.get("key4") == "value4"

    def test_update_existing_key(self):
        """Test updating an existing key doesn't count against size"""
        manager = CacheManager(max_size=2)

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        # Update existing key (shouldn't trigger eviction)
        manager.set("key1", "value1_updated")

        assert manager.size() == 2
        assert manager.get("key1") == "value1_updated"
        assert manager.get("key2") == "value2"

    def test_get_stats(self):
        """Test getting cache statistics"""
        manager = CacheManager(default_ttl=600, max_size=200)

        manager.set("key1", "value1")
        manager.set("key2", "value2")

        stats = manager.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 200
        assert stats["default_ttl"] == 600

    def test_stats_excludes_expired(self):
        """Test that stats cleanup expired entries"""
        manager = CacheManager()

        # Set entries with short TTL
        manager.set("key1", "value1", ttl=1)
        manager.set("key2", "value2", ttl=1)

        # Before expiration
        assert manager.size() == 2

        # After expiration
        time.sleep(1.1)
        stats = manager.get_stats()

        # Stats should exclude expired entries
        assert stats["size"] == 0

    def test_thread_safety(self):
        """Test thread safety with concurrent access"""
        import threading

        manager = CacheManager()
        errors = []

        def worker(thread_id):
            try:
                for i in range(100):
                    key = f"key_{thread_id}_{i}"
                    manager.set(key, f"value_{i}")
                    result = manager.get(key)
                    assert result == f"value_{i}"
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0

    def test_cache_entry_dataclass(self):
        """Test CacheEntry dataclass"""
        entry = CacheEntry(value="test", expires_at=time.time() + 100)

        assert entry.value == "test"
        assert entry.expires_at > time.time()

    def test_various_value_types(self):
        """Test caching various value types"""
        manager = CacheManager()

        # String
        manager.set("str", "hello")
        assert manager.get("str") == "hello"

        # Integer
        manager.set("int", 42)
        assert manager.get("int") == 42

        # List
        manager.set("list", [1, 2, 3])
        assert manager.get("list") == [1, 2, 3]

        # Dict
        manager.set("dict", {"key": "value"})
        assert manager.get("dict") == {"key": "value"}

        # None (should be cacheable)
        manager.set("none", None)
        assert manager.get("none") is None
