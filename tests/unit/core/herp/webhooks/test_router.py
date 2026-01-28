"""
Tests for HERP Webhook Router
"""

import json
import time
from unittest.mock import Mock

import pytest

from src.core.herp.webhooks.router import (
    AsyncWebhookRouter,
    FailedEvent,
    WebhookRoute,
    WebhookRouter,
)

# Mark all tests to ignore structlog warnings
pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


class TestWebhookRoute:
    """Test WebhookRoute dataclass"""

    def test_initialization(self):
        """Test route initialization"""
        handler = Mock()

        route = WebhookRoute(
            event_type="candidacy.created",
            handler=handler,
            max_retries=3,
            retry_delay=1.0,
        )

        assert route.event_type == "candidacy.created"
        assert route.handler == handler
        assert route.max_retries == 3
        assert route.retry_delay == 1.0
        assert route.backoff_multiplier == 2.0
        assert route.max_retry_delay == 60.0

    def test_initialization_with_filter(self):
        """Test route initialization with filter"""
        handler = Mock()
        filter_fn = lambda data: data.get("status") == "active"

        route = WebhookRoute(
            event_type="candidacy.updated", handler=handler, filter=filter_fn
        )

        assert route.filter == filter_fn

    def test_initialization_defaults(self):
        """Test route initialization with defaults"""
        handler = Mock()

        route = WebhookRoute(event_type="test", handler=handler)

        assert route.filter is None
        assert route.max_retries == 3
        assert route.retry_delay == 1.0
        assert route.backoff_multiplier == 2.0
        assert route.max_retry_delay == 60.0


class TestFailedEvent:
    """Test FailedEvent dataclass"""

    def test_initialization(self):
        """Test failed event initialization"""
        payload = {"event": "test", "data": {}}
        error = "Handler failed"

        failed = FailedEvent(payload=payload, error=error)

        assert failed.payload == payload
        assert failed.error == error
        assert failed.retries == 0
        assert failed.route is None
        assert failed.failed_at is not None

    def test_initialization_with_route(self):
        """Test failed event with route"""
        handler = Mock()
        route = WebhookRoute(event_type="test", handler=handler)
        payload = {"event": "test"}

        failed = FailedEvent(payload=payload, error="Error", route=route, retries=3)

        assert failed.route == route
        assert failed.retries == 3


class TestWebhookRouterInitialization:
    """Test WebhookRouter initialization"""

    def test_initialization(self):
        """Test router initialization"""
        router = WebhookRouter()

        assert router.routes == []
        assert router.enable_dlq is True
        assert router.processed_count == 0
        assert router.failed_count == 0
        assert len(router.dead_letter_queue) == 0

    def test_initialization_disable_dlq(self):
        """Test router initialization with DLQ disabled"""
        router = WebhookRouter(enable_dlq=False)

        assert router.enable_dlq is False


class TestWebhookRouterAddRoute:
    """Test adding routes"""

    @pytest.fixture
    def router(self):
        """Create router"""
        return WebhookRouter()

    def test_add_route_basic(self, router):
        """Test adding basic route"""
        handler = Mock()

        router.add_route(event_type="candidacy.created", handler=handler)

        assert len(router.routes) == 1
        assert router.routes[0].event_type == "candidacy.created"
        assert router.routes[0].handler == handler

    def test_add_route_with_filter(self, router):
        """Test adding route with filter"""
        handler = Mock()
        filter_fn = lambda data: data.get("status") == "active"

        router.add_route(
            event_type="candidacy.updated", handler=handler, filter=filter_fn
        )

        assert router.routes[0].filter == filter_fn

    def test_add_route_with_retry_config(self, router):
        """Test adding route with custom retry configuration"""
        handler = Mock()

        router.add_route(
            event_type="candidacy.created",
            handler=handler,
            max_retries=5,
            retry_delay=2.0,
            backoff_multiplier=3.0,
            max_retry_delay=120.0,
        )

        route = router.routes[0]
        assert route.max_retries == 5
        assert route.retry_delay == 2.0
        assert route.backoff_multiplier == 3.0
        assert route.max_retry_delay == 120.0

    def test_add_multiple_routes(self, router):
        """Test adding multiple routes"""
        handler1 = Mock()
        handler2 = Mock()

        router.add_route(event_type="candidacy.created", handler=handler1)
        router.add_route(event_type="candidacy.updated", handler=handler2)

        assert len(router.routes) == 2


class TestWebhookRouterRouting:
    """Test webhook routing"""

    @pytest.fixture
    def router(self):
        """Create router"""
        return WebhookRouter()

    def test_route_matching_event_type(self, router):
        """Test routing with matching event type"""
        handler = Mock()
        router.add_route(event_type="candidacy.created", handler=handler)

        payload = {"event": "candidacy.created", "event_id": "evt_123", "data": {}}

        router.route(payload)

        handler.assert_called_once_with(payload)
        assert router.processed_count == 1

    def test_route_no_matching_route(self, router):
        """Test routing with no matching route"""
        handler = Mock()
        router.add_route(event_type="candidacy.created", handler=handler)

        payload = {"event": "candidacy.updated", "event_id": "evt_123", "data": {}}

        router.route(payload)

        handler.assert_not_called()
        assert router.processed_count == 0

    def test_route_wildcard_match(self, router):
        """Test routing with wildcard route"""
        handler = Mock()
        router.add_route(event_type="*", handler=handler)

        payload = {"event": "any.event.type", "event_id": "evt_123", "data": {}}

        router.route(payload)

        handler.assert_called_once()

    def test_route_with_filter_matching(self, router):
        """Test routing with matching filter"""
        handler = Mock()
        filter_fn = lambda data: data.get("status") == "active"

        router.add_route(
            event_type="candidacy.updated", handler=handler, filter=filter_fn
        )

        payload = {
            "event": "candidacy.updated",
            "event_id": "evt_123",
            "data": {"status": "active"},
        }

        router.route(payload)

        handler.assert_called_once()

    def test_route_with_filter_not_matching(self, router):
        """Test routing with non-matching filter"""
        handler = Mock()
        filter_fn = lambda data: data.get("status") == "active"

        router.add_route(
            event_type="candidacy.updated", handler=handler, filter=filter_fn
        )

        payload = {
            "event": "candidacy.updated",
            "event_id": "evt_123",
            "data": {"status": "terminated"},
        }

        router.route(payload)

        handler.assert_not_called()

    def test_route_multiple_matching_routes(self, router):
        """Test routing to multiple matching routes"""
        handler1 = Mock()
        handler2 = Mock()

        router.add_route(event_type="*", handler=handler1)
        router.add_route(event_type="candidacy.created", handler=handler2)

        payload = {"event": "candidacy.created", "event_id": "evt_123", "data": {}}

        router.route(payload)

        handler1.assert_called_once()
        handler2.assert_called_once()
        assert router.processed_count == 2


class TestWebhookRouterRetry:
    """Test retry logic"""

    @pytest.fixture
    def router(self):
        """Create router"""
        return WebhookRouter()

    def test_retry_on_failure(self, router):
        """Test retry on handler failure"""
        handler = Mock(
            side_effect=[Exception("Error"), None]
        )  # Fail once, then succeed

        router.add_route(
            event_type="test",
            handler=handler,
            max_retries=1,
            retry_delay=0.01,  # Short delay for testing
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        router.route(payload)

        # Should be called twice (initial + 1 retry)
        assert handler.call_count == 2
        assert router.processed_count == 1
        assert router.failed_count == 0

    def test_max_retries_exceeded(self, router):
        """Test max retries exceeded"""
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test",
            handler=handler,
            max_retries=2,
            retry_delay=0.01,
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        router.route(payload)

        # Should be called 3 times (initial + 2 retries)
        assert handler.call_count == 3
        assert router.processed_count == 0
        assert router.failed_count == 1

    def test_exponential_backoff(self, router):
        """Test exponential backoff timing"""
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test",
            handler=handler,
            max_retries=2,
            retry_delay=0.1,
            backoff_multiplier=2.0,
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        start = time.time()
        router.route(payload)
        duration = time.time() - start

        # Should have delays: 0.1s, 0.2s = 0.3s total minimum
        assert duration >= 0.3
        assert handler.call_count == 3


class TestWebhookRouterDLQ:
    """Test dead letter queue"""

    @pytest.fixture
    def router(self):
        """Create router with DLQ enabled"""
        return WebhookRouter(enable_dlq=True)

    def test_failed_event_added_to_dlq(self, router):
        """Test failed event added to DLQ"""
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        router.route(payload)

        dlq = router.get_dead_letter_queue()
        assert len(dlq) == 1
        assert dlq[0].payload == payload
        assert "Always fails" in dlq[0].error

    def test_dlq_disabled(self):
        """Test DLQ disabled"""
        router = WebhookRouter(enable_dlq=False)
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        router.route(payload)

        dlq = router.get_dead_letter_queue()
        assert len(dlq) == 0

    def test_dlq_max_size(self):
        """Test DLQ max size limit"""
        router = WebhookRouter(enable_dlq=True)
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        # Add more events than max DLQ size (1000)
        for i in range(1100):
            payload = {"event": "test", "event_id": f"evt_{i}", "data": {}}
            router.route(payload)

        dlq = router.get_dead_letter_queue()
        # Should be capped at 1000
        assert len(dlq) == 1000

    def test_replay_failed_event(self, router):
        """Test replaying failed event"""
        handler = Mock(side_effect=[Exception("Fail first time"), None])

        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        # First attempt - should fail
        router.route(payload)

        assert router.failed_count == 1
        dlq = router.get_dead_letter_queue()
        assert len(dlq) == 1

        # Replay - should succeed
        router.replay_failed_event(dlq[0])

        assert router.processed_count == 1

    def test_clear_dlq(self, router):
        """Test clearing DLQ"""
        handler = Mock(side_effect=Exception("Always fails"))

        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}
        router.route(payload)

        assert len(router.get_dead_letter_queue()) == 1

        router.clear_dead_letter_queue()

        assert len(router.get_dead_letter_queue()) == 0


class TestWebhookRouterRawPayload:
    """Test routing from raw payloads"""

    @pytest.fixture
    def router(self):
        """Create router"""
        return WebhookRouter()

    def test_route_raw_valid_json(self, router):
        """Test routing from raw JSON bytes"""
        handler = Mock()
        router.add_route(event_type="test", handler=handler)

        payload = {"event": "test", "event_id": "evt_123", "data": {}}
        raw_payload = json.dumps(payload).encode()

        router.route_raw(raw_payload)

        handler.assert_called_once()

    def test_route_raw_invalid_json(self, router):
        """Test routing from invalid JSON"""
        handler = Mock()
        router.add_route(event_type="test", handler=handler)

        raw_payload = b"invalid json {{"

        router.route_raw(raw_payload)

        handler.assert_not_called()


class TestWebhookRouterStats:
    """Test router statistics"""

    @pytest.fixture
    def router(self):
        """Create router"""
        return WebhookRouter()

    def test_get_stats(self, router):
        """Test getting router statistics"""
        handler = Mock()
        router.add_route(event_type="test", handler=handler)

        payload = {"event": "test", "event_id": "evt_123", "data": {}}
        router.route(payload)

        stats = router.get_stats()

        assert stats["routes"] == 1
        assert stats["processed"] == 1
        assert stats["failed"] == 0
        assert stats["dlq_size"] == 0

    def test_stats_with_failures(self, router):
        """Test stats with failures"""
        handler = Mock(side_effect=Exception("Fail"))
        router.add_route(
            event_type="test", handler=handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}
        router.route(payload)

        stats = router.get_stats()

        assert stats["processed"] == 0
        assert stats["failed"] == 1
        assert stats["dlq_size"] == 1


class TestAsyncWebhookRouter:
    """Test AsyncWebhookRouter"""

    @pytest.fixture
    def router(self):
        """Create async router"""
        return AsyncWebhookRouter()

    @pytest.mark.asyncio
    async def test_route_async_handler(self, router):
        """Test routing with async handler"""
        handler = Mock()

        async def async_handler(payload):
            handler(payload)

        router.add_route(event_type="test", handler=async_handler)

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        await router.route(payload)

        handler.assert_called_once_with(payload)
        assert router.processed_count == 1

    @pytest.mark.asyncio
    async def test_route_async_with_retry(self, router):
        """Test async routing with retry"""
        call_count = 0

        async def async_handler(payload):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Fail first time")

        router.add_route(
            event_type="test", handler=async_handler, max_retries=1, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        await router.route(payload)

        assert call_count == 2
        assert router.processed_count == 1

    @pytest.mark.asyncio
    async def test_route_async_max_retries(self, router):
        """Test async routing with max retries exceeded"""

        async def async_handler(payload):
            raise Exception("Always fails")

        router.add_route(
            event_type="test", handler=async_handler, max_retries=2, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        await router.route(payload)

        assert router.processed_count == 0
        assert router.failed_count == 1

    @pytest.mark.asyncio
    async def test_route_async_dlq(self, router):
        """Test async DLQ"""

        async def async_handler(payload):
            raise Exception("Fail")

        router.add_route(
            event_type="test", handler=async_handler, max_retries=0, retry_delay=0.01
        )

        payload = {"event": "test", "event_id": "evt_123", "data": {}}

        await router.route(payload)

        dlq = router.get_dead_letter_queue()
        assert len(dlq) == 1

    @pytest.mark.asyncio
    async def test_route_raw_async(self, router):
        """Test routing from raw bytes asynchronously"""
        handler = Mock()

        async def async_handler(payload):
            handler(payload)

        router.add_route(event_type="test", handler=async_handler)

        payload = {"event": "test", "event_id": "evt_123", "data": {}}
        raw_payload = json.dumps(payload).encode()

        await router.route_raw(raw_payload)

        handler.assert_called_once()

    def test_get_stats_async(self, router):
        """Test getting stats from async router"""
        stats = router.get_stats()

        assert "routes" in stats
        assert "processed" in stats
        assert "failed" in stats
        assert "dlq_size" in stats
