#!/usr/bin/env python3
"""
Type definitions for HERP API responses

Uses TypedDict for better type safety and IDE support.
Requires Python 3.8+, uses NotRequired for optional fields (Python 3.11+).
"""

from datetime import datetime
from typing import List, Literal, Optional, TypedDict

# For Python 3.11+, use NotRequired for optional fields
# For Python 3.8-3.10, all fields are required unless explicitly Optional
try:
    from typing import NotRequired
except ImportError:
    # Fallback for Python < 3.11
    from typing_extensions import NotRequired


# ============================================================================
# Candidacy Types
# ============================================================================


class CandidacyResponse(TypedDict, total=False):
    """HERP candidacy response"""

    id: str
    name: str
    email: NotRequired[str]
    phone: NotRequired[str]
    resume_url: NotRequired[str]
    requisition_id: str
    step: str
    status: str
    created_at: str
    updated_at: str
    terminated_at: NotRequired[str]
    termination_reason: NotRequired[str]
    tags: NotRequired[List[str]]
    custom_fields: NotRequired[dict]


class CandidaciesListResponse(TypedDict):
    """Response for list candidacies endpoint"""

    data: List[CandidacyResponse]
    has_more: bool
    next_cursor: NotRequired[str]


class CandidacyCreateRequest(TypedDict, total=False):
    """Request for creating a candidacy"""

    name: str
    email: NotRequired[str]
    phone: NotRequired[str]
    resume_url: NotRequired[str]
    requisition_id: str
    step: NotRequired[str]
    tags: NotRequired[List[str]]
    custom_fields: NotRequired[dict]


class CandidacyStepUpdate(TypedDict, total=False):
    """Request for updating candidacy step"""

    step: str
    scheduled_date: NotRequired[str]
    notes: NotRequired[str]


# ============================================================================
# Contact Types
# ============================================================================

ContactType = Literal[
    "phone_screen",
    "casual_interview",
    "technical_interview",
    "behavioral_interview",
    "final_interview",
    "reference_check",
    "other",
]


class ContactResponse(TypedDict, total=False):
    """HERP contact/interview response"""

    id: str
    candidacy_id: str
    type: ContactType
    title: NotRequired[str]
    scheduled_at: NotRequired[str]
    duration_minutes: NotRequired[int]
    location: NotRequired[str]
    interviewer_ids: NotRequired[List[str]]
    notes: NotRequired[str]
    created_at: str
    updated_at: str


class ContactsListResponse(TypedDict):
    """Response for list contacts endpoint"""

    contacts: List[ContactResponse]
    has_more: NotRequired[bool]


class ContactCreateRequest(TypedDict, total=False):
    """Request for creating a contact"""

    type: ContactType
    title: NotRequired[str]
    scheduled_at: NotRequired[str]
    duration_minutes: NotRequired[int]
    location: NotRequired[str]
    interviewer_ids: NotRequired[List[str]]
    notes: NotRequired[str]


# ============================================================================
# Timeline Types
# ============================================================================


class TimelineCommentResponse(TypedDict, total=False):
    """HERP timeline comment response"""

    id: str
    candidacy_id: str
    user_id: str
    user_name: NotRequired[str]
    content: str
    content_type: Literal["text/plain", "text/markdown"]
    created_at: str
    updated_at: str


class TimelineCommentsListResponse(TypedDict):
    """Response for list timeline comments endpoint"""

    data: List[TimelineCommentResponse]
    has_more: NotRequired[bool]


class TimelineCommentCreateRequest(TypedDict, total=False):
    """Request for creating a timeline comment"""

    content: str
    content_type: NotRequired[Literal["text/plain", "text/markdown"]]


# ============================================================================
# File Types
# ============================================================================

FileType = Literal["resume", "career_summary", "other"]


class FileResponse(TypedDict, total=False):
    """HERP file response"""

    id: str
    candidacy_id: str
    name: str
    type: FileType
    size_bytes: NotRequired[int]
    mime_type: NotRequired[str]
    url: NotRequired[str]
    created_at: str


class FilesListResponse(TypedDict):
    """Response for list files endpoint"""

    files: List[FileResponse]
    has_more: NotRequired[bool]


# ============================================================================
# Evaluation Types
# ============================================================================


class EvaluationQuestionResponse(TypedDict, total=False):
    """Evaluation question response"""

    id: str
    question: str
    answer: NotRequired[str]
    score: NotRequired[int]
    max_score: NotRequired[int]


class EvaluationResponse(TypedDict, total=False):
    """HERP evaluation response"""

    id: str
    candidacy_id: str
    contact_id: NotRequired[str]
    evaluator_id: str
    evaluator_name: NotRequired[str]
    questions: List[EvaluationQuestionResponse]
    overall_score: NotRequired[int]
    max_overall_score: NotRequired[int]
    recommendation: NotRequired[
        Literal["strong_yes", "yes", "maybe", "no", "strong_no"]
    ]
    notes: NotRequired[str]
    created_at: str
    updated_at: str


class EvaluationSubmitRequest(TypedDict, total=False):
    """Request for submitting an evaluation"""

    questions: List[dict]  # Question responses
    overall_score: NotRequired[int]
    recommendation: NotRequired[
        Literal["strong_yes", "yes", "maybe", "no", "strong_no"]
    ]
    notes: NotRequired[str]


# ============================================================================
# Assignment Types
# ============================================================================


class AssignmentResponse(TypedDict, total=False):
    """HERP assignment response"""

    id: str
    candidacy_id: str
    user_id: str
    user_name: NotRequired[str]
    role: NotRequired[str]
    created_at: str


class AssignmentsListResponse(TypedDict):
    """Response for list assignments endpoint"""

    assignments: List[AssignmentResponse]


class AssignmentCreateRequest(TypedDict):
    """Request for creating an assignment"""

    user_id: str
    role: NotRequired[str]


# ============================================================================
# Requisition Types
# ============================================================================


class RequisitionResponse(TypedDict, total=False):
    """HERP requisition/job response"""

    id: str
    title: str
    department: NotRequired[str]
    location: NotRequired[str]
    employment_type: NotRequired[str]
    status: NotRequired[str]
    headcount: NotRequired[int]
    filled_count: NotRequired[int]
    created_at: str
    updated_at: str


class RequisitionsListResponse(TypedDict):
    """Response for list requisitions endpoint"""

    requisitions: List[RequisitionResponse]
    has_more: NotRequired[bool]


# ============================================================================
# User Types
# ============================================================================


class UserResponse(TypedDict, total=False):
    """HERP user response"""

    id: str
    name: str
    email: str
    role: NotRequired[str]
    department: NotRequired[str]
    is_active: NotRequired[bool]
    created_at: NotRequired[str]


class UsersListResponse(TypedDict):
    """Response for list users endpoint"""

    users: List[UserResponse]
    has_more: NotRequired[bool]


# ============================================================================
# Error Response Types
# ============================================================================


class ErrorResponse(TypedDict, total=False):
    """HERP API error response"""

    error: str
    message: str
    status_code: int
    details: NotRequired[dict]


# ============================================================================
# Pagination Types
# ============================================================================


class PaginationParams(TypedDict, total=False):
    """Common pagination parameters"""

    limit: NotRequired[int]
    offset: NotRequired[int]
    cursor: NotRequired[str]


# ============================================================================
# Search Types
# ============================================================================


class SearchParams(TypedDict, total=False):
    """Search parameters for candidacies"""

    query: NotRequired[str]
    requisition_id: NotRequired[str]
    step: NotRequired[str]
    status: NotRequired[str]
    tags: NotRequired[List[str]]
    created_after: NotRequired[str]
    created_before: NotRequired[str]
    updated_after: NotRequired[str]
    updated_before: NotRequired[str]
