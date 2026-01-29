"""
Tests for HERP Event Store

Tests for event storage, retrieval, and subscription mechanisms.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

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
    CandidacyTerminated,
    Event,
)


class TestInMemoryEventStore:
    """Test InMemoryEventStore implementation"""

    @pytest.fixture
    def store(self):
        """Create fresh in-memory store for each test"""
        return InMemoryEventStore()

    @pytest.fixture
    def sample_events(self):
        """Create sample events for testing"""
        base_time = datetime(2026, 1, 29, 10, 0, 0)

        return [
            CandidacyCreated.create(
                candidacy_id="cand_1",
                name="John Doe",
                email="john@example.com",
            ),
            CandidacyStepChanged.create(
                candidacy_id="cand_1",
                from_step="application",
                to_step="screening",
            ),
            CandidacyCreated.create(
                candidacy_id="cand_2",
                name="Jane Smith",
                email="jane@example.com",
            ),
        ]

    def test_store_initialization(self, store):
        """Test store initializes with empty state"""
        assert isinstance(store, EventStore)
        assert store.count() == 0
        assert store.events == []
        assert store.events_by_aggregate == {}
        assert store.events_by_type == {}

    def test_append_single_event(self, store):
        """Test appending single event"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="Test User",
        )

        store.append(event)

        assert store.count() == 1
        assert event in store.events

    def test_append_multiple_events(self, store, sample_events):
        """Test appending multiple events"""
        for event in sample_events:
            store.append(event)

        assert store.count() == 3
        assert len(store.events) == 3

    def test_events_indexed_by_aggregate(self, store, sample_events):
        """Test events are indexed by aggregate ID"""
        for event in sample_events:
            store.append(event)

        # cand_1 has 2 events
        cand_1_events = store.events_by_aggregate["cand_1"]
        assert len(cand_1_events) == 2
        assert all(e.aggregate_id == "cand_1" for e in cand_1_events)

        # cand_2 has 1 event
        cand_2_events = store.events_by_aggregate["cand_2"]
        assert len(cand_2_events) == 1
        assert cand_2_events[0].aggregate_id == "cand_2"

    def test_events_indexed_by_type(self, store, sample_events):
        """Test events are indexed by event type"""
        for event in sample_events:
            store.append(event)

        # CandidacyCreated has 2 events
        created_events = store.events_by_type["CandidacyCreated"]
        assert len(created_events) == 2

        # CandidacyStepChanged has 1 event
        step_changed_events = store.events_by_type["CandidacyStepChanged"]
        assert len(step_changed_events) == 1

    def test_load_events_for_aggregate(self, store, sample_events):
        """Test loading events for specific aggregate"""
        for event in sample_events:
            store.append(event)

        events = store.load_events("cand_1")

        assert len(events) == 2
        assert all(e.aggregate_id == "cand_1" for e in events)
        # Events should be sorted by timestamp
        assert events[0].timestamp <= events[1].timestamp

    def test_load_events_for_nonexistent_aggregate(self, store):
        """Test loading events for aggregate with no events"""
        events = store.load_events("nonexistent_aggregate")

        assert events == []

    def test_load_events_with_version_filter(self, store):
        """Test loading events from specific version"""
        # Create events with different versions
        event1 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            version=1,
            timestamp=datetime(2026, 1, 29, 10, 0, 0),
        )
        event2 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            version=2,
            timestamp=datetime(2026, 1, 29, 10, 1, 0),
        )
        event3 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            version=3,
            timestamp=datetime(2026, 1, 29, 10, 2, 0),
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        # Load from version 2
        events = store.load_events("agg_1", from_version=2)

        assert len(events) == 2
        assert events[0].version == 2
        assert events[1].version == 3

    def test_load_events_by_type(self, store, sample_events):
        """Test loading events by type"""
        for event in sample_events:
            store.append(event)

        events = store.load_events_by_type("CandidacyCreated")

        assert len(events) == 2
        assert all(e.event_type == "CandidacyCreated" for e in events)

    def test_load_events_by_type_with_timestamp_filter(self, store):
        """Test loading events by type with timestamp filters"""
        base_time = datetime(2026, 1, 29, 10, 0, 0)

        event1 = CandidacyCreated.create(candidacy_id="c1", name="User 1")
        event1 = Event(
            event_id=event1.event_id,
            event_type=event1.event_type,
            aggregate_id=event1.aggregate_id,
            timestamp=base_time,
            data=event1.data,
            metadata=event1.metadata,
        )

        event2 = CandidacyCreated.create(candidacy_id="c2", name="User 2")
        event2 = Event(
            event_id=event2.event_id,
            event_type=event2.event_type,
            aggregate_id=event2.aggregate_id,
            timestamp=base_time + timedelta(hours=1),
            data=event2.data,
            metadata=event2.metadata,
        )

        event3 = CandidacyCreated.create(candidacy_id="c3", name="User 3")
        event3 = Event(
            event_id=event3.event_id,
            event_type=event3.event_type,
            aggregate_id=event3.aggregate_id,
            timestamp=base_time + timedelta(hours=2),
            data=event3.data,
            metadata=event3.metadata,
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        # Load events from 1 hour onwards
        events = store.load_events_by_type(
            "CandidacyCreated",
            from_timestamp=base_time + timedelta(hours=1),
        )

        assert len(events) == 2
        assert events[0].aggregate_id == "c2"
        assert events[1].aggregate_id == "c3"

        # Load events up to 1 hour
        events = store.load_events_by_type(
            "CandidacyCreated",
            to_timestamp=base_time + timedelta(hours=1),
        )

        assert len(events) == 2
        assert events[0].aggregate_id == "c1"
        assert events[1].aggregate_id == "c2"

    def test_load_all_events(self, store, sample_events):
        """Test loading all events"""
        for event in sample_events:
            store.append(event)

        events = store.load_all_events()

        assert len(events) == 3
        # Events should be sorted by timestamp
        for i in range(len(events) - 1):
            assert events[i].timestamp <= events[i + 1].timestamp

    def test_load_all_events_with_timestamp_filter(self, store):
        """Test loading all events with timestamp filters"""
        base_time = datetime(2026, 1, 29, 10, 0, 0)

        event1 = Event(
            event_type="Test1",
            aggregate_id="a1",
            timestamp=base_time,
        )
        event2 = Event(
            event_type="Test2",
            aggregate_id="a2",
            timestamp=base_time + timedelta(hours=1),
        )
        event3 = Event(
            event_type="Test3",
            aggregate_id="a3",
            timestamp=base_time + timedelta(hours=2),
        )

        store.append(event1)
        store.append(event2)
        store.append(event3)

        # Load events in middle hour
        events = store.load_all_events(
            from_timestamp=base_time + timedelta(minutes=30),
            to_timestamp=base_time + timedelta(hours=1, minutes=30),
        )

        assert len(events) == 1
        assert events[0].event_type == "Test2"

    def test_clear_store(self, store, sample_events):
        """Test clearing all events from store"""
        for event in sample_events:
            store.append(event)

        assert store.count() == 3

        store.clear()

        assert store.count() == 0
        assert store.events == []
        assert store.events_by_aggregate == {}
        assert store.events_by_type == {}

    def test_count_by_aggregate(self, store, sample_events):
        """Test counting events by aggregate"""
        for event in sample_events:
            store.append(event)

        assert store.count_by_aggregate("cand_1") == 2
        assert store.count_by_aggregate("cand_2") == 1
        assert store.count_by_aggregate("nonexistent") == 0


class TestFileEventStore:
    """Test FileEventStore implementation"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for file storage"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def store(self, temp_dir):
        """Create file-based event store"""
        return FileEventStore(temp_dir)

    def test_store_initialization_creates_directory(self, temp_dir):
        """Test store creates base directory"""
        store = FileEventStore(temp_dir)

        assert Path(temp_dir).exists()
        assert Path(temp_dir).is_dir()

    def test_append_event_creates_file(self, store, temp_dir):
        """Test appending event creates JSON file"""
        event = CandidacyCreated.create(
            candidacy_id="cand_123",
            name="Test User",
        )

        store.append(event)

        # Check aggregate directory created
        aggregate_dir = Path(temp_dir) / "cand_123"
        assert aggregate_dir.exists()

        # Check event file created
        event_file = aggregate_dir / f"{event.event_id}.json"
        assert event_file.exists()

        # Verify file contents
        with open(event_file) as f:
            data = json.load(f)
            assert data["event_type"] == "CandidacyCreated"
            assert data["aggregate_id"] == "cand_123"

    def test_load_events_from_files(self, store):
        """Test loading events from JSON files"""
        event1 = CandidacyCreated.create("cand_1", "User 1")
        event2 = CandidacyStepChanged.create("cand_1", "app", "interview")

        store.append(event1)
        store.append(event2)

        events = store.load_events("cand_1")

        assert len(events) == 2
        assert events[0].event_type in ["CandidacyCreated", "CandidacyStepChanged"]
        assert events[1].event_type in ["CandidacyCreated", "CandidacyStepChanged"]

    def test_load_events_for_nonexistent_aggregate(self, store):
        """Test loading events for aggregate with no events"""
        events = store.load_events("nonexistent")

        assert events == []

    def test_load_events_with_version_filter(self, store):
        """Test loading events from specific version"""
        event1 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            version=1,
            timestamp=datetime(2026, 1, 29, 10, 0, 0),
        )
        event2 = Event(
            event_type="Test",
            aggregate_id="agg_1",
            version=2,
            timestamp=datetime(2026, 1, 29, 10, 1, 0),
        )

        store.append(event1)
        store.append(event2)

        events = store.load_events("agg_1", from_version=2)

        assert len(events) == 1
        assert events[0].version == 2

    def test_load_events_by_type(self, store):
        """Test loading events by type across aggregates"""
        store.append(CandidacyCreated.create("cand_1", "User 1"))
        store.append(CandidacyStepChanged.create("cand_1", "a", "b"))
        store.append(CandidacyCreated.create("cand_2", "User 2"))

        events = store.load_events_by_type("CandidacyCreated")

        assert len(events) == 2
        assert all(e.event_type == "CandidacyCreated" for e in events)

    def test_load_all_events(self, store):
        """Test loading all events from all aggregates"""
        store.append(CandidacyCreated.create("cand_1", "User 1"))
        store.append(CandidacyCreated.create("cand_2", "User 2"))
        store.append(CandidacyStepChanged.create("cand_1", "a", "b"))

        events = store.load_all_events()

        assert len(events) == 3

    def test_events_persist_across_store_instances(self, temp_dir):
        """Test events persist when creating new store instance"""
        # Create store and append event
        store1 = FileEventStore(temp_dir)
        event = CandidacyCreated.create("cand_persist", "Persist User")
        store1.append(event)

        # Create new store instance
        store2 = FileEventStore(temp_dir)
        events = store2.load_events("cand_persist")

        assert len(events) == 1
        assert events[0].aggregate_id == "cand_persist"


class TestEventSubscriber:
    """Test EventSubscriber for event notifications"""

    @pytest.fixture
    def store(self):
        """Create in-memory store for testing"""
        return InMemoryEventStore()

    @pytest.fixture
    def subscriber(self, store):
        """Create event subscriber"""
        return EventSubscriber(store)

    def test_subscriber_initialization(self, subscriber, store):
        """Test subscriber initializes correctly"""
        assert subscriber.event_store == store
        assert subscriber.subscribers == {}
        assert subscriber.all_subscribers == []

    def test_subscribe_to_event_type(self, subscriber, store):
        """Test subscribing to specific event type"""
        handler = Mock()

        subscriber.subscribe("CandidacyCreated", handler)

        assert "CandidacyCreated" in subscriber.subscribers
        assert handler in subscriber.subscribers["CandidacyCreated"]

    def test_handler_called_on_matching_event(self, subscriber, store):
        """Test handler is called when matching event is appended"""
        handler = Mock()
        subscriber.subscribe("CandidacyCreated", handler)

        event = CandidacyCreated.create("cand_1", "Test User")
        store.append(event)

        handler.assert_called_once_with(event)

    def test_handler_not_called_on_non_matching_event(self, subscriber, store):
        """Test handler is not called for different event type"""
        handler = Mock()
        subscriber.subscribe("CandidacyCreated", handler)

        event = CandidacyStepChanged.create("cand_1", "a", "b")
        store.append(event)

        handler.assert_not_called()

    def test_multiple_handlers_for_same_event_type(self, subscriber, store):
        """Test multiple handlers can subscribe to same event type"""
        handler1 = Mock()
        handler2 = Mock()

        subscriber.subscribe("CandidacyCreated", handler1)
        subscriber.subscribe("CandidacyCreated", handler2)

        event = CandidacyCreated.create("cand_1", "Test")
        store.append(event)

        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_subscribe_all_events(self, subscriber, store):
        """Test subscribing to all events"""
        handler = Mock()

        subscriber.subscribe_all(handler)

        # Append different event types
        event1 = CandidacyCreated.create("cand_1", "User")
        event2 = CandidacyStepChanged.create("cand_1", "a", "b")

        store.append(event1)
        store.append(event2)

        assert handler.call_count == 2

    def test_handler_exceptions_are_caught(self, subscriber, store):
        """Test exceptions in handlers don't break event processing"""
        failing_handler = Mock(side_effect=Exception("Handler error"))
        successful_handler = Mock()

        subscriber.subscribe("CandidacyCreated", failing_handler)
        subscriber.subscribe("CandidacyCreated", successful_handler)

        event = CandidacyCreated.create("cand_1", "Test")

        # Should not raise exception
        store.append(event)

        # Both handlers should have been called
        failing_handler.assert_called_once()
        successful_handler.assert_called_once()

    def test_subscribe_all_with_type_specific_handlers(self, subscriber, store):
        """Test all-event and type-specific handlers work together"""
        all_handler = Mock()
        type_handler = Mock()

        subscriber.subscribe_all(all_handler)
        subscriber.subscribe("CandidacyCreated", type_handler)

        event = CandidacyCreated.create("cand_1", "Test")
        store.append(event)

        # Both should be called
        all_handler.assert_called_once()
        type_handler.assert_called_once()


class TestEventStoreIntegration:
    """Integration tests for event store usage patterns"""

    def test_complete_candidacy_workflow(self):
        """Test storing and loading complete candidacy workflow"""
        store = InMemoryEventStore()

        # Create candidacy
        created = CandidacyCreated.create(
            candidacy_id="cand_workflow",
            name="Workflow Test",
            email="test@example.com",
        )
        store.append(created)

        # Change step
        step_changed = CandidacyStepChanged.create(
            candidacy_id="cand_workflow",
            from_step="application",
            to_step="interview",
        )
        store.append(step_changed)

        # Terminate
        terminated = CandidacyTerminated.create(
            candidacy_id="cand_workflow",
            reason="hired",
        )
        store.append(terminated)

        # Load all events for this candidacy
        events = store.load_events("cand_workflow")

        assert len(events) == 3
        assert events[0].event_type == "CandidacyCreated"
        assert events[1].event_type == "CandidacyStepChanged"
        assert events[2].event_type == "CandidacyTerminated"

    def test_file_store_with_subscriber(self):
        """Test file store with event subscriber"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileEventStore(tmpdir)
            subscriber = EventSubscriber(store)

            handler = Mock()
            subscriber.subscribe("CandidacyCreated", handler)

            event = CandidacyCreated.create("cand_1", "Test")
            store.append(event)

            # Handler should be called
            handler.assert_called_once()

            # Event should be persisted
            events = store.load_events("cand_1")
            assert len(events) == 1

    def test_event_store_acts_as_audit_log(self):
        """Test event store provides complete audit trail"""
        store = InMemoryEventStore()

        # Multiple operations on same candidacy
        operations = [
            CandidacyCreated.create("cand_1", "User", user_id="recruiter_1"),
            CandidacyStepChanged.create(
                "cand_1", "app", "screen", user_id="recruiter_1"
            ),
            CandidacyStepChanged.create(
                "cand_1", "screen", "interview", user_id="recruiter_2"
            ),
            CandidacyTerminated.create("cand_1", "hired", user_id="manager_1"),
        ]

        for op in operations:
            store.append(op)

        # Can reconstruct full history
        history = store.load_events("cand_1")

        assert len(history) == 4
        # Can see who made each change
        assert history[0].metadata.get("user_id") == "recruiter_1"
        assert history[3].metadata.get("user_id") == "manager_1"
