"""
Tests for cache decorators
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.core.cache.decorators import (
    cached_response,
    async_cached_response,
    invalidate_cache,
    _generate_cache_key,
)
from src.core.cache.manager import CacheManager


@pytest.fixture
def cache_manager():
    """Create test cache manager"""
    return CacheManager(max_size=100, default_ttl=60)


class TestCacheKeyGeneration:
    """Test cache key generation"""

    def test_simple_key(self):
        """Test simple cache key generation"""
        key = _generate_cache_key("test_func", (), {})
        assert "test_func" in key

    def test_key_with_args(self):
        """Test cache key with arguments"""
        key = _generate_cache_key("test_func", ("arg1", "arg2"), {})
        assert "test_func" in key
        assert "arg1" in key
        assert "arg2" in key

    def test_key_with_kwargs(self):
        """Test cache key with keyword arguments"""
        key = _generate_cache_key("test_func", (), {"key1": "value1"})
        assert "test_func" in key
        assert "key1" in key

    def test_key_consistency(self):
        """Test that same inputs produce same key"""
        key1 = _generate_cache_key("func", ("a",), {"b": 1})
        key2 = _generate_cache_key("func", ("a",), {"b": 1})
        assert key1 == key2

    def test_long_key_hashing(self):
        """Test that long keys are hashed"""
        long_value = "x" * 500
        key = _generate_cache_key("func", (long_value,), {})
        # Should be hashed to shorter length
        assert len(key) < 250


class TestCachedResponse:
    """Test cached_response decorator"""

    def test_cache_hit(self, cache_manager):
        """Test cache hit"""
        call_count = 0

        class TestClass:
            cache_manager = cache_manager

            @cached_response(ttl=60)
            def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id, "data": "test"}

        obj = TestClass()

        # First call - cache miss
        result1 = obj.get_data("123")
        assert result1 == {"id": "123", "data": "test"}
        assert call_count == 1

        # Second call - cache hit
        result2 = obj.get_data("123")
        assert result2 == {"id": "123", "data": "test"}
        assert call_count == 1  # Function not called again

    def test_cache_miss_different_args(self, cache_manager):
        """Test cache miss with different arguments"""
        call_count = 0

        class TestClass:
            cache_manager = cache_manager

            @cached_response(ttl=60)
            def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id}

        obj = TestClass()

        obj.get_data("123")
        obj.get_data("456")  # Different arg - cache miss

        assert call_count == 2

    def test_cache_expiration(self, cache_manager):
        """Test cache expiration"""
        call_count = 0

        class TestClass:
            cache_manager = cache_manager

            @cached_response(ttl=1)  # 1 second TTL
            def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id}

        obj = TestClass()

        obj.get_data("123")
        assert call_count == 1

        # Wait for expiration
        time.sleep(1.1)

        obj.get_data("123")
        assert call_count == 2  # Cache expired, function called again

    def test_no_cache_manager(self):
        """Test decorator without cache manager"""
        call_count = 0

        class TestClass:
            @cached_response(ttl=60)
            def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id}

        obj = TestClass()

        obj.get_data("123")
        obj.get_data("123")

        # Without cache manager, function called twice
        assert call_count == 2

    def test_none_result_not_cached(self, cache_manager):
        """Test that None results are not cached"""
        call_count = 0

        class TestClass:
            cache_manager = cache_manager

            @cached_response(ttl=60)
            def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return None

        obj = TestClass()

        obj.get_data("123")
        obj.get_data("123")

        # None not cached, function called twice
        assert call_count == 2


class TestInvalidateCache:
    """Test cache invalidation decorator"""

    def test_invalidate_all(self, cache_manager):
        """Test invalidating all cache"""

        class TestClass:
            cache_manager = cache_manager

            @cached_response(ttl=60)
            def get_data(self, id):
                return {"id": id}

            @invalidate_cache()
            def update_data(self, id, data):
                return {"id": id, "updated": True}

        obj = TestClass()

        # Cache some data
        obj.get_data("123")
        assert cache_manager.size() == 1

        # Invalidate cache
        obj.update_data("123", {"new": "data"})

        # Cache should be cleared
        assert cache_manager.size() == 0

    def test_no_cache_manager(self):
        """Test invalidate decorator without cache manager"""

        class TestClass:
            @invalidate_cache()
            def update_data(self, id):
                return {"id": id}

        obj = TestClass()

        # Should not raise error
        result = obj.update_data("123")
        assert result == {"id": "123"}


@pytest.mark.asyncio
class TestAsyncCachedResponse:
    """Test async_cached_response decorator"""

    async def test_async_cache_hit(self, cache_manager):
        """Test async cache hit"""
        call_count = 0

        class TestClass:
            cache_manager = cache_manager

            @async_cached_response(ttl=60)
            async def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id, "data": "test"}

        obj = TestClass()

        # First call - cache miss
        result1 = await obj.get_data("123")
        assert result1 == {"id": "123", "data": "test"}
        assert call_count == 1

        # Second call - cache hit
        result2 = await obj.get_data("123")
        assert result2 == {"id": "123", "data": "test"}
        assert call_count == 1  # Function not called again

    async def test_async_no_cache_manager(self):
        """Test async decorator without cache manager"""
        call_count = 0

        class TestClass:
            @async_cached_response(ttl=60)
            async def get_data(self, id):
                nonlocal call_count
                call_count += 1
                return {"id": id}

        obj = TestClass()

        await obj.get_data("123")
        await obj.get_data("123")

        # Without cache manager, function called twice
        assert call_count == 2
