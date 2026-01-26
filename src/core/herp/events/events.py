#!/usr/bin/env python3
"""
HERP Events

Defines immutable event types for candidacy changes.

All events are immutable and represent facts that have happened.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Event:
    """
    Base event class

    All events are immutable (frozen=True) and represent facts that happened.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of event (e.g., "CandidacyCreated")
        aggregate_id: ID of the aggregate (e.g., candidacy_id)
        timestamp: When the event occurred
        data: Event-specific data
        metadata: Additional metadata (user_id, correlation_id, etc.)
        version: Event version for schema evolution
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    aggregate_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary"""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            aggregate_id=data["aggregate_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
        )


@dataclass(frozen=True)
class CandidacyEvent(Event):
    """Base class for candidacy-related events"""

    pass


@dataclass(frozen=True)
class CandidacyCreated(CandidacyEvent):
    """
    Event: Candidacy was created

    Data:
        name: Candidate name
        email: Candidate email
        requisition_id: Job requisition ID
        step: Initial hiring step
        status: Initial status (usually "active")
        tags: Initial tags
        custom_fields: Custom field values
    """

    event_type: str = field(default="CandidacyCreated", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        name: str,
        email: Optional[str] = None,
        requisition_id: Optional[str] = None,
        step: str = "application",
        status: str = "active",
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> "CandidacyCreated":
        """Create CandidacyCreated event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "name": name,
                "email": email,
                "requisition_id": requisition_id,
                "step": step,
                "status": status,
                "tags": tags or [],
                "custom_fields": custom_fields or {},
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class CandidacyStepChanged(CandidacyEvent):
    """
    Event: Candidacy hiring step changed

    Data:
        from_step: Previous step
        to_step: New step
        comment: Optional comment about the change
    """

    event_type: str = field(default="CandidacyStepChanged", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        from_step: str,
        to_step: str,
        comment: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "CandidacyStepChanged":
        """Create CandidacyStepChanged event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "from_step": from_step,
                "to_step": to_step,
                "comment": comment,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class CandidacyStatusChanged(CandidacyEvent):
    """
    Event: Candidacy status changed

    Data:
        from_status: Previous status
        to_status: New status
        reason: Reason for change
    """

    event_type: str = field(default="CandidacyStatusChanged", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        from_status: str,
        to_status: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "CandidacyStatusChanged":
        """Create CandidacyStatusChanged event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "from_status": from_status,
                "to_status": to_status,
                "reason": reason,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class CandidacyTerminated(CandidacyEvent):
    """
    Event: Candidacy was terminated

    Data:
        reason: Termination reason (hired, rejected, withdrawn, etc.)
        comment: Optional comment
        final_step: Step at termination
    """

    event_type: str = field(default="CandidacyTerminated", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        reason: str,
        comment: Optional[str] = None,
        final_step: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "CandidacyTerminated":
        """Create CandidacyTerminated event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "reason": reason,
                "comment": comment,
                "final_step": final_step,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class ContactAdded(CandidacyEvent):
    """
    Event: Contact/interview added to candidacy

    Data:
        contact_id: Contact ID
        type: Contact type (phone_screen, technical_interview, etc.)
        scheduled_at: Scheduled datetime
        interviewer_ids: List of interviewer user IDs
        title: Contact title
    """

    event_type: str = field(default="ContactAdded", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        contact_id: str,
        contact_type: str,
        scheduled_at: Optional[str] = None,
        interviewer_ids: Optional[List[str]] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "ContactAdded":
        """Create ContactAdded event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "contact_id": contact_id,
                "type": contact_type,
                "scheduled_at": scheduled_at,
                "interviewer_ids": interviewer_ids or [],
                "title": title,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class ContactUpdated(CandidacyEvent):
    """
    Event: Contact/interview was updated

    Data:
        contact_id: Contact ID
        changes: Dictionary of changed fields
    """

    event_type: str = field(default="ContactUpdated", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        contact_id: str,
        changes: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> "ContactUpdated":
        """Create ContactUpdated event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "contact_id": contact_id,
                "changes": changes,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class FileUploaded(CandidacyEvent):
    """
    Event: File uploaded to candidacy

    Data:
        file_id: File ID
        file_name: File name
        file_type: File type (resume, career_summary, etc.)
        file_size: File size in bytes
    """

    event_type: str = field(default="FileUploaded", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        file_id: str,
        file_name: str,
        file_type: str,
        file_size: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> "FileUploaded":
        """Create FileUploaded event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class TimelineCommentAdded(CandidacyEvent):
    """
    Event: Timeline comment added

    Data:
        comment_id: Comment ID
        comment: Comment text
        format: Comment format (text/plain, text/markdown)
    """

    event_type: str = field(default="TimelineCommentAdded", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        comment_id: str,
        comment: str,
        format: str = "text/plain",
        user_id: Optional[str] = None,
    ) -> "TimelineCommentAdded":
        """Create TimelineCommentAdded event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "comment_id": comment_id,
                "comment": comment,
                "format": format,
            },
            metadata={"user_id": user_id} if user_id else {},
        )


@dataclass(frozen=True)
class AssignmentAdded(CandidacyEvent):
    """
    Event: Team member assigned to candidacy

    Data:
        user_id: Assigned user ID
        role: User role (recruiter, hiring_manager, interviewer)
    """

    event_type: str = field(default="AssignmentAdded", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        assigned_user_id: str,
        role: str = "recruiter",
        by_user_id: Optional[str] = None,
    ) -> "AssignmentAdded":
        """Create AssignmentAdded event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "user_id": assigned_user_id,
                "role": role,
            },
            metadata={"user_id": by_user_id} if by_user_id else {},
        )


@dataclass(frozen=True)
class AssignmentRemoved(CandidacyEvent):
    """
    Event: Team member unassigned from candidacy

    Data:
        user_id: Unassigned user ID
    """

    event_type: str = field(default="AssignmentRemoved", init=False)

    @classmethod
    def create(
        cls,
        candidacy_id: str,
        unassigned_user_id: str,
        by_user_id: Optional[str] = None,
    ) -> "AssignmentRemoved":
        """Create AssignmentRemoved event"""
        return cls(
            aggregate_id=candidacy_id,
            data={
                "user_id": unassigned_user_id,
            },
            metadata={"user_id": by_user_id} if by_user_id else {},
        )
