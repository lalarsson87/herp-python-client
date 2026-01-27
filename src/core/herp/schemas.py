"""
Schema definitions for HERP API responses

Complete TypedDict schemas for all HERP Hire API endpoints.
Provides static type checking and IDE autocomplete for API responses.

Usage:
    from src.core.herp.schemas import HerpCandidacyResponse

    def get_candidacy(candidacy_id: str) -> HerpCandidacyResponse:
        return client.candidacies.get(candidacy_id)

    # TypedDict provides autocomplete and type checking
    candidacy: HerpCandidacyResponse = get_candidacy("cand_123")
    print(candidacy["name"])  # Type-safe field access
"""

from typing import Any, Dict, List, Literal, NotRequired, TypedDict


# ============================================================================
# Candidacy Schemas
# ============================================================================


class HerpCandidacyResponse(TypedDict):
    """
    Candidacy response schema

    Represents a single candidacy (job application) in HERP.
    """

    id: str
    name: str
    email: NotRequired[str]
    phone: NotRequired[str]
    resume_url: NotRequired[str]
    requisition_id: str
    step: NotRequired[str]
    status: Literal["active", "hired", "terminated"]
    created_at: str  # ISO 8601 datetime
    updated_at: str  # ISO 8601 datetime
    tags: NotRequired[List[str]]
    custom_fields: NotRequired[Dict[str, Any]]
    source: NotRequired[str]
    referrer: NotRequired[str]


class HerpCandidaciesListResponse(TypedDict):
    """
    Candidacies list response schema

    Paginated list of candidacies.
    """

    data: List[HerpCandidacyResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


# ============================================================================
# Contact/Interview Schemas
# ============================================================================


class HerpContactResponse(TypedDict):
    """
    Contact (interview) response schema

    Represents an interview or contact event.
    """

    id: str
    candidacy_id: str
    type: Literal[
        "phone_screen",
        "technical_interview",
        "casual_interview",
        "behavioral_interview",
        "final_interview",
        "reference_check",
        "other",
    ]
    title: NotRequired[str]
    scheduled_at: NotRequired[str]  # ISO 8601 datetime
    duration_minutes: NotRequired[int]
    location: NotRequired[str]
    interviewer_ids: NotRequired[List[str]]
    notes: NotRequired[str]
    status: NotRequired[Literal["scheduled", "completed", "cancelled"]]
    created_at: str
    updated_at: str


class HerpContactsListResponse(TypedDict):
    """
    Contacts list response schema

    Paginated list of contacts.
    """

    data: List[HerpContactResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


# ============================================================================
# Evaluation Schemas
# ============================================================================


class HerpEvaluationQuestionResponse(TypedDict):
    """Individual evaluation question response"""

    id: str
    question_text: NotRequired[str]
    answer: NotRequired[str]
    score: NotRequired[int]
    max_score: NotRequired[int]


class HerpEvaluationResponse(TypedDict):
    """
    Evaluation response schema

    Represents an evaluation/assessment for a candidacy.
    """

    id: str
    candidacy_id: str
    contact_id: NotRequired[str]
    evaluator_id: str
    questions: NotRequired[List[HerpEvaluationQuestionResponse]]
    overall_score: NotRequired[int]
    max_overall_score: NotRequired[int]
    recommendation: NotRequired[
        Literal["strong_yes", "yes", "maybe", "no", "strong_no"]
    ]
    notes: NotRequired[str]
    submitted_at: NotRequired[str]  # ISO 8601 datetime
    created_at: str
    updated_at: str


# ============================================================================
# Timeline/Activity Schemas
# ============================================================================


class HerpTimelineCommentResponse(TypedDict):
    """
    Timeline comment response schema

    Represents a comment on a candidacy timeline.
    """

    id: str
    candidacy_id: str
    author_id: str
    author_name: NotRequired[str]
    content: str
    content_type: Literal["text/plain", "text/markdown"]
    created_at: str
    updated_at: str


class HerpTimelineCommentsListResponse(TypedDict):
    """
    Timeline comments list response schema

    Paginated list of timeline comments.
    """

    data: List[HerpTimelineCommentResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


# ============================================================================
# File/Document Schemas
# ============================================================================


class HerpFileResponse(TypedDict):
    """
    File response schema

    Represents an uploaded file (resume, cover letter, etc).
    """

    id: str
    candidacy_id: str
    filename: str
    file_type: Literal["resume", "career_summary", "other"]
    content_type: str  # MIME type
    size_bytes: int
    url: NotRequired[str]
    download_url: NotRequired[str]
    uploaded_by: NotRequired[str]
    created_at: str
    updated_at: str


class HerpFilesListResponse(TypedDict):
    """
    Files list response schema

    Paginated list of files.
    """

    data: List[HerpFileResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


# ============================================================================
# Assignment Schemas
# ============================================================================


class HerpAssignmentResponse(TypedDict):
    """
    Assignment response schema

    Represents a team member assignment to a candidacy.
    """

    id: str
    candidacy_id: str
    user_id: str
    user_name: NotRequired[str]
    role: NotRequired[Literal["recruiter", "hiring_manager", "interviewer", "other"]]
    created_at: str


class HerpAssignmentsListResponse(TypedDict):
    """
    Assignments list response schema

    List of assignments for a candidacy.
    """

    data: List[HerpAssignmentResponse]
    total: NotRequired[int]


# ============================================================================
# Master Data Schemas
# ============================================================================


class HerpRequisitionResponse(TypedDict):
    """
    Requisition (job posting) response schema

    Represents a job requisition/opening.
    """

    id: str
    title: str
    description: NotRequired[str]
    department: NotRequired[str]
    location: NotRequired[str]
    employment_type: NotRequired[Literal["full_time", "part_time", "contract", "intern"]]
    status: Literal["draft", "open", "closed", "on_hold"]
    hiring_manager_id: NotRequired[str]
    created_at: str
    updated_at: str


class HerpRequisitionsListResponse(TypedDict):
    """
    Requisitions list response schema

    Paginated list of requisitions.
    """

    data: List[HerpRequisitionResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


class HerpUserResponse(TypedDict):
    """
    User response schema

    Represents a team member/user in HERP.
    """

    id: str
    name: str
    email: str
    role: NotRequired[Literal["admin", "recruiter", "hiring_manager", "interviewer"]]
    department: NotRequired[str]
    is_active: NotRequired[bool]
    created_at: str
    updated_at: str


class HerpUsersListResponse(TypedDict):
    """
    Users list response schema

    Paginated list of users.
    """

    data: List[HerpUserResponse]
    total: NotRequired[int]
    page: NotRequired[int]
    per_page: NotRequired[int]
    has_more: NotRequired[bool]


# ============================================================================
# Error Response Schema
# ============================================================================


class HerpErrorResponse(TypedDict):
    """
    Error response schema

    Standard error response from HERP API.
    """

    error: str
    error_description: NotRequired[str]
    error_code: NotRequired[str]
    status_code: int
    request_id: NotRequired[str]


# ============================================================================
# Pagination Metadata
# ============================================================================


class HerpPaginationMetadata(TypedDict):
    """
    Pagination metadata

    Common pagination fields across list responses.
    """

    total: int
    page: int
    per_page: int
    has_more: bool
    next_page: NotRequired[int]
    prev_page: NotRequired[int]


# ============================================================================
# Type Aliases for Common Patterns
# ============================================================================

# Response types for API methods
CandidacyResponse = HerpCandidacyResponse
CandidacyListResponse = HerpCandidaciesListResponse
ContactResponse = HerpContactResponse
ContactListResponse = HerpContactsListResponse
EvaluationResponse = HerpEvaluationResponse
FileResponse = HerpFileResponse
FileListResponse = HerpFilesListResponse
TimelineCommentResponse = HerpTimelineCommentResponse
TimelineCommentListResponse = HerpTimelineCommentsListResponse
RequisitionResponse = HerpRequisitionResponse
RequisitionListResponse = HerpRequisitionsListResponse
UserResponse = HerpUserResponse
UserListResponse = HerpUsersListResponse
