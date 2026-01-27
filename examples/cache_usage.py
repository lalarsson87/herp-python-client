#!/usr/bin/env python3
"""
Cache Usage Examples

Demonstrates how to use the CacheManager for various scenarios:
1. Manual caching
2. Function decorator caching
3. Cache statistics
4. Namespace management
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.cache import CacheManager, CacheConfig, get_global_cache
from src.core.herp.client import HerpClient
from src.core.utils.config import HerpConfig


# ============================================================================
# Example 1: Basic Manual Caching
# ============================================================================

def example_manual_caching():
    """Demonstrate basic cache operations"""
    print("\n" + "="*60)
    print("Example 1: Manual Caching")
    print("="*60)

    # Create cache with custom config
    cache = CacheManager(CacheConfig(
        max_size=100,
        default_ttl=3600,  # 1 hour
        enabled=True
    ))

    # Set values
    cache.set("user:123", {"name": "John", "email": "john@example.com"})
    cache.set("user:456", {"name": "Jane", "email": "jane@example.com"}, ttl=600)  # 10 min

    # Get values
    user1 = cache.get("user:123")
    user2 = cache.get("user:456")

    print(f"User 1: {user1}")
    print(f"User 2: {user2}")

    # Cache miss
    user3 = cache.get("user:789")
    print(f"User 3 (miss): {user3}")

    # Get stats
    stats = cache.get_stats()
    print(f"\nCache Stats:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate:.1f}%")


# ============================================================================
# Example 2: Decorator-based Caching
# ============================================================================

def example_decorator_caching():
    """Demonstrate function decorator caching"""
    print("\n" + "="*60)
    print("Example 2: Decorator Caching")
    print("="*60)

    cache = CacheManager(CacheConfig(max_size=50))

    @cache.cache(ttl=300, key_prefix="api")
    def expensive_api_call(user_id: str):
        """Simulate expensive API call"""
        print(f"  -> Making API call for user {user_id}...")
        time.sleep(0.1)  # Simulate network delay
        return {"id": user_id, "name": f"User {user_id}", "loaded_at": time.time()}

    # First call - cache miss
    print("First call (cache miss):")
    start = time.time()
    result1 = expensive_api_call("123")
    elapsed1 = time.time() - start
    print(f"  Result: {result1}")
    print(f"  Time: {elapsed1*1000:.1f}ms")

    # Second call - cache hit
    print("\nSecond call (cache hit):")
    start = time.time()
    result2 = expensive_api_call("123")
    elapsed2 = time.time() - start
    print(f"  Result: {result2}")
    print(f"  Time: {elapsed2*1000:.1f}ms")

    print(f"\nSpeedup: {elapsed1/elapsed2:.1f}x faster")

    # Different user - cache miss
    print("\nDifferent user (cache miss):")
    result3 = expensive_api_call("456")
    print(f"  Result: {result3}")

    stats = cache.get_stats()
    print(f"\nFinal Stats - Hit Rate: {stats.hit_rate:.1f}%")


# ============================================================================
# Example 3: Namespace Management
# ============================================================================

def example_namespaces():
    """Demonstrate cache namespace management"""
    print("\n" + "="*60)
    print("Example 3: Cache Namespaces")
    print("="*60)

    cache = CacheManager()

    # Store data in different namespaces
    cache.set("user:123", {"name": "John"}, prefix="herp")
    cache.set("user:123", {"name": "Jane"}, prefix="notion")
    cache.set("page:123", {"title": "Page 1"}, prefix="notion")

    # Retrieve from specific namespaces
    herp_user = cache.get("user:123", prefix="herp")
    notion_user = cache.get("user:123", prefix="notion")

    print(f"HERP user:123: {herp_user}")
    print(f"Notion user:123: {notion_user}")

    # Clear specific namespace
    print(f"\nCache size before clear: {cache.size()}")
    cleared = cache.clear(prefix="notion")
    print(f"Cleared {cleared} items from 'notion' namespace")
    print(f"Cache size after clear: {cache.size()}")

    # HERP data still exists
    herp_user = cache.get("user:123", prefix="herp")
    print(f"HERP user still cached: {herp_user}")


# ============================================================================
# Example 4: Real-World HERP Integration
# ============================================================================

def example_herp_integration():
    """Demonstrate cache with HERP client"""
    print("\n" + "="*60)
    print("Example 4: HERP Client Integration")
    print("="*60)

    # This example requires valid HERP API credentials
    # Uncomment and add your credentials to test

    """
    import os

    cache = CacheManager(CacheConfig(max_size=1000, default_ttl=3600))

    herp_config = HerpConfig(
        api_key=os.getenv("HERP_API_KEY"),
        base_url="https://public-api.herp.cloud/hire/public"
    )
    herp_client = HerpClient(config=herp_config, cache_manager=cache)

    # Decorator for caching requisitions
    @cache.cache(ttl=7200, key_prefix="herp")  # 2 hour cache
    def get_requisitions():
        print("  -> Fetching requisitions from API...")
        return herp_client.list_requisitions()

    # Decorator for caching users
    @cache.cache(ttl=3600, key_prefix="herp")  # 1 hour cache
    def get_users():
        print("  -> Fetching users from API...")
        return herp_client.list_users()

    # First sync
    print("First sync:")
    reqs1 = get_requisitions()  # API call
    users1 = get_users()  # API call
    print(f"  Loaded {len(reqs1)} requisitions, {len(users1)} users")

    # Second sync (cached)
    print("\nSecond sync (cached):")
    reqs2 = get_requisitions()  # Cache hit
    users2 = get_users()  # Cache hit
    print(f"  Loaded {len(reqs2)} requisitions, {len(users2)} users")

    stats = cache.get_stats()
    print(f"\nCache hit rate: {stats.hit_rate:.1f}%")
    print(f"API calls saved: {stats.hits}")
    """

    print("\nNote: This example requires valid HERP API credentials.")
    print("Uncomment and configure to test with real API.")


# ============================================================================
# Example 5: TTL and Expiration
# ============================================================================

def example_ttl_expiration():
    """Demonstrate TTL and expiration behavior"""
    print("\n" + "="*60)
    print("Example 5: TTL and Expiration")
    print("="*60)

    cache = CacheManager(CacheConfig(default_ttl=2))  # 2 second default

    # Set with short TTL
    cache.set("temp_data", "This will expire", ttl=1)
    cache.set("persistent_data", "This lasts longer", ttl=10)

    print("Immediately after set:")
    print(f"  temp_data: {cache.get('temp_data')}")
    print(f"  persistent_data: {cache.get('persistent_data')}")

    # Wait for first item to expire
    print("\nWaiting 1.5 seconds...")
    time.sleep(1.5)

    print("After 1.5 seconds:")
    print(f"  temp_data: {cache.get('temp_data')}")  # None (expired)
    print(f"  persistent_data: {cache.get('persistent_data')}")  # Still cached

    # Cleanup expired entries
    cleaned = cache.cleanup()
    print(f"\nCleaned up {cleaned} expired entries")


# ============================================================================
# Example 6: Global Cache Instance
# ============================================================================

def example_global_cache():
    """Demonstrate global cache pattern"""
    print("\n" + "="*60)
    print("Example 6: Global Cache Instance")
    print("="*60)

    # Get global cache (created once, reused everywhere)
    cache1 = get_global_cache(CacheConfig(max_size=500))
    cache1.set("shared_key", "shared_value")

    # Get same instance elsewhere
    cache2 = get_global_cache()

    print(f"Cache 1 size: {cache1.size()}")
    print(f"Cache 2 size: {cache2.size()}")
    print(f"Same instance: {cache1 is cache2}")
    print(f"Shared value: {cache2.get('shared_key')}")


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "CACHE USAGE EXAMPLES" + " "*23 + "║")
    print("╚" + "="*58 + "╝")

    example_manual_caching()
    example_decorator_caching()
    example_namespaces()
    example_ttl_expiration()
    example_global_cache()
    example_herp_integration()

    print("\n" + "="*60)
    print("All examples complete!")
    print("="*60 + "\n")
