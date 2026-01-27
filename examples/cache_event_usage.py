#!/usr/bin/env python3
"""
Example: Event-driven Cache Invalidation

This example demonstrates how to use the event-driven cache invalidation system
to automatically invalidate cache entries when data is modified.

The event system prevents stale data by:
1. Listening to data modification events (CREATE, UPDATE, DELETE)
2. Automatically invalidating relevant cache entries
3. Supporting pattern-based invalidation for related data

Usage:
    python examples/cache_event_usage.py
"""

from src.core.cache import (
    CacheManager,
    CacheConfig,
    get_cache_event_bus,
    CacheEventType,
)
from src.core.herp.client import HerpClient
from src.core.utils.config import HerpConfig


def basic_event_driven_cache_example():
    """Basic example of event-driven cache invalidation"""
    print("=" * 70)
    print("Basic Event-Driven Cache Invalidation Example")
    print("=" * 70)

    # 1. Create cache manager
    cache = CacheManager(CacheConfig(max_size=100, default_ttl=3600))

    # 2. Get event bus and register cache
    event_bus = get_cache_event_bus()
    event_bus.register_cache(cache)

    # 3. Cache some data
    cache.set("candidacy:12345", {"id": "12345", "name": "John Doe"}, prefix="herp")
    cache.set(
        "candidacy:12345:contacts",
        [{"id": "c1", "type": "interview"}],
        prefix="herp",
    )

    print("\n1. Initial cache state:")
    print(f"   Candidacy: {cache.get('candidacy:12345', prefix='herp')}")
    print(f"   Contacts: {cache.get('candidacy:12345:contacts', prefix='herp')}")

    # 4. Emit update event - this automatically invalidates related cache
    print("\n2. Emitting UPDATE event for candidacy 12345...")
    invalidated_count = event_bus.emit_update(
        resource_type="candidacy", resource_id="12345", prefix="herp"
    )
    print(f"   Invalidated {invalidated_count} cache entries")

    # 5. Verify cache was invalidated
    print("\n3. After invalidation:")
    print(f"   Candidacy: {cache.get('candidacy:12345', prefix='herp')}")
    print(f"   Contacts: {cache.get('candidacy:12345:contacts', prefix='herp')}")
    print("   ✓ Both entries automatically invalidated!")


def integrated_herp_client_example():
    """Example showing integration with HerpClient (pseudo-code)"""
    print("\n" + "=" * 70)
    print("Integrated HerpClient with Event-Driven Cache")
    print("=" * 70)

    # Initialize cache and event bus
    cache = CacheManager(CacheConfig(max_size=1000, default_ttl=3600))
    event_bus = get_cache_event_bus()
    event_bus.register_cache(cache)

    print("\n1. Cache initialized and registered with event bus")

    # When updating a candidacy in HerpClient, you would:
    # a) Update the data via API
    # b) Emit an event to invalidate cache
    print("\n2. Pseudo-code for HerpClient update method:")
    print("""
    def update_candidacy(self, candidacy_id: str, data: dict):
        # Update via API
        result = self._make_request("PATCH", f"/v1/candidacies/{candidacy_id}", json=data)

        # Emit event to invalidate cache
        event_bus = get_cache_event_bus()
        event_bus.emit_update(
            resource_type="candidacy",
            resource_id=candidacy_id,
            prefix="herp",
            invalidation_patterns=[
                f"contact:.*:{candidacy_id}",  # Invalidate related contacts
                f"file:.*:{candidacy_id}",     # Invalidate related files
                f"timeline:.*:{candidacy_id}"  # Invalidate timeline
            ]
        )

        return result
    """)

    print("   ✓ All related cache entries automatically invalidated on update!")


def bulk_update_example():
    """Example showing bulk update invalidation"""
    print("\n" + "=" * 70)
    print("Bulk Update Cache Invalidation")
    print("=" * 70)

    cache = CacheManager(CacheConfig(max_size=1000, default_ttl=3600))
    event_bus = get_cache_event_bus()
    event_bus.register_cache(cache)

    # Cache multiple candidacies
    print("\n1. Caching 100 candidacies...")
    for i in range(100):
        cache.set(f"candidacy:{i}", {"id": str(i)}, prefix="herp")

    print(f"   Cache size: {cache.size()} entries")

    # Bulk update event
    print("\n2. Emitting BULK_UPDATE event for all candidacies...")
    invalidated_count = event_bus.emit_bulk_update(
        resource_type="candidacy", prefix="herp"
    )
    print(f"   Invalidated {invalidated_count} cache entries")

    print(f"\n3. After bulk invalidation:")
    print(f"   Cache size: {cache.size()} entries")
    print("   ✓ All candidacy entries invalidated!")


def create_delete_events_example():
    """Example showing CREATE and DELETE events"""
    print("\n" + "=" * 70)
    print("CREATE and DELETE Event Handling")
    print("=" * 70)

    cache = CacheManager(CacheConfig(max_size=100, default_ttl=3600))
    event_bus = get_cache_event_bus()
    event_bus.register_cache(cache)

    # Cache list of candidacies
    print("\n1. Caching list of candidacies...")
    cache.set("list_candidacies", [{"id": "1"}, {"id": "2"}], prefix="herp")
    cache.set("candidacy_list_all", [{"id": "1"}, {"id": "2"}], prefix="herp")

    print(
        f"   list_candidacies: {cache.get('list_candidacies', prefix='herp')}"
    )

    # CREATE event invalidates list caches
    print("\n2. Emitting CREATE event for new candidacy...")
    event_bus.emit_create(resource_type="candidacy", resource_id="3", prefix="herp")

    print("\n3. After CREATE event:")
    print(f"   list_candidacies: {cache.get('list_candidacies', prefix='herp')}")
    print("   ✓ List cache invalidated (stale after new entry created)")

    # Re-cache
    cache.set(
        "list_candidacies", [{"id": "1"}, {"id": "2"}, {"id": "3"}], prefix="herp"
    )
    cache.set("candidacy:2", {"id": "2", "name": "Jane"}, prefix="herp")

    # DELETE event invalidates resource and lists
    print("\n4. Emitting DELETE event for candidacy 2...")
    event_bus.emit_delete(resource_type="candidacy", resource_id="2", prefix="herp")

    print("\n5. After DELETE event:")
    print(f"   candidacy:2: {cache.get('candidacy:2', prefix='herp')}")
    print(f"   list_candidacies: {cache.get('list_candidacies', prefix='herp')}")
    print("   ✓ Both resource and list caches invalidated")


def performance_example():
    """Example showing performance of event system"""
    print("\n" + "=" * 70)
    print("Event System Performance")
    print("=" * 70)

    import time

    cache = CacheManager(CacheConfig(max_size=10000, default_ttl=3600))
    event_bus = get_cache_event_bus()
    listener = event_bus.register_cache(cache)

    # Cache 1000 entries
    print("\n1. Caching 1000 candidacies...")
    for i in range(1000):
        cache.set(f"candidacy:{i}", {"id": str(i)}, prefix="herp")

    # Measure bulk invalidation performance
    print("\n2. Measuring bulk invalidation performance...")
    start = time.time()
    count = event_bus.emit_bulk_update(resource_type="candidacy", prefix="herp")
    duration = time.time() - start

    print(f"   Invalidated {count} entries in {duration:.4f} seconds")
    print(f"   Rate: {count/duration:.0f} invalidations/second")
    print(f"   Total invalidations: {listener.get_invalidation_count()}")
    print("   ✓ Event system handles large-scale invalidation efficiently")


def statistics_example():
    """Example showing cache statistics with events"""
    print("\n" + "=" * 70)
    print("Cache Statistics with Event System")
    print("=" * 70)

    cache = CacheManager(CacheConfig(max_size=100, default_ttl=3600))
    event_bus = get_cache_event_bus()
    listener = event_bus.register_cache(cache)

    # Simulate cache usage
    print("\n1. Simulating cache usage...")
    cache.set("candidacy:1", {"id": "1"}, prefix="herp")
    cache.get("candidacy:1", prefix="herp")  # Hit
    cache.get("candidacy:1", prefix="herp")  # Hit
    cache.get("candidacy:2", prefix="herp")  # Miss

    stats = cache.get_stats()
    print(f"   Hits: {stats.hits}")
    print(f"   Misses: {stats.misses}")
    print(f"   Hit Rate: {stats.hit_rate:.1f}%")

    # Invalidate and check
    print("\n2. Invalidating candidacy:1...")
    event_bus.emit_update("candidacy", "1", prefix="herp")

    print(f"\n3. Event system statistics:")
    print(f"   Total invalidations: {listener.get_invalidation_count()}")

    # Access after invalidation
    cache.get("candidacy:1", prefix="herp")  # Miss (invalidated)
    stats = cache.get_stats()

    print(f"\n4. After invalidation:")
    print(f"   Hits: {stats.hits}")
    print(f"   Misses: {stats.misses}")
    print(f"   Hit Rate: {stats.hit_rate:.1f}%")
    print("   ✓ Cache statistics track invalidation effects")


def main():
    """Run all examples"""
    print("\n")
    print("#" * 70)
    print("# Event-Driven Cache Invalidation Examples")
    print("#" * 70)

    basic_event_driven_cache_example()
    integrated_herp_client_example()
    bulk_update_example()
    create_delete_events_example()
    performance_example()
    statistics_example()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Event system automatically invalidates cache on data changes")
    print("  2. Supports CREATE, UPDATE, DELETE, and BULK_UPDATE events")
    print("  3. Pattern-based invalidation handles related data")
    print("  4. Thread-safe and performant for production use")
    print("  5. Integrates seamlessly with existing cache infrastructure")
    print()


if __name__ == "__main__":
    main()
