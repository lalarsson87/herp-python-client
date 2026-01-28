"""
Tests for HERP Event Store
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.core.herp.events.event_store import (
    EventStore,
    EventSubscriber,
    FileEventStore,
    InMemoryEventStore,
)
from src.core.herp.events.events import (
    CandidacyCreated,
    CandidacyStepChanged,
    ContactAdded,
    Event,
)


class TestInMemoryEventStore:
    """Test InMemoryEventStore implementation"""

    @pytest.fixture
    def store(self):
        """Create fresh event store"""
        return InMemoryEventStore()

    def test_initialization(self, store):
        """Test store initialization"""
        assert store.count() == 0
        assert store.events == []
        assert store.events_by_aggregate == {}
        assert store.events_by_type == {}

    def test_append_single_event(self, store):
        """Test appending single event"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123", name="Alice", email="alice@example.com"
        )

        store.append(event)

        assert store.count() == 1
        assert event in store.events
        assert event in store.events_by_aggregate["cand_123"]
        assert event in store.events_by_type["CandidacyCreated"]

    def test_append_multiple_events(self, store):
        """Test appending multiple events"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyCreated.create(candidacy_id="cand_2", name="Bob")
        event3 = CandidacyStepChanged.create(
            candidacy_id="cand_1", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        assert store.count() == 3

    def test_load_events_by_aggregate_id(self, store):
        """Test loading events for specific aggregate"""
        event1 = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )
        event3 = CandidacyCreated.create(candidacy_id="cand_456", name="Bob")

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_events("cand_123")

        assert len(events) == 2
        assert event1 in events
        assert event2 in events
        assert event3 not in events

    def test_load_events_nonexistent_aggregate(self, store):
        """Test loading events for nonexistent aggregate"""
        events = store.load_events("nonexistent")

        assert events == []

    def test_load_events_chronological_order(self, store):
        """Test events are returned in chronological order"""
        # Create events with different timestamps
        event1 = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )

        # Append in reverse order
        store.append(event2)
        store.append(event1)

        events = store.load_events("cand_123")

        # Should be returned in chronological order
        assert events[0].timestamp <= events[1].timestamp

    def test_load_events_from_version(self, store):
        """Test loading events from specific version"""
        event1 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            data={},
            version=1,
        )
        event2 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            data={},
            version=2,
        )
        event3 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            data={},
            version=3,
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_events("agg_1", from_version=2)

        assert len(events) == 2
        assert event1 not in events
        assert event2 in events
        assert event3 in events

    def test_load_events_by_type(self, store):
        """Test loading events by type"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyCreated.create(candidacy_id="cand_2", name="Bob")
        event3 = CandidacyStepChanged.create(
            candidacy_id="cand_1", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        created_events = store.load_events_by_type("CandidacyCreated")

        assert len(created_events) == 2
        assert event1 in created_events
        assert event2 in created_events
        assert event3 not in created_events

    def test_load_events_by_type_with_timestamp_filter(self, store):
        """Test loading events by type with timestamp filtering"""
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        event1 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            timestamp=past,
            data={},
        )
        event2 = Event(
            event_type="Test",
            aggregate_id="agg_2",
            timestamp=now,
            data={},
        )
        event3 = Event(
            event_type="Test",
            aggregate_id="agg_3",
            timestamp=future,
            data={},
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        # Load events from now onwards
        events = store.load_events_by_type("Test", from_timestamp=now)

        assert len(events) == 2
        assert event1 not in events
        assert event2 in events
        assert event3 in events

    def test_load_events_by_type_with_time_range(self, store):
        """Test loading events by type with time range"""
        now = datetime.now()
        past = now - timedelta(hours=2)
        recent = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        event1 = Event(event_type="Test", aggregate_id="agg_1", timestamp=past, data={})
        event2 = Event(
            event_type="Test", aggregate_id="agg_2", timestamp=recent, data={}
        )
        event3 = Event(
            event_type="Test", aggregate_id="agg_3", timestamp=future, data={}
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        # Load events in time range
        events = store.load_events_by_type(
            "Test", from_timestamp=recent, to_timestamp=now
        )

        assert len(events) == 1
        assert event2 in events

    def test_load_all_events(self, store):
        """Test loading all events"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_1", from_step="app", to_step="screen"
        )
        event3 = ContactAdded.create(
            candidacy_id="cand_2", contact_id="contact_1", contact_type="interview"
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        all_events = store.load_all_events()

        assert len(all_events) == 3

    def test_load_all_events_with_timestamp_filter(self, store):
        """Test loading all events with timestamp filtering"""
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        event1 = Event(
            event_type="Test1", aggregate_id="agg_1", timestamp=past, data={}
        )
        event2 = Event(event_type="Test2", aggregate_id="agg_2", timestamp=now, data={})
        event3 = Event(
            event_type="Test3", aggregate_id="agg_3", timestamp=future, data={}
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_all_events(from_timestamp=now)

        assert len(events) == 2

    def test_clear(self, store):
        """Test clearing all events"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyCreated.create(candidacy_id="cand_2", name="Bob")

        store.append(event1)
        store.append(event2)

        assert store.count() == 2

        store.clear()

        assert store.count() == 0
        assert store.events == []
        assert store.events_by_aggregate == {}
        assert store.events_by_type == {}

    def test_count_by_aggregate(self, store):
        """Test counting events by aggregate"""
        event1 = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )
        event3 = CandidacyCreated.create(candidacy_id="cand_456", name="Bob")

        store.append(event1)
        store.append(event2)
        store.append(event3)

        assert store.count_by_aggregate("cand_123") == 2
        assert store.count_by_aggregate("cand_456") == 1
        assert store.count_by_aggregate("nonexistent") == 0


class TestFileEventStore:
    """Test FileEventStore implementation"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield tmp_dir

    @pytest.fixture
    def store(self, temp_dir):
        """Create file event store"""
        return FileEventStore(temp_dir)

    def test_initialization(self, temp_dir):
        """Test store initialization creates directory"""
        store = FileEventStore(temp_dir)

        assert store.base_path.exists()
        assert store.base_path.is_dir()

    def test_append_creates_file(self, store):
        """Test appending creates JSON file"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123", name="Alice", email="alice@example.com"
        )

        store.append(event)

        # Check file exists
        event_file = store.base_path / "cand_123" / f"{event.event_id}.json"
        assert event_file.exists()

        # Check file content
        with open(event_file) as f:
            data = json.load(f)
            assert data["event_type"] == "CandidacyCreated"
            assert data["aggregate_id"] == "cand_123"

    def test_append_creates_aggregate_directory(self, store):
        """Test appending creates aggregate directory"""
        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")

        store.append(event)

        aggregate_dir = store.base_path / "cand_123"
        assert aggregate_dir.exists()
        assert aggregate_dir.is_dir()

    def test_load_events_from_files(self, store):
        """Test loading events from files"""
        event1 = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)

        # Load events
        events = store.load_events("cand_123")

        assert len(events) == 2
        # Events should be loaded (though as base Event class)
        assert events[0].event_type in ["CandidacyCreated", "CandidacyStepChanged"]

    def test_load_events_nonexistent_aggregate(self, store):
        """Test loading events for nonexistent aggregate"""
        events = store.load_events("nonexistent")

        assert events == []

    def test_load_events_from_version(self, store):
        """Test loading events from specific version"""
        event1 = Event(event_type="Test", aggregate_id="agg_1", data={}, version=1)
        event2 = Event(event_type="Test", aggregate_id="agg_1", data={}, version=2)
        event3 = Event(event_type="Test", aggregate_id="agg_1", data={}, version=3)

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_events("agg_1", from_version=2)

        assert len(events) == 2

    def test_load_events_by_type(self, store):
        """Test loading events by type from files"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyCreated.create(candidacy_id="cand_2", name="Bob")
        event3 = CandidacyStepChanged.create(
            candidacy_id="cand_1", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        created_events = store.load_events_by_type("CandidacyCreated")

        assert len(created_events) == 2

    def test_load_events_by_type_with_timestamp_filter(self, store):
        """Test loading events by type with timestamp filtering"""
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        event1 = Event(event_type="Test", aggregate_id="agg_1", timestamp=past, data={})
        event2 = Event(event_type="Test", aggregate_id="agg_2", timestamp=now, data={})
        event3 = Event(
            event_type="Test", aggregate_id="agg_3", timestamp=future, data={}
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_events_by_type("Test", from_timestamp=now)

        assert len(events) == 2

    def test_load_all_events_from_files(self, store):
        """Test loading all events from files"""
        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_2", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)

        all_events = store.load_all_events()

        assert len(all_events) == 2

    def test_load_all_events_with_timestamp_filter(self, store):
        """Test loading all events with timestamp filtering"""
        now = datetime.now()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)

        event1 = Event(
            event_type="Test1", aggregate_id="agg_1", timestamp=past, data={}
        )
        event2 = Event(event_type="Test2", aggregate_id="agg_2", timestamp=now, data={})
        event3 = Event(
            event_type="Test3", aggregate_id="agg_3", timestamp=future, data={}
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        events = store.load_all_events(from_timestamp=now, to_timestamp=future)

        assert len(events) == 2

    def test_event_file_structure(self, store):
        """Test event file structure"""
        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")

        store.append(event)

        # Check directory structure
        assert (store.base_path / "cand_123").exists()
        assert (store.base_path / "cand_123" / f"{event.event_id}.json").exists()

        # Check JSON structure
        event_file = store.base_path / "cand_123" / f"{event.event_id}.json"
        with open(event_file) as f:
            data = json.load(f)

        assert "event_id" in data
        assert "event_type" in data
        assert "aggregate_id" in data
        assert "timestamp" in data
        assert "data" in data
        assert "metadata" in data
        assert "version" in data


class TestEventSubscriber:
    """Test EventSubscriber implementation"""

    @pytest.fixture
    def store(self):
        """Create event store"""
        return InMemoryEventStore()

    @pytest.fixture
    def subscriber(self, store):
        """Create event subscriber"""
        return EventSubscriber(store)

    def test_initialization(self, subscriber, store):
        """Test subscriber initialization"""
        assert subscriber.event_store == store
        assert subscriber.subscribers == {}
        assert subscriber.all_subscribers == []

    def test_subscribe_to_event_type(self, subscriber):
        """Test subscribing to specific event type"""
        called = []

        def handler(event):
            called.append(event)

        subscriber.subscribe("CandidacyCreated", handler)

        assert "CandidacyCreated" in subscriber.subscribers
        assert handler in subscriber.subscribers["CandidacyCreated"]

    def test_subscribe_all(self, subscriber):
        """Test subscribing to all events"""
        called = []

        def handler(event):
            called.append(event)

        subscriber.subscribe_all(handler)

        assert handler in subscriber.all_subscribers

    def test_notification_on_append(self, subscriber, store):
        """Test subscribers are notified on event append"""
        called = []

        def handler(event):
            called.append(event)

        subscriber.subscribe("CandidacyCreated", handler)

        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        store.append(event)

        assert len(called) == 1
        assert called[0] == event

    def test_notification_type_specific(self, subscriber, store):
        """Test only subscribed event types trigger handler"""
        created_called = []
        changed_called = []

        def created_handler(event):
            created_called.append(event)

        def changed_handler(event):
            changed_called.append(event)

        subscriber.subscribe("CandidacyCreated", created_handler)
        subscriber.subscribe("CandidacyStepChanged", changed_handler)

        event1 = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_123", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)

        assert len(created_called) == 1
        assert len(changed_called) == 1

    def test_notification_all_subscribers(self, subscriber, store):
        """Test all-event subscribers receive all events"""
        called = []

        def handler(event):
            called.append(event)

        subscriber.subscribe_all(handler)

        event1 = CandidacyCreated.create(candidacy_id="cand_1", name="Alice")
        event2 = CandidacyStepChanged.create(
            candidacy_id="cand_1", from_step="app", to_step="screen"
        )

        store.append(event1)
        store.append(event2)

        assert len(called) == 2

    def test_multiple_subscribers_same_type(self, subscriber, store):
        """Test multiple subscribers for same event type"""
        called1 = []
        called2 = []

        def handler1(event):
            called1.append(event)

        def handler2(event):
            called2.append(event)

        subscriber.subscribe("CandidacyCreated", handler1)
        subscriber.subscribe("CandidacyCreated", handler2)

        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        store.append(event)

        assert len(called1) == 1
        assert len(called2) == 1

    def test_handler_exception_doesnt_break_other_handlers(self, subscriber, store):
        """Test exception in one handler doesn't affect others"""
        called = []

        def failing_handler(event):
            raise ValueError("Test error")

        def working_handler(event):
            called.append(event)

        subscriber.subscribe("CandidacyCreated", failing_handler)
        subscriber.subscribe("CandidacyCreated", working_handler)

        event = CandidacyCreated.create(candidacy_id="cand_123", name="Alice")
        store.append(event)

        # Working handler should still be called despite failing handler
        assert len(called) == 1


class TestEventStoreInterface:
    """Test EventStore abstract interface"""

    def test_event_store_is_abstract(self):
        """Test EventStore is abstract and can't be instantiated"""
        with pytest.raises(TypeError):
            EventStore()  # type: ignore

    def test_inmemory_implements_interface(self):
        """Test InMemoryEventStore implements EventStore interface"""
        store = InMemoryEventStore()

        assert isinstance(store, EventStore)
        assert hasattr(store, "append")
        assert hasattr(store, "load_events")
        assert hasattr(store, "load_events_by_type")
        assert hasattr(store, "load_all_events")

    def test_file_implements_interface(self):
        """Test FileEventStore implements EventStore interface"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = FileEventStore(tmp_dir)

            assert isinstance(store, EventStore)
            assert hasattr(store, "append")
            assert hasattr(store, "load_events")
            assert hasattr(store, "load_events_by_type")
            assert hasattr(store, "load_all_events")
