#!/usr/bin/env python3
"""
HERP Event Store

Provides storage and retrieval of events.

Supports:
- Appending events
- Loading events by aggregate ID
- Loading events by event type
- Time-based queries
- Event snapshots for performance
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from ...utils.logging import get_logger
from .events import Event

logger = get_logger(__name__)


class EventStore(ABC):
    """
    Abstract event store interface

    Implementations can use different storage backends:
    - In-memory (for testing)
    - File-based (SQLite, JSON files)
    - Database (PostgreSQL, MySQL)
    - Event streaming (Kafka, Kinesis)
    """

    @abstractmethod
    def append(self, event: Event) -> None:
        """
        Append event to store

        Args:
            event: Event to append

        Note:
            Events are immutable and append-only
        """
        pass

    @abstractmethod
    def load_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """
        Load all events for an aggregate

        Args:
            aggregate_id: Aggregate ID (e.g., candidacy_id)
            from_version: Load events from this version onwards

        Returns:
            List of events in chronological order
        """
        pass

    @abstractmethod
    def load_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Load events by type

        Args:
            event_type: Type of event
            from_timestamp: Load events from this timestamp
            to_timestamp: Load events until this timestamp

        Returns:
            List of events matching criteria
        """
        pass

    @abstractmethod
    def load_all_events(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """
        Load all events

        Args:
            from_timestamp: Load events from this timestamp
            to_timestamp: Load events until this timestamp

        Returns:
            List of all events in chronological order
        """
        pass


class InMemoryEventStore(EventStore):
    """
    In-memory event store for testing and development

    Events are stored in memory and lost on process restart.
    Not suitable for production use.

    Usage:
        store = InMemoryEventStore()
        store.append(event)
        events = store.load_events("candidacy_123")
    """

    def __init__(self):
        """Initialize in-memory event store"""
        self.events: List[Event] = []
        self.events_by_aggregate: Dict[str, List[Event]] = {}
        self.events_by_type: Dict[str, List[Event]] = {}

    def append(self, event: Event) -> None:
        """Append event to store"""
        # Add to main list
        self.events.append(event)

        # Index by aggregate
        if event.aggregate_id not in self.events_by_aggregate:
            self.events_by_aggregate[event.aggregate_id] = []
        self.events_by_aggregate[event.aggregate_id].append(event)

        # Index by type
        if event.event_type not in self.events_by_type:
            self.events_by_type[event.event_type] = []
        self.events_by_type[event.event_type].append(event)

        logger.debug(f"Appended event: {event.event_type} for {event.aggregate_id}")

    def load_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Load all events for an aggregate"""
        events = self.events_by_aggregate.get(aggregate_id, [])

        if from_version > 0:
            events = [e for e in events if e.version >= from_version]

        return sorted(events, key=lambda e: e.timestamp)

    def load_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """Load events by type"""
        events = self.events_by_type.get(event_type, [])

        # Filter by timestamp
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]

        return sorted(events, key=lambda e: e.timestamp)

    def load_all_events(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """Load all events"""
        events = self.events.copy()

        # Filter by timestamp
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]

        return sorted(events, key=lambda e: e.timestamp)

    def clear(self) -> None:
        """Clear all events (for testing)"""
        self.events.clear()
        self.events_by_aggregate.clear()
        self.events_by_type.clear()

    def count(self) -> int:
        """Get total event count"""
        return len(self.events)

    def count_by_aggregate(self, aggregate_id: str) -> int:
        """Get event count for aggregate"""
        return len(self.events_by_aggregate.get(aggregate_id, []))


class FileEventStore(EventStore):
    """
    File-based event store using JSON

    Events are stored as JSON files in a directory structure:
    - events/{aggregate_id}/{event_id}.json

    Suitable for development and small-scale production use.

    Usage:
        store = FileEventStore("/path/to/events")
        store.append(event)
        events = store.load_events("candidacy_123")
    """

    def __init__(self, base_path: str):
        """
        Initialize file event store

        Args:
            base_path: Base directory for event storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def append(self, event: Event) -> None:
        """Append event to file storage"""
        # Create aggregate directory
        aggregate_dir = self.base_path / event.aggregate_id
        aggregate_dir.mkdir(parents=True, exist_ok=True)

        # Write event to file
        event_file = aggregate_dir / f"{event.event_id}.json"
        with open(event_file, "w") as f:
            json.dump(event.to_dict(), f, indent=2)

        logger.debug(f"Wrote event to file: {event_file}")

    def load_events(self, aggregate_id: str, from_version: int = 0) -> List[Event]:
        """Load all events for an aggregate from files"""
        aggregate_dir = self.base_path / aggregate_id

        if not aggregate_dir.exists():
            return []

        # Load all event files
        events = []
        for event_file in aggregate_dir.glob("*.json"):
            with open(event_file) as f:
                event_data = json.load(f)
                event = Event.from_dict(event_data)

                if event.version >= from_version:
                    events.append(event)

        return sorted(events, key=lambda e: e.timestamp)

    def load_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """Load events by type (scans all files)"""
        events = []

        # Scan all aggregate directories
        for aggregate_dir in self.base_path.iterdir():
            if not aggregate_dir.is_dir():
                continue

            # Load events from this aggregate
            for event_file in aggregate_dir.glob("*.json"):
                with open(event_file) as f:
                    event_data = json.load(f)

                    # Filter by type
                    if event_data["event_type"] != event_type:
                        continue

                    event = Event.from_dict(event_data)

                    # Filter by timestamp
                    if from_timestamp and event.timestamp < from_timestamp:
                        continue
                    if to_timestamp and event.timestamp > to_timestamp:
                        continue

                    events.append(event)

        return sorted(events, key=lambda e: e.timestamp)

    def load_all_events(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
    ) -> List[Event]:
        """Load all events from files"""
        events = []

        # Scan all aggregate directories
        for aggregate_dir in self.base_path.iterdir():
            if not aggregate_dir.is_dir():
                continue

            # Load events from this aggregate
            for event_file in aggregate_dir.glob("*.json"):
                with open(event_file) as f:
                    event_data = json.load(f)
                    event = Event.from_dict(event_data)

                    # Filter by timestamp
                    if from_timestamp and event.timestamp < from_timestamp:
                        continue
                    if to_timestamp and event.timestamp > to_timestamp:
                        continue

                    events.append(event)

        return sorted(events, key=lambda e: e.timestamp)


class EventSubscriber:
    """
    Event subscriber for real-time event notifications

    Allows subscribing to events and getting notified when they're appended.

    Usage:
        subscriber = EventSubscriber(event_store)
        subscriber.subscribe("CandidacyCreated", lambda event: print(event))
        subscriber.subscribe_all(lambda event: handle_event(event))
    """

    def __init__(self, event_store: EventStore):
        """
        Initialize event subscriber

        Args:
            event_store: Event store to subscribe to
        """
        self.event_store = event_store
        self.subscribers: Dict[str, List[Callable]] = {}
        self.all_subscribers: List[Callable] = []

        # Wrap append method to notify subscribers
        original_append = event_store.append

        def append_with_notification(event: Event) -> None:
            original_append(event)
            self._notify(event)

        event_store.append = append_with_notification

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to specific event type

        Args:
            event_type: Event type to subscribe to
            handler: Function to call when event occurs
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to all events

        Args:
            handler: Function to call for all events
        """
        self.all_subscribers.append(handler)

    def _notify(self, event: Event) -> None:
        """Notify subscribers of new event"""
        # Notify type-specific subscribers
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

        # Notify all-event subscribers
        for handler in self.all_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
