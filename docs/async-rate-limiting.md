# Async/Await Rate Limiting Refactoring

## Overview

This document describes the async/await refactoring of the rate limiting system to provide non-blocking rate limiting for HERP and Notion APIs.

## Motivation

The original synchronous rate limiters used `time.sleep()` and `threading.Lock`, which:
- **Blocked the calling thread** during rate limit waits
- **Could not be used in async contexts** (asyncio applications)
- **Prevented concurrent request processing** within a single thread
- **Limited scalability** for high-throughput async applications

The async refactoring enables:
- ✅ **Non-blocking waits** using `asyncio.sleep()`
- ✅ **Concurrent request handling** within the event loop
- ✅ **Async/await pattern support** for modern Python applications
- ✅ **Better resource utilization** by not blocking threads
- ✅ **Scalability** for async applications with many concurrent requests

## Implementation

### New Async Modules

#### 1. `src/core/herp/async_rate_limiter.py`

**AsyncHerpRateLimiter**: Async version of HERP API rate limiter
- Token bucket algorithm (100 requests/minute)
- Non-blocking token acquisition using `asyncio.sleep()`
- `asyncio.Lock` for coroutine-safe operations
- Async context manager support (`async with`)

**AsyncAdaptiveRateLimiter**: Adaptive async rate limiter
- Adjusts rate based on `x-remaining-request` header
- Conservative behavior when approaching limits
- Non-blocking adaptive waits

**Global functions**:
- `get_async_rate_limiter()`: Get or create global async limiter
- `reset_async_rate_limiter()`: Reset global limiter (for testing)

#### 2. `src/core/notion/async_rate_limiter.py`

**AsyncNotionRateLimiter**: Async version of Notion API rate limiter
- Sliding window algorithm (3 requests/second)
- Non-blocking window management
- Async lock for concurrent safety

**AsyncAdaptiveNotionRateLimiter**: Adaptive async rate limiter
- Gradually increases rate after slowdowns
- Exponential backoff on errors
- Non-blocking adaptive behavior

**Global functions**:
- `get_async_rate_limiter()`: Get or create global async limiter
- `reset_async_rate_limiter()`: Reset global limiter (for testing)

### Key Design Decisions

#### 1. While Loop Outside Lock

```python
async def acquire(self, timeout: Optional[float] = None) -> bool:
    while True:
        async with self.lock:
            # Check for tokens
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            # Calculate wait time
            wait_time = self.min_interval / 2

        # Wait OUTSIDE the lock - allows other coroutines to proceed
        await asyncio.sleep(wait_time)
```

This design ensures the event loop isn't blocked while waiting for tokens.

#### 2. Separate Async and Sync Versions

We created new async modules rather than modifying existing ones to:
- **Maintain backwards compatibility** with synchronous code
- **Allow gradual migration** to async patterns
- **Avoid mixed sync/async complexity** in a single module
- **Keep sync version for simple use cases** that don't need async

#### 3. Synchronous Helper Methods

Methods like `_refill_tokens()` and `_can_make_request()` remain synchronous because they:
- Perform quick calculations without I/O
- Are called within async context but don't need to be awaited
- Keep the code simpler and more efficient

## Usage Examples

### Basic Async Usage

```python
import asyncio
from src.core.herp.async_rate_limiter import AsyncHerpRateLimiter

async def make_api_calls():
    limiter = AsyncHerpRateLimiter(requests_per_minute=100)

    # Acquire permission before making request
    await limiter.acquire()
    response = await make_http_request()

    # Or use context manager
    async with limiter:
        response = await make_http_request()
```

### Concurrent Requests

```python
async def fetch_many_candidates():
    limiter = AsyncHerpRateLimiter(requests_per_minute=100)

    async def fetch_one(candidacy_id):
        await limiter.acquire()
        return await client.get_candidacy(candidacy_id)

    # All requests respect rate limit without blocking event loop
    tasks = [fetch_one(cid) for cid in candidacy_ids]
    results = await asyncio.gather(*tasks)
```

### Adaptive Rate Limiting

```python
from src.core.herp.async_rate_limiter import AsyncAdaptiveRateLimiter

async def smart_api_calls():
    limiter = AsyncAdaptiveRateLimiter(requests_per_minute=100)

    async with limiter:
        response = await client.get(url)

        # Update limiter based on API response
        limiter.update_from_response_headers(response.headers)
```

### Global Limiter

```python
from src.core.herp.async_rate_limiter import get_async_rate_limiter

async def main():
    # Get global limiter (shared across application)
    limiter = await get_async_rate_limiter(adaptive=True)

    await limiter.acquire()
    response = await make_request()
```

## Testing

### Test Coverage

**HERP Async Rate Limiter**: 23 tests
- Token bucket algorithm
- Token refill over time
- Rate limiting enforcement
- Concurrent acquisition
- Adaptive behavior with headers
- Global limiter management
- High concurrency performance
- Non-blocking behavior verification

**Notion Async Rate Limiter**: 25 tests
- Sliding window algorithm
- Burst capacity
- Rate limiting enforcement
- Adaptive rate adjustment
- Error handling with backoff
- Global limiter management
- High concurrency performance
- Minimum interval enforcement

**Total**: 48 tests, all passing ✅

### Running Tests

```bash
# Test HERP async rate limiter
pytest tests/unit/core/herp/test_async_rate_limiter.py -v

# Test Notion async rate limiter
pytest tests/unit/core/notion/test_async_rate_limiter.py -v

# Test both
pytest tests/unit/core/*/test_async_rate_limiter.py -v
```

## Performance Benefits

### Before (Synchronous)

```python
import time

def make_100_requests():
    limiter = HerpRateLimiter(requests_per_minute=100)

    for i in range(100):
        limiter.acquire()  # BLOCKS the thread
        make_request()

    # Total time: ~60 seconds (strictly sequential)
```

### After (Asynchronous)

```python
import asyncio

async def make_100_requests():
    limiter = AsyncHerpRateLimiter(requests_per_minute=100)

    async def make_one():
        await limiter.acquire()  # NON-BLOCKING
        await make_request()

    # Process concurrently up to rate limit
    tasks = [make_one() for _ in range(100)]
    await asyncio.gather(*tasks)

    # Total time: ~60 seconds (but event loop free for other work)
    # Other coroutines can run during waits!
```

## Migration Guide

### For New Async Code

Use the async rate limiters directly:

```python
from src.core.herp.async_rate_limiter import get_async_rate_limiter

async def my_async_function():
    limiter = await get_async_rate_limiter()
    await limiter.acquire()
    # Make API call
```

### For Existing Sync Code

**Option 1**: Keep using synchronous rate limiters (no changes needed)

```python
from src.core.herp.rate_limiter import HerpRateLimiter

def my_sync_function():
    limiter = HerpRateLimiter()
    limiter.acquire()
    # Make API call
```

**Option 2**: Gradually migrate to async

```python
# Before
def fetch_candidates():
    limiter = HerpRateLimiter()
    for cid in candidate_ids:
        limiter.acquire()
        data = sync_http_client.get(cid)

# After
async def fetch_candidates():
    limiter = AsyncHerpRateLimiter()
    async def fetch_one(cid):
        await limiter.acquire()
        return await async_http_client.get(cid)

    tasks = [fetch_one(cid) for cid in candidate_ids]
    return await asyncio.gather(*tasks)
```

## API Reference

### AsyncHerpRateLimiter

```python
class AsyncHerpRateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: Optional[int] = None
    )

    async def acquire(self, timeout: Optional[float] = None) -> bool
    async def wait(self) -> None
    async def get_available_tokens(self) -> float
    async def reset(self) -> None
    def get_current_rate(self) -> float

    # Async context manager
    async def __aenter__(self) -> Self
    async def __aexit__(self, ...) -> None
```

### AsyncAdaptiveRateLimiter

```python
class AsyncAdaptiveRateLimiter(AsyncHerpRateLimiter):
    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: Optional[int] = None,
        safety_margin: float = 0.9
    )

    def update_from_response_headers(self, headers: dict) -> None
    async def acquire(self, timeout: Optional[float] = None) -> bool
```

### AsyncNotionRateLimiter

```python
class AsyncNotionRateLimiter:
    def __init__(
        self,
        requests_per_second: int = 3,
        burst_size: Optional[int] = None
    )

    async def acquire(self, timeout: Optional[float] = None) -> bool
    async def wait(self) -> None
    async def get_available_capacity(self) -> int
    async def reset(self) -> None
    async def handle_rate_limit_error(self) -> None
    def get_current_rate(self) -> float

    # Async context manager
    async def __aenter__(self) -> Self
    async def __aexit__(self, ...) -> None
```

### AsyncAdaptiveNotionRateLimiter

```python
class AsyncAdaptiveNotionRateLimiter(AsyncNotionRateLimiter):
    def __init__(
        self,
        requests_per_second: int = 3,
        burst_size: Optional[int] = None,
        safety_margin: float = 0.9
    )

    async def handle_success(self) -> None
    async def handle_rate_limit_error(self) -> None
```

## Future Enhancements

Potential improvements for future iterations:

1. **Async HTTP Client Integration**
   - Create async HERP and Notion client classes
   - Automatically use async rate limiters
   - Seamless integration with aiohttp/httpx

2. **Distributed Rate Limiting**
   - Redis-backed async rate limiter for multi-instance deployments
   - Shared token bucket across processes
   - Cluster-wide rate limiting

3. **Advanced Metrics**
   - Async metrics collection for rate limiter statistics
   - Real-time rate limit monitoring
   - Grafana/Prometheus integration

4. **Circuit Breaker Integration**
   - Combine async rate limiting with circuit breaker pattern
   - Automatic backoff on repeated failures
   - Health check integration

5. **Priority Queues**
   - Priority-based token acquisition
   - VIP requests bypass normal limits
   - Fair queuing algorithms

## Conclusion

The async/await refactoring provides:
- ✅ **Non-blocking rate limiting** for modern async applications
- ✅ **100% backwards compatible** with existing synchronous code
- ✅ **Comprehensive test coverage** (48 tests, all passing)
- ✅ **Production-ready** async rate limiters for HERP and Notion APIs
- ✅ **Better resource utilization** and scalability

The synchronous rate limiters remain available for simple use cases, while the new async versions enable high-performance concurrent applications.
