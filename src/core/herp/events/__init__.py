"""
HERP Event Sourcing

Provides event sourcing capabilities for tracking candidacy changes as immutable events.

Components:
    - Event: Base event class
    - EventStore: Event storage and retrieval
    - EventSourcedCandidacy: Event-sourced candidacy aggregate
    - Projections: Event-to-state projections
"""

from .aggregate import EventSourcedCandidacy
from .event_store import EventStore, InMemoryEventStore
from .events import (
    AssignmentAdded,
    AssignmentRemoved,
    CandidacyCreated,
    CandidacyEvent,
    CandidacyStatusChanged,
    CandidacyStepChanged,
    CandidacyTerminated,
    ContactAdded,
    ContactUpdated,
    Event,
    FileUploaded,
    TimelineCommentAdded,
)
from .projections import (
    AuditLogProjection,
    CandidacyProjection,
    TimelineProjection,
)

__all__ = [
    # Events
    "Event",
    "CandidacyEvent",
    "CandidacyCreated",
    "CandidacyStepChanged",
    "CandidacyStatusChanged",
    "CandidacyTerminated",
    "ContactAdded",
    "ContactUpdated",
    "FileUploaded",
    "TimelineCommentAdded",
    "AssignmentAdded",
    "AssignmentRemoved",
    # Event Store
    "EventStore",
    "InMemoryEventStore",
    # Aggregate
    "EventSourcedCandidacy",
    # Projections
    "CandidacyProjection",
    "TimelineProjection",
    "AuditLogProjection",
]
