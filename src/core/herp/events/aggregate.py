#!/usr/bin/env python3
"""
HERP Event-Sourced Aggregate

Provides event-sourced candidacy aggregate that rebuilds state from events.

The aggregate:
- Stores no state itself, only events
- Rebuilds state by replaying events
- Ensures consistency through event ordering
- Enables temporal queries (state at any point in time)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .events import (
    Event,
    CandidacyCreated,
    CandidacyStepChanged,
    CandidacyStatusChanged,
    CandidacyTerminated,
    ContactAdded,
    ContactUpdated,
    FileUploaded,
    TimelineCommentAdded,
    AssignmentAdded,
    AssignmentRemoved,
)
from .event_store import EventStore
from ...utils.logging import get_logger


logger = get_logger(__name__)


class EventSourcedCandidacy:
    """
    Event-sourced candidacy aggregate

    Rebuilds candidacy state from events. State is not stored directly,
    but reconstructed by replaying events.

    Usage:
        # Create new candidacy
        candidacy = EventSourcedCandidacy.create(
            candidacy_id="cand_123",
            name="Jane Doe",
            email="jane@example.com",
            event_store=store
        )

        # Load existing candidacy
        candidacy = EventSourcedCandidacy.load("cand_123", event_store=store)

        # Get current state
        state = candidacy.get_state()

        # Get historical state
        state_at_time = candidacy.get_state_at(datetime(2026, 1, 15))

        # Apply changes
        candidacy.change_step("interview", user_id="user_456")
        candidacy.add_contact(contact_id="contact_789", ...)
    """

    def __init__(
        self,
        candidacy_id: str,
        event_store: EventStore,
        events: Optional[List[Event]] = None
    ):
        """
        Initialize event-sourced candidacy

        Args:
            candidacy_id: Candidacy ID
            event_store: Event store for persistence
            events: Initial events (optional)
        """
        self.candidacy_id = candidacy_id
        self.event_store = event_store
        self.uncommitted_events: List[Event] = []

        # Load events if provided, otherwise load from store
        if events is not None:
            self.events = events
        else:
            self.events = event_store.load_events(candidacy_id)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        name: str,
        email: Optional[str] = None,
        requisition_id: Optional[str] = None,
        step: str = "application",
        tags: Optional[List[str]] = None,
        event_store: Optional[EventStore] = None,
        user_id: Optional[str] = None,
    ) -> "EventSourcedCandidacy":
        """
        Create new candidacy

        Args:
            candidacy_id: Candidacy ID
            name: Candidate name
            email: Candidate email
            requisition_id: Job requisition ID
            step: Initial hiring step
            tags: Initial tags
            event_store: Event store (if provided, event is saved immediately)
            user_id: User creating the candidacy

        Returns:
            New EventSourcedCandidacy
        """
        event = CandidacyCreated.create(
            candidacy_id=candidacy_id,
            name=name,
            email=email,
            requisition_id=requisition_id,
            step=step,
            tags=tags,
            user_id=user_id,
        )

        candidacy = cls(candidacy_id, event_store or EventStore(), events=[])
        candidacy._apply_event(event)

        if event_store:
            candidacy.commit()

        return candidacy

    @classmethod
    def load(cls, candidacy_id: str, event_store: EventStore) -> "EventSourcedCandidacy":
        """
        Load candidacy from event store

        Args:
            candidacy_id: Candidacy ID
            event_store: Event store

        Returns:
            EventSourcedCandidacy with state reconstructed from events
        """
        return cls(candidacy_id, event_store)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current candidacy state

        Returns:
            Current state dictionary
        """
        return self._rebuild_state(self.events)

    def get_state_at(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Get candidacy state at specific point in time

        Args:
            timestamp: Point in time to get state

        Returns:
            State at that timestamp
        """
        events_until = [e for e in self.events if e.timestamp <= timestamp]
        return self._rebuild_state(events_until)

    def get_events(self) -> List[Event]:
        """Get all events for this candidacy"""
        return self.events.copy()

    def get_event_history(self) -> List[Dict[str, Any]]:
        """
        Get event history as list of dictionaries

        Returns:
            List of event dictionaries with timestamp, type, data
        """
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "data": event.data,
                "metadata": event.metadata,
            }
            for event in self.events
        ]

    def change_step(
        self,
        to_step: str,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Change hiring step

        Args:
            to_step: New step
            comment: Optional comment
            user_id: User making the change
        """
        current_state = self.get_state()
        from_step = current_state.get("step")

        event = CandidacyStepChanged.create(
            candidacy_id=self.candidacy_id,
            from_step=from_step,
            to_step=to_step,
            comment=comment,
            user_id=user_id,
        )

        self._apply_event(event)

    def change_status(
        self,
        to_status: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Change candidacy status

        Args:
            to_status: New status
            reason: Reason for change
            user_id: User making the change
        """
        current_state = self.get_state()
        from_status = current_state.get("status")

        event = CandidacyStatusChanged.create(
            candidacy_id=self.candidacy_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            user_id=user_id,
        )

        self._apply_event(event)

    def terminate(
        self,
        reason: str,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Terminate candidacy

        Args:
            reason: Termination reason
            comment: Optional comment
            user_id: User terminating
        """
        current_state = self.get_state()
        final_step = current_state.get("step")

        event = CandidacyTerminated.create(
            candidacy_id=self.candidacy_id,
            reason=reason,
            comment=comment,
            final_step=final_step,
            user_id=user_id,
        )

        self._apply_event(event)
        # Also change status to terminated
        self.change_status("terminated", reason=reason, user_id=user_id)

    def add_contact(
        self,
        contact_id: str,
        contact_type: str,
        scheduled_at: Optional[str] = None,
        interviewer_ids: Optional[List[str]] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Add contact/interview"""
        event = ContactAdded.create(
            candidacy_id=self.candidacy_id,
            contact_id=contact_id,
            contact_type=contact_type,
            scheduled_at=scheduled_at,
            interviewer_ids=interviewer_ids,
            title=title,
            user_id=user_id,
        )

        self._apply_event(event)

    def update_contact(
        self,
        contact_id: str,
        changes: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> None:
        """Update contact/interview"""
        event = ContactUpdated.create(
            candidacy_id=self.candidacy_id,
            contact_id=contact_id,
            changes=changes,
            user_id=user_id,
        )

        self._apply_event(event)

    def upload_file(
        self,
        file_id: str,
        file_name: str,
        file_type: str,
        file_size: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Record file upload"""
        event = FileUploaded.create(
            candidacy_id=self.candidacy_id,
            file_id=file_id,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            user_id=user_id,
        )

        self._apply_event(event)

    def add_timeline_comment(
        self,
        comment_id: str,
        comment: str,
        format: str = "text/plain",
        user_id: Optional[str] = None,
    ) -> None:
        """Add timeline comment"""
        event = TimelineCommentAdded.create(
            candidacy_id=self.candidacy_id,
            comment_id=comment_id,
            comment=comment,
            format=format,
            user_id=user_id,
        )

        self._apply_event(event)

    def assign_user(
        self,
        assigned_user_id: str,
        role: str = "recruiter",
        by_user_id: Optional[str] = None,
    ) -> None:
        """Assign team member"""
        event = AssignmentAdded.create(
            candidacy_id=self.candidacy_id,
            assigned_user_id=assigned_user_id,
            role=role,
            by_user_id=by_user_id,
        )

        self._apply_event(event)

    def unassign_user(
        self,
        unassigned_user_id: str,
        by_user_id: Optional[str] = None,
    ) -> None:
        """Unassign team member"""
        event = AssignmentRemoved.create(
            candidacy_id=self.candidacy_id,
            unassigned_user_id=unassigned_user_id,
            by_user_id=by_user_id,
        )

        self._apply_event(event)

    def commit(self) -> None:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            self.event_store.append(event)
            self.events.append(event)

        self.uncommitted_events.clear()

    def _apply_event(self, event: Event) -> None:
        """Apply event (add to uncommitted events)"""
        self.uncommitted_events.append(event)

    def _rebuild_state(self, events: List[Event]) -> Dict[str, Any]:
        """
        Rebuild state from events

        Args:
            events: List of events to replay

        Returns:
            Current state
        """
        state: Dict[str, Any] = {
            "candidacy_id": self.candidacy_id,
            "name": None,
            "email": None,
            "requisition_id": None,
            "step": None,
            "status": None,
            "tags": [],
            "custom_fields": {},
            "contacts": [],
            "files": [],
            "timeline_comments": [],
            "assignments": [],
            "created_at": None,
            "updated_at": None,
            "terminated_at": None,
        }

        for event in events:
            # Update timestamps
            if state["created_at"] is None:
                state["created_at"] = event.timestamp
            state["updated_at"] = event.timestamp

            # Apply event to state
            if isinstance(event, CandidacyCreated):
                state.update(event.data)
                state["created_at"] = event.timestamp

            elif isinstance(event, CandidacyStepChanged):
                state["step"] = event.data["to_step"]

            elif isinstance(event, CandidacyStatusChanged):
                state["status"] = event.data["to_status"]

            elif isinstance(event, CandidacyTerminated):
                state["terminated_at"] = event.timestamp

            elif isinstance(event, ContactAdded):
                state["contacts"].append({
                    "contact_id": event.data["contact_id"],
                    "type": event.data["type"],
                    "scheduled_at": event.data.get("scheduled_at"),
                    "interviewer_ids": event.data.get("interviewer_ids", []),
                    "title": event.data.get("title"),
                    "added_at": event.timestamp,
                })

            elif isinstance(event, ContactUpdated):
                # Find and update contact
                contact_id = event.data["contact_id"]
                for contact in state["contacts"]:
                    if contact["contact_id"] == contact_id:
                        contact.update(event.data.get("changes", {}))
                        break

            elif isinstance(event, FileUploaded):
                state["files"].append({
                    "file_id": event.data["file_id"],
                    "file_name": event.data["file_name"],
                    "file_type": event.data["file_type"],
                    "file_size": event.data.get("file_size"),
                    "uploaded_at": event.timestamp,
                })

            elif isinstance(event, TimelineCommentAdded):
                state["timeline_comments"].append({
                    "comment_id": event.data["comment_id"],
                    "comment": event.data["comment"],
                    "format": event.data.get("format", "text/plain"),
                    "added_at": event.timestamp,
                    "added_by": event.metadata.get("user_id"),
                })

            elif isinstance(event, AssignmentAdded):
                state["assignments"].append({
                    "user_id": event.data["user_id"],
                    "role": event.data["role"],
                    "assigned_at": event.timestamp,
                })

            elif isinstance(event, AssignmentRemoved):
                # Remove assignment
                user_id = event.data["user_id"]
                state["assignments"] = [
                    a for a in state["assignments"]
                    if a["user_id"] != user_id
                ]

        return state
