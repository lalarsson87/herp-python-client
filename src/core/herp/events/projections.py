#!/usr/bin/env python3
"""
HERP Event Projections

Provides different views (projections) of event streams.

Projections transform events into read models optimized for specific queries:
- CandidacyProjection: Current state view
- TimelineProjection: Chronological activity view
- AuditLogProjection: Compliance and audit view
- AnalyticsProjection: Analytics and reporting view
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from .events import Event, CandidacyEvent
from .event_store import EventStore
from ...utils.logging import get_logger


logger = get_logger(__name__)


class Projection:
    """
    Base projection class

    Projections build read models from events for specific query patterns.
    """

    def __init__(self, event_store: EventStore):
        """
        Initialize projection

        Args:
            event_store: Event store to project from
        """
        self.event_store = event_store

    def project(self, events: List[Event]) -> Any:
        """
        Project events into read model

        Args:
            events: Events to project

        Returns:
            Projected read model
        """
        raise NotImplementedError


class CandidacyProjection(Projection):
    """
    Candidacy state projection

    Projects candidacy events into current state view.
    Optimized for "get current candidacy state" queries.

    Usage:
        projection = CandidacyProjection(event_store)
        state = projection.get_candidacy_state("cand_123")
        all_states = projection.get_all_candidacy_states()
    """

    def get_candidacy_state(self, candidacy_id: str) -> Dict[str, Any]:
        """
        Get current state for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            Current candidacy state
        """
        from .aggregate import EventSourcedCandidacy

        candidacy = EventSourcedCandidacy.load(candidacy_id, self.event_store)
        return candidacy.get_state()

    def get_all_candidacy_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current states for all candidacies

        Returns:
            Dictionary mapping candidacy_id to state
        """
        from .aggregate import EventSourcedCandidacy

        all_events = self.event_store.load_all_events()

        # Group events by aggregate
        events_by_candidacy = defaultdict(list)
        for event in all_events:
            if isinstance(event, CandidacyEvent):
                events_by_candidacy[event.aggregate_id].append(event)

        # Build states
        states = {}
        for candidacy_id, events in events_by_candidacy.items():
            candidacy = EventSourcedCandidacy(
                candidacy_id, self.event_store, events=events
            )
            states[candidacy_id] = candidacy.get_state()

        return states

    def get_candidacies_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all candidacies with specific status

        Args:
            status: Status to filter by

        Returns:
            List of candidacy states
        """
        all_states = self.get_all_candidacy_states()
        return [
            state for state in all_states.values()
            if state.get("status") == status
        ]

    def get_candidacies_by_step(self, step: str) -> List[Dict[str, Any]]:
        """
        Get all candidacies at specific hiring step

        Args:
            step: Hiring step to filter by

        Returns:
            List of candidacy states
        """
        all_states = self.get_all_candidacy_states()
        return [
            state for state in all_states.values()
            if state.get("step") == step
        ]


class TimelineProjection(Projection):
    """
    Timeline projection

    Projects events into chronological activity timeline.
    Optimized for "show activity feed" queries.

    Usage:
        projection = TimelineProjection(event_store)
        timeline = projection.get_candidacy_timeline("cand_123")
        recent = projection.get_recent_activity(hours=24)
    """

    def get_candidacy_timeline(
        self,
        candidacy_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get timeline for candidacy

        Args:
            candidacy_id: Candidacy ID
            from_timestamp: Start time filter
            to_timestamp: End time filter

        Returns:
            List of timeline entries
        """
        events = self.event_store.load_events(candidacy_id)

        # Filter by timestamp
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]

        # Convert to timeline entries
        timeline = []
        for event in events:
            entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "description": self._format_event_description(event),
                "user_id": event.metadata.get("user_id"),
                "data": event.data,
            }
            timeline.append(entry)

        return sorted(timeline, key=lambda x: x["timestamp"], reverse=True)

    def get_recent_activity(
        self,
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity across all candidacies

        Args:
            hours: Hours to look back
            limit: Maximum entries to return

        Returns:
            List of timeline entries
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=hours)
        events = self.event_store.load_all_events(from_timestamp=cutoff)

        # Convert to timeline entries
        timeline = []
        for event in events:
            if not isinstance(event, CandidacyEvent):
                continue

            entry = {
                "candidacy_id": event.aggregate_id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "description": self._format_event_description(event),
                "user_id": event.metadata.get("user_id"),
                "data": event.data,
            }
            timeline.append(entry)

        # Sort by timestamp (most recent first)
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)

        # Apply limit
        if limit:
            timeline = timeline[:limit]

        return timeline

    def _format_event_description(self, event: Event) -> str:
        """Format event as human-readable description"""
        descriptions = {
            "CandidacyCreated": f"Candidacy created for {event.data.get('name')}",
            "CandidacyStepChanged": f"Step changed from {event.data.get('from_step')} to {event.data.get('to_step')}",
            "CandidacyStatusChanged": f"Status changed to {event.data.get('to_status')}",
            "CandidacyTerminated": f"Candidacy terminated: {event.data.get('reason')}",
            "ContactAdded": f"Contact added: {event.data.get('type')}",
            "ContactUpdated": f"Contact updated: {event.data.get('contact_id')}",
            "FileUploaded": f"File uploaded: {event.data.get('file_name')}",
            "TimelineCommentAdded": f"Comment added",
            "AssignmentAdded": f"User {event.data.get('user_id')} assigned as {event.data.get('role')}",
            "AssignmentRemoved": f"User {event.data.get('user_id')} unassigned",
        }

        return descriptions.get(event.event_type, event.event_type)


class AuditLogProjection(Projection):
    """
    Audit log projection

    Projects events into audit log for compliance.
    Optimized for "who did what when" queries.

    Usage:
        projection = AuditLogProjection(event_store)
        audit_log = projection.get_audit_log("cand_123")
        user_actions = projection.get_user_actions("user_456")
    """

    def get_audit_log(
        self,
        candidacy_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit log for candidacy

        Args:
            candidacy_id: Candidacy ID
            from_timestamp: Start time filter
            to_timestamp: End time filter

        Returns:
            List of audit log entries
        """
        events = self.event_store.load_events(candidacy_id)

        # Filter by timestamp
        if from_timestamp:
            events = [e for e in events if e.timestamp >= from_timestamp]
        if to_timestamp:
            events = [e for e in events if e.timestamp <= to_timestamp]

        # Convert to audit entries
        audit_log = []
        for event in events:
            entry = {
                "timestamp": event.timestamp.isoformat(),
                "event_id": event.event_id,
                "event_type": event.event_type,
                "user_id": event.metadata.get("user_id"),
                "action": self._format_action(event),
                "before": self._extract_before_value(event),
                "after": self._extract_after_value(event),
                "ip_address": event.metadata.get("ip_address"),
                "user_agent": event.metadata.get("user_agent"),
            }
            audit_log.append(entry)

        return audit_log

    def get_user_actions(
        self,
        user_id: str,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all actions by a user

        Args:
            user_id: User ID
            from_timestamp: Start time filter
            to_timestamp: End time filter

        Returns:
            List of user actions
        """
        all_events = self.event_store.load_all_events(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )

        # Filter by user
        user_events = [
            e for e in all_events
            if e.metadata.get("user_id") == user_id
        ]

        # Convert to action entries
        actions = []
        for event in user_events:
            entry = {
                "timestamp": event.timestamp.isoformat(),
                "candidacy_id": event.aggregate_id,
                "event_type": event.event_type,
                "action": self._format_action(event),
                "data": event.data,
            }
            actions.append(entry)

        return sorted(actions, key=lambda x: x["timestamp"], reverse=True)

    def _format_action(self, event: Event) -> str:
        """Format event as audit action"""
        actions = {
            "CandidacyCreated": "Created candidacy",
            "CandidacyStepChanged": "Changed hiring step",
            "CandidacyStatusChanged": "Changed status",
            "CandidacyTerminated": "Terminated candidacy",
            "ContactAdded": "Added contact",
            "ContactUpdated": "Updated contact",
            "FileUploaded": "Uploaded file",
            "TimelineCommentAdded": "Added comment",
            "AssignmentAdded": "Added assignment",
            "AssignmentRemoved": "Removed assignment",
        }

        return actions.get(event.event_type, event.event_type)

    def _extract_before_value(self, event: Event) -> Optional[str]:
        """Extract 'before' value for audit"""
        if event.event_type == "CandidacyStepChanged":
            return event.data.get("from_step")
        elif event.event_type == "CandidacyStatusChanged":
            return event.data.get("from_status")
        return None

    def _extract_after_value(self, event: Event) -> Optional[str]:
        """Extract 'after' value for audit"""
        if event.event_type == "CandidacyStepChanged":
            return event.data.get("to_step")
        elif event.event_type == "CandidacyStatusChanged":
            return event.data.get("to_status")
        return None


class AnalyticsProjection(Projection):
    """
    Analytics projection

    Projects events into metrics and analytics.
    Optimized for reporting and dashboards.

    Usage:
        projection = AnalyticsProjection(event_store)
        metrics = projection.get_metrics()
        funnel = projection.get_conversion_funnel()
    """

    def get_metrics(
        self,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get recruitment metrics

        Args:
            from_timestamp: Start time filter
            to_timestamp: End time filter

        Returns:
            Dictionary of metrics
        """
        from .aggregate import EventSourcedCandidacy

        all_events = self.event_store.load_all_events(
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )

        # Group events by candidacy
        events_by_candidacy = defaultdict(list)
        for event in all_events:
            if isinstance(event, CandidacyEvent):
                events_by_candidacy[event.aggregate_id].append(event)

        # Calculate metrics
        total_candidacies = len(events_by_candidacy)
        candidacies_by_status = defaultdict(int)
        candidacies_by_step = defaultdict(int)
        terminated_reasons = defaultdict(int)

        for candidacy_id, events in events_by_candidacy.items():
            candidacy = EventSourcedCandidacy(
                candidacy_id, self.event_store, events=events
            )
            state = candidacy.get_state()

            status = state.get("status")
            step = state.get("step")

            if status:
                candidacies_by_status[status] += 1
            if step:
                candidacies_by_step[step] += 1

            # Check for termination
            for event in events:
                if event.event_type == "CandidacyTerminated":
                    reason = event.data.get("reason")
                    if reason:
                        terminated_reasons[reason] += 1

        return {
            "total_candidacies": total_candidacies,
            "by_status": dict(candidacies_by_status),
            "by_step": dict(candidacies_by_step),
            "termination_reasons": dict(terminated_reasons),
            "active_candidacies": candidacies_by_status.get("active", 0),
            "hired_candidacies": candidacies_by_status.get("hired", 0),
            "terminated_candidacies": candidacies_by_status.get("terminated", 0),
        }

    def get_conversion_funnel(self) -> Dict[str, int]:
        """
        Get conversion funnel (candidacies by step)

        Returns:
            Dictionary mapping step to count
        """
        projection = CandidacyProjection(self.event_store)
        all_states = projection.get_all_candidacy_states()

        funnel = defaultdict(int)
        for state in all_states.values():
            step = state.get("step")
            if step:
                funnel[step] += 1

        return dict(funnel)

    def get_time_to_hire(self) -> Dict[str, Any]:
        """
        Get time-to-hire metrics

        Returns:
            Dictionary with average, min, max time-to-hire
        """
        from .aggregate import EventSourcedCandidacy

        all_events = self.event_store.load_all_events()

        # Group events by candidacy
        events_by_candidacy = defaultdict(list)
        for event in all_events:
            if isinstance(event, CandidacyEvent):
                events_by_candidacy[event.aggregate_id].append(event)

        # Calculate time-to-hire for hired candidates
        times_to_hire = []

        for candidacy_id, events in events_by_candidacy.items():
            candidacy = EventSourcedCandidacy(
                candidacy_id, self.event_store, events=events
            )
            state = candidacy.get_state()

            if state.get("status") == "hired":
                created_at = state.get("created_at")
                terminated_at = state.get("terminated_at")

                if created_at and terminated_at:
                    delta = (terminated_at - created_at).days
                    times_to_hire.append(delta)

        if not times_to_hire:
            return {
                "count": 0,
                "average_days": None,
                "min_days": None,
                "max_days": None,
            }

        return {
            "count": len(times_to_hire),
            "average_days": sum(times_to_hire) / len(times_to_hire),
            "min_days": min(times_to_hire),
            "max_days": max(times_to_hire),
        }
