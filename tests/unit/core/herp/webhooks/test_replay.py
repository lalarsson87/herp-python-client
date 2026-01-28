"""
Tests for HERP Webhook Event Replay
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.core.herp.webhooks.replay import EventReplayer, EventStore
from src.core.herp.webhooks.router import FailedEvent, WebhookRoute, WebhookRouter

# Mark all tests to ignore structlog warnings
pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


class TestEventStoreInitialization:
    """Test EventStore initialization"""

    def test_initialization_default_path(self):
        """Test event store initialization with default path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            store = EventStore(storage_path=storage_path)

            assert store.storage_path.exists()
            assert store.events_file == store.storage_path / "events.jsonl"
            assert (
                store.failed_events_file == store.storage_path / "failed_events.jsonl"
            )

    def test_initialization_creates_directory(self):
        """Test event store creates storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / "nested" / "path" / "events")
            store = EventStore(storage_path=storage_path)

            assert store.storage_path.exists()
            assert store.storage_path.is_dir()


class TestEventStoreStoreEvent:
    """Test storing events"""

    @pytest.fixture
    def store(self):
        """Create event store"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            yield EventStore(storage_path=storage_path)

    def test_store_success_event(self, store):
        """Test storing successful event"""
        payload = {
            "event": "candidacy.created",
            "event_id": "evt_123",
            "data": {"candidacy_id": "cand_123"},
        }

        store.store_event("candidacy.created", payload, status="success")

        # Check event was stored
        assert store.events_file.exists()

        # Read and verify
        with open(store.events_file) as f:
            stored = json.loads(f.readline())

        assert stored["event_type"] == "candidacy.created"
        assert stored["event_id"] == "evt_123"
        assert stored["payload"] == payload
        assert stored["status"] == "success"
        assert "stored_at" in stored

    def test_store_failed_event(self, store):
        """Test storing failed event"""
        payload = {
            "event": "candidacy.updated",
            "event_id": "evt_456",
            "data": {},
        }

        store.store_event("candidacy.updated", payload, status="failed")

        # Failed events go to separate file
        assert store.failed_events_file.exists()

        with open(store.failed_events_file) as f:
            stored = json.loads(f.readline())

        assert stored["status"] == "failed"
        assert stored["event_id"] == "evt_456"

    def test_store_multiple_events(self, store):
        """Test storing multiple events"""
        for i in range(5):
            payload = {"event": "test", "event_id": f"evt_{i}", "data": {}}
            store.store_event("test", payload)

        # Count lines in file
        with open(store.events_file) as f:
            lines = f.readlines()

        assert len(lines) == 5

    def test_store_failed_event_object(self, store):
        """Test storing FailedEvent object"""
        payload = {"event": "test", "event_id": "evt_789", "data": {}}
        failed = FailedEvent(
            payload=payload,
            error="Handler failed",
            retries=3,
            failed_at=datetime.now(),
        )

        store.store_failed_event(failed)

        # Read and verify
        with open(store.failed_events_file) as f:
            stored = json.loads(f.readline())

        assert stored["error"] == "Handler failed"
        assert stored["retries"] == 3
        assert "failed_at" in stored


class TestEventStoreGetEvents:
    """Test querying events"""

    @pytest.fixture
    def store(self):
        """Create event store with sample events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            store = EventStore(storage_path=storage_path)

            # Add test events
            now = datetime.now()

            # Success events
            for i in range(3):
                payload = {
                    "event": "candidacy.created",
                    "event_id": f"evt_success_{i}",
                    "data": {},
                }
                store.store_event("candidacy.created", payload, status="success")

            # Failed events
            for i in range(2):
                payload = {
                    "event": "candidacy.updated",
                    "event_id": f"evt_failed_{i}",
                    "data": {},
                }
                store.store_event("candidacy.updated", payload, status="failed")

            yield store

    def test_get_all_events(self, store):
        """Test getting all events"""
        events = store.get_events()

        # Should get both success and failed events
        assert len(events) == 5

    def test_get_events_by_type(self, store):
        """Test filtering by event type"""
        events = store.get_events(event_type="candidacy.created")

        assert len(events) == 3
        assert all(e["event_type"] == "candidacy.created" for e in events)

    def test_get_events_by_status(self, store):
        """Test filtering by status"""
        success_events = store.get_events(status="success")
        failed_events = store.get_events(status="failed")

        assert len(success_events) == 3
        assert len(failed_events) == 2

    def test_get_events_with_limit(self, store):
        """Test limit parameter"""
        events = store.get_events(limit=2)

        assert len(events) == 2

    def test_get_failed_events(self, store):
        """Test get_failed_events helper"""
        failed = store.get_failed_events()

        assert len(failed) == 2
        assert all(e["status"] == "failed" for e in failed)

    def test_get_events_nonexistent_file(self):
        """Test querying when files don't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            store = EventStore(storage_path=storage_path)

            events = store.get_events()

            assert events == []

    def test_get_events_time_filter(self, store):
        """Test filtering by time range"""
        now = datetime.now()

        # Events stored just now
        events_recent = store.get_events(since=now - timedelta(minutes=1))
        assert len(events_recent) == 5

        # Events from far future (none)
        events_future = store.get_events(since=now + timedelta(days=1))
        assert len(events_future) == 0

        # Events until far past (none)
        events_past = store.get_events(until=now - timedelta(days=1))
        assert len(events_past) == 0


class TestEventStoreStreamEvents:
    """Test event streaming"""

    @pytest.fixture
    def store(self):
        """Create event store with sample events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            store = EventStore(storage_path=storage_path)

            # Add test events
            for i in range(5):
                payload = {"event": "test", "event_id": f"evt_{i}", "data": {}}
                store.store_event("test", payload)

            yield store

    def test_stream_all_events(self, store):
        """Test streaming all events"""
        events = list(store.stream_events())

        assert len(events) == 5

    def test_stream_filtered_events(self, store):
        """Test streaming with event_type filter"""
        # Add different event type
        store.store_event("other", {"event": "other", "event_id": "evt_other"})

        events = list(store.stream_events(event_type="test"))

        assert len(events) == 5
        assert all(e["event_type"] == "test" for e in events)

    def test_stream_time_filtered(self, store):
        """Test streaming with time filter"""
        now = datetime.now()

        events = list(store.stream_events(since=now - timedelta(minutes=1)))

        assert len(events) == 5


class TestEventStoreStats:
    """Test event statistics"""

    @pytest.fixture
    def store(self):
        """Create event store"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            yield EventStore(storage_path=storage_path)

    def test_stats_empty_store(self, store):
        """Test stats for empty store"""
        stats = store.get_stats()

        assert stats["total_events"] == 0
        assert stats["failed_events"] == 0
        assert "storage_path" in stats

    def test_stats_with_events(self, store):
        """Test stats with events"""
        # Add success events
        for i in range(3):
            store.store_event("test", {"event": "test", "event_id": f"evt_{i}"})

        # Add failed events
        for i in range(2):
            store.store_event(
                "test",
                {"event": "test", "event_id": f"evt_failed_{i}"},
                status="failed",
            )

        stats = store.get_stats()

        assert stats["total_events"] == 3
        assert stats["failed_events"] == 2


class TestEventStoreClear:
    """Test clearing event store"""

    @pytest.fixture
    def store(self):
        """Create event store with events"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = str(Path(tmpdir) / ".webhook_events")
            store = EventStore(storage_path=storage_path)

            # Add events
            store.store_event("test", {"event": "test", "event_id": "evt_1"})
            store.store_event(
                "test", {"event": "test", "event_id": "evt_2"}, status="failed"
            )

            yield store

    def test_clear_all(self, store):
        """Test clearing all events"""
        assert store.events_file.exists()
        assert store.failed_events_file.exists()

        store.clear(clear_failed=True)

        assert not store.events_file.exists()
        assert not store.failed_events_file.exists()

    def test_clear_keep_failed(self, store):
        """Test clearing only success events"""
        store.clear(clear_failed=False)

        assert not store.events_file.exists()
        assert store.failed_events_file.exists()


class TestEventReplayerInitialization:
    """Test EventReplayer initialization"""

    def test_initialization(self):
        """Test replayer initialization"""
        router = WebhookRouter()
        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))
            replayer = EventReplayer(router, store)

            assert replayer.router == router
            assert replayer.event_store == store


class TestEventReplayerReplayEvents:
    """Test replaying events"""

    @pytest.fixture
    def setup(self):
        """Create replayer with events"""
        router = WebhookRouter()
        handler = Mock()
        router.add_route(event_type="*", handler=handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add test events
            for i in range(3):
                payload = {
                    "event": "candidacy.created",
                    "event_id": f"evt_{i}",
                    "data": {},
                }
                store.store_event("candidacy.created", payload)

            replayer = EventReplayer(router, store)

            yield replayer, handler

    def test_replay_all_events(self, setup):
        """Test replaying all events"""
        replayer, handler = setup

        result = replayer.replay_events()

        assert result["total"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0
        assert handler.call_count == 3

    def test_replay_with_event_type_filter(self, setup):
        """Test replaying with event type filter"""
        replayer, handler = setup

        # Add different event type
        payload = {"event": "other", "event_id": "evt_other", "data": {}}
        replayer.event_store.store_event("other", payload)

        result = replayer.replay_events(event_type="candidacy.created")

        # Should only replay candidacy.created events
        assert result["total"] == 3

    def test_replay_with_limit(self, setup):
        """Test replaying with limit"""
        replayer, handler = setup

        result = replayer.replay_events(limit=2)

        assert result["total"] == 2
        assert handler.call_count == 2

    def test_replay_dry_run(self, setup):
        """Test dry run mode"""
        replayer, handler = setup

        result = replayer.replay_events(dry_run=True)

        assert result["total"] == 3
        assert result["skipped"] == 3
        assert result["dry_run"] is True

        # Handler should not be called
        handler.assert_not_called()


class TestEventReplayerReplayFailed:
    """Test replaying failed events"""

    @pytest.fixture
    def setup(self):
        """Create replayer with failed events"""
        router = WebhookRouter()
        handler = Mock()
        router.add_route(event_type="*", handler=handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add success and failed events
            for i in range(2):
                store.store_event(
                    "test", {"event": "test", "event_id": f"evt_success_{i}"}
                )

            for i in range(3):
                store.store_event(
                    "test",
                    {"event": "test", "event_id": f"evt_failed_{i}"},
                    status="failed",
                )

            replayer = EventReplayer(router, store)

            yield replayer, handler

    def test_replay_only_failed(self, setup):
        """Test replaying only failed events"""
        replayer, handler = setup

        result = replayer.replay_failed_events()

        # Should only replay failed events
        assert result["total"] == 3
        assert handler.call_count == 3

    def test_replay_failed_with_limit(self, setup):
        """Test replaying failed events with limit"""
        replayer, handler = setup

        result = replayer.replay_failed_events(limit=1)

        assert result["total"] == 1

    def test_replay_failed_dry_run(self, setup):
        """Test dry run for failed events"""
        replayer, handler = setup

        result = replayer.replay_failed_events(dry_run=True)

        assert result["skipped"] == 3
        handler.assert_not_called()


class TestEventReplayerReplayById:
    """Test replaying specific event by ID"""

    @pytest.fixture
    def setup(self):
        """Create replayer with events"""
        router = WebhookRouter()
        handler = Mock()
        router.add_route(event_type="*", handler=handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add test events
            for i in range(3):
                store.store_event("test", {"event": "test", "event_id": f"evt_{i}"})

            replayer = EventReplayer(router, store)

            yield replayer, handler

    def test_replay_event_by_id_success(self, setup):
        """Test replaying event by ID"""
        replayer, handler = setup

        success = replayer.replay_event_by_id("evt_1")

        assert success is True
        handler.assert_called_once()

    def test_replay_event_by_id_not_found(self, setup):
        """Test replaying non-existent event"""
        replayer, handler = setup

        success = replayer.replay_event_by_id("evt_nonexistent")

        assert success is False
        handler.assert_not_called()

    def test_replay_event_by_id_dry_run(self, setup):
        """Test dry run for specific event"""
        replayer, handler = setup

        success = replayer.replay_event_by_id("evt_1", dry_run=True)

        assert success is True
        handler.assert_not_called()


class TestEventReplayerReplayWithFilter:
    """Test replaying with custom filter"""

    @pytest.fixture
    def setup(self):
        """Create replayer with events"""
        router = WebhookRouter()
        handler = Mock()
        router.add_route(event_type="*", handler=handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add events with different data
            for i in range(5):
                payload = {
                    "event": "test",
                    "event_id": f"evt_{i}",
                    "data": {"candidacy_id": f"cand_{i % 2}"},  # Only 2 unique IDs
                }
                store.store_event("test", payload)

            replayer = EventReplayer(router, store)

            yield replayer, handler

    def test_replay_with_filter(self, setup):
        """Test replaying with custom filter function"""
        replayer, handler = setup

        # Filter for candidacy_id = "cand_0"
        filter_func = lambda e: e["payload"]["data"]["candidacy_id"] == "cand_0"

        result = replayer.replay_with_filter(filter_func)

        # Should replay 3 events (indices 0, 2, 4)
        assert result["total"] == 3
        assert result["successful"] == 3

    def test_replay_with_filter_limit(self, setup):
        """Test filter replay with limit"""
        replayer, handler = setup

        filter_func = lambda e: True  # Match all

        result = replayer.replay_with_filter(filter_func, limit=2)

        assert result["total"] == 2

    def test_replay_with_filter_dry_run(self, setup):
        """Test filter replay dry run"""
        replayer, handler = setup

        filter_func = lambda e: True

        result = replayer.replay_with_filter(filter_func, dry_run=True)

        assert result["skipped"] == 5
        handler.assert_not_called()


class TestEventReplayerStats:
    """Test replay statistics"""

    @pytest.fixture
    def setup(self):
        """Create replayer with events"""
        router = WebhookRouter()

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add events
            for i in range(3):
                store.store_event("test", {"event": "test", "event_id": f"evt_{i}"})

            for i in range(2):
                store.store_event(
                    "test",
                    {"event": "test", "event_id": f"evt_failed_{i}"},
                    status="failed",
                )

            replayer = EventReplayer(router, store)

            yield replayer

    def test_get_replay_stats(self, setup):
        """Test getting replay statistics"""
        replayer = setup

        stats = replayer.get_replay_stats()

        assert "storage" in stats
        assert "router" in stats
        assert stats["replayable_events"] == 3
        assert stats["failed_in_storage"] == 2


class TestEventReplayerErrorHandling:
    """Test error handling in replay"""

    @pytest.fixture
    def setup(self):
        """Create replayer with failing handler"""
        router = WebhookRouter()
        handler = Mock(side_effect=Exception("Handler error"))
        router.add_route(event_type="*", handler=handler, max_retries=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))

            # Add events
            for i in range(3):
                store.store_event("test", {"event": "test", "event_id": f"evt_{i}"})

            replayer = EventReplayer(router, store)

            yield replayer, handler

    def test_replay_with_handler_failures(self, setup):
        """Test replay continues on handler failures"""
        replayer, handler = setup

        result = replayer.replay_events()

        # Router handles failures internally, so all events are "successfully replayed"
        # (i.e., successfully routed through the router, even if handlers fail)
        assert result["total"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0

        # But the router should track the failed handlers
        assert replayer.router.failed_count == 3
        assert handler.call_count == 3


class TestEventReplayerIntegration:
    """Integration tests for event replay"""

    @pytest.fixture
    def setup(self):
        """Create complete replay setup"""
        router = WebhookRouter()
        results = []

        def capture_handler(payload):
            results.append(payload["event_id"])

        router.add_route(event_type="candidacy.created", handler=capture_handler)

        with tempfile.TemporaryDirectory() as tmpdir:
            store = EventStore(storage_path=str(Path(tmpdir) / ".webhook_events"))
            replayer = EventReplayer(router, store)

            yield replayer, store, results

    def test_end_to_end_replay(self, setup):
        """Test complete event storage and replay workflow"""
        replayer, store, results = setup

        # Store events
        for i in range(3):
            payload = {
                "event": "candidacy.created",
                "event_id": f"evt_{i}",
                "data": {},
            }
            store.store_event("candidacy.created", payload)

        # Replay all events
        result = replayer.replay_events()

        assert result["total"] == 3
        assert result["successful"] == 3
        assert len(results) == 3
        assert results == ["evt_0", "evt_1", "evt_2"]

    def test_selective_replay_workflow(self, setup):
        """Test selective replay workflow"""
        replayer, store, results = setup

        # Store mixed event types
        for i in range(2):
            store.store_event(
                "candidacy.created",
                {
                    "event": "candidacy.created",
                    "event_id": f"evt_created_{i}",
                    "data": {},
                },
            )

        for i in range(2):
            store.store_event(
                "candidacy.updated",
                {
                    "event": "candidacy.updated",
                    "event_id": f"evt_updated_{i}",
                    "data": {},
                },
            )

        # Replay only candidacy.created events
        result = replayer.replay_events(event_type="candidacy.created")

        assert result["total"] == 2
        assert len(results) == 2  # Handler only registered for candidacy.created
