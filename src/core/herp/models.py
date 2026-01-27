#!/usr/bin/env python3
"""
HERP API Data Models

Type-safe data models for HERP API entities with validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class CandidacyStatus(Enum):
    """Candidacy status values"""

    ACTIVE = "active"
    TERMINATED = "terminated"


class TerminationReason(Enum):
    """Termination reason values"""

    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    HIRED = "hired"
    OTHER = "other"


class ContactType(Enum):
    """Contact/Interview type values"""

    TECHNICAL_INTERVIEW = "technical_interview"
    CASUAL_CONVERSATION = "casual_conversation"
    PHONE_SCREEN = "phone_screen"
    ONSITE_INTERVIEW = "onsite_interview"
    FINAL_INTERVIEW = "final_interview"
    OTHER = "other"


class FileType(Enum):
    """File type values"""

    RESUME = "resume"
    CAREER_SUMMARY = "career_summary"
    OTHER = "other"


@dataclass
class Candidacy:
    """
    HERP Candidacy model

    Represents a candidate application in HERP.
    """

    id: str
    name: str
    email: Optional[str] = None
    status: str = "active"
    step: Optional[str] = None
    termination_reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    requisition_id: Optional[str] = None
    channel: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Candidacy":
        """
        Create Candidacy from API response

        Args:
            data: API response dictionary

        Returns:
            Candidacy instance
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email"),
            status=data.get("status", "active"),
            step=data.get("step"),
            termination_reason=data.get("terminationReason"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            requisition_id=data.get("requisitionId"),
            channel=data.get("channel"),
            metadata=data,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request format"""
        return {
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "step": self.step,
        }

    @property
    def is_active(self) -> bool:
        """Check if candidacy is active"""
        return self.status == "active"

    @property
    def is_terminated(self) -> bool:
        """Check if candidacy is terminated"""
        return self.status == "terminated"


@dataclass
class Contact:
    """
    HERP Contact/Interview model

    Represents an interview or meeting with a candidate.
    """

    id: str
    candidacy_id: str
    contact_type: str
    scheduled_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    evaluations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], candidacy_id: str = "") -> "Contact":
        """Create Contact from API response"""
        return cls(
            id=data.get("id", ""),
            candidacy_id=candidacy_id,
            contact_type=data.get("contactType", ""),
            scheduled_at=data.get("scheduledAt"),
            completed_at=data.get("completedAt"),
            created_at=data.get("createdAt"),
            evaluations=data.get("evaluations", []),
            metadata=data,
        )

    @property
    def is_scheduled(self) -> bool:
        """Check if contact is scheduled"""
        return self.scheduled_at is not None

    @property
    def is_completed(self) -> bool:
        """Check if contact is completed"""
        return self.completed_at is not None


@dataclass
class Evaluation:
    """
    HERP Evaluation model

    Represents an evaluation/assessment of a candidate.
    """

    id: str
    candidacy_id: Optional[str] = None
    contact_id: Optional[str] = None
    evaluator_id: Optional[str] = None
    result: Optional[str] = None
    responses: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Evaluation":
        """Create Evaluation from API response"""
        return cls(
            id=data.get("id", ""),
            candidacy_id=data.get("candidacyId"),
            contact_id=data.get("contactId"),
            evaluator_id=data.get("evaluatorId"),
            result=data.get("result"),
            responses=data.get("responses", {}),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            metadata=data,
        )


@dataclass
class TimelineComment:
    """
    HERP Timeline Comment model

    Represents a comment on a candidate's timeline.
    """

    id: str
    candidacy_id: str
    author_id: str
    comment: str
    content_type: str = "text/plain"
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], candidacy_id: str = ""
    ) -> "TimelineComment":
        """Create TimelineComment from API response"""
        return cls(
            id=data.get("id", ""),
            candidacy_id=candidacy_id,
            author_id=data.get("authorId", ""),
            comment=data.get("comment", ""),
            content_type=data.get("contentType", "text/plain"),
            created_at=data.get("createdAt"),
            metadata=data,
        )


@dataclass
class File:
    """
    HERP File model

    Represents a file attached to a candidacy.
    """

    id: str
    candidacy_id: str
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    created_at: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], candidacy_id: str = "") -> "File":
        """Create File from API response"""
        return cls(
            id=data.get("id", ""),
            candidacy_id=candidacy_id,
            file_name=data.get("fileName", ""),
            file_type=data.get("fileType", "other"),
            file_size=data.get("fileSize"),
            created_at=data.get("createdAt"),
            download_url=data.get("downloadUrl"),
            metadata=data,
        )


@dataclass
class Requisition:
    """
    HERP Requisition model

    Represents a job opening/position.
    """

    id: str
    title: str
    status: str = "open"
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requisition":
        """Create Requisition from API response"""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            status=data.get("status", "open"),
            created_at=data.get("createdAt"),
            metadata=data,
        )


@dataclass
class User:
    """
    HERP User model

    Represents a user/team member in HERP.
    """

    id: str
    name: str
    email: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create User from API response"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email"),
            metadata=data,
        )


# Type aliases for common collections
CandidacyList = List[Candidacy]
ContactList = List[Contact]
EvaluationList = List[Evaluation]
TimelineCommentList = List[TimelineComment]
FileList = List[File]
RequisitionList = List[Requisition]
UserList = List[User]
