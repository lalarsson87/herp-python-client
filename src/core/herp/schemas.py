"""
Schema definitions for HERP API responses

Complete TypedDict schemas for all HERP Hire API endpoints.
Provides static type checking and IDE autocomplete for API responses.

**IMPORTANT**: These schemas match the ACTUAL HERP API responses which use
camelCase field names (e.g., `requisitionId`, not `requisition_id`).

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
# Nested Channel Schemas
# ============================================================================


class HerpAgentChannel(TypedDict):
    """Agent channel information"""

    id: str
    company: str
    name: str


class HerpMediaChannel(TypedDict):
    """Media channel information"""

    mediaName: str
    isScout: bool


class HerpManualChannel(TypedDict):
    """Manual channel information"""

    kind: str
    description: NotRequired[str]


class HerpChannelAgent(TypedDict):
    """Channel with agent type"""

    type: Literal["agent"]
    agent: HerpAgentChannel


class HerpChannelMedia(TypedDict):
    """Channel with media type"""

    type: Literal["media"]
    mediaName: str
    isScout: bool


class HerpChannelManual(TypedDict):
    """Channel with manual type"""

    type: Literal["manual"]
    kind: str
    description: NotRequired[str]


class HerpChannelJobMiru(TypedDict):
    """Channel with jobmiru type"""

    type: Literal["jobmiru"]


class HerpChannelCareerPage(TypedDict):
    """Channel with career page type"""

    type: Literal["careerPage"]


# Union of all channel types
HerpChannel = (
    HerpChannelAgent
    | HerpChannelMedia
    | HerpChannelManual
    | HerpChannelJobMiru
    | HerpChannelCareerPage
)


# ============================================================================
# Candidacy Schemas
# ============================================================================


class HerpCandidacyResponse(TypedDict):
    """
    Candidacy response schema

    Represents a single candidacy (job application) in HERP.

    **Field Names**: Uses camelCase as returned by HERP API
    (e.g., `requisitionId`, not `requisition_id`)
    """

    # Required fields
    id: str
    name: str
    status: Literal["active", "hired", "terminated"]
    requisitionId: str
    appliedAt: str  # ISO 8601 datetime
    step: str
    stepUpdatedAt: str  # ISO 8601 datetime
    updatedAt: str  # ISO 8601 datetime
    channel: HerpChannel
    operators: List[str]
    tags: List[str]

    # Optional fields
    email: NotRequired[str]
    telephoneNumber: NotRequired[str]
    age: NotRequired[str]
    company: NotRequired[str]
    education: NotRequired[str]
    career: NotRequired[str]
    note: NotRequired[str]
    terminationReason: NotRequired[str]
    terminatedAt: NotRequired[str]  # ISO 8601 datetime


class HerpCandidaciesListResponse(TypedDict):
    """
    Candidacies list response schema

    The HERP API returns candidacies in a top-level "candidacies" key.
    """

    candidacies: List[HerpCandidacyResponse]


# ============================================================================
# Contact/Interview Schemas
# ============================================================================


class HerpEvaluationItem(TypedDict):
    """Evaluation item in a contact"""

    id: str
    status: Literal["unfilled", "completed", "pending"]
    requesterId: str
    evaluatorId: str


class HerpContactResponse(TypedDict):
    """
    Contact (interview/assessment) response schema

    Represents an interview, assessment, or contact event.

    **Field Names**: Uses camelCase as returned by HERP API
    """

    # Required fields
    id: str
    type: str  # Type of contact (e.g., "書類", "カジュアル面談", etc.)
    step: str  # Hiring step
    createdAt: str  # ISO 8601 datetime
    createdBy: str  # User ID

    # Optional fields
    evaluations: NotRequired[List[HerpEvaluationItem]]
    requireAssessmentSchedule: NotRequired[bool]
    title: NotRequired[str]
    scheduledAt: NotRequired[str]  # ISO 8601 datetime
    location: NotRequired[str]
    notes: NotRequired[str]


class HerpContactsListResponse(TypedDict):
    """
    Contacts list response schema

    The HERP API returns contacts in a top-level "contacts" key.
    """

    contacts: List[HerpContactResponse]


# ============================================================================
# Evaluation Schemas
# ============================================================================


class HerpEvaluationQuestionResponse(TypedDict):
    """Evaluation question schema"""

    id: str
    question: str
    type: Literal["text", "rating", "boolean", "select"]
    required: NotRequired[bool]
    options: NotRequired[List[str]]


class HerpEvaluationResponse(TypedDict):
    """Evaluation response schema"""

    id: str
    contactId: str
    evaluatorId: str
    status: Literal["pending", "submitted", "completed"]
    createdAt: str
    updatedAt: str
    questions: List[HerpEvaluationQuestionResponse]
    answers: NotRequired[Dict[str, Any]]
    overallRating: NotRequired[int]
    recommendation: NotRequired[Literal["strong_yes", "yes", "no", "strong_no"]]
    notes: NotRequired[str]


class HerpEvaluationsListResponse(TypedDict):
    """Evaluations list response schema"""

    evaluations: List[HerpEvaluationResponse]


# ============================================================================
# Timeline Comment Schemas
# ============================================================================


class HerpTimelineCommentResponse(TypedDict):
    """Timeline comment response schema"""

    id: str
    candidacyId: str
    userId: str
    content: str
    contentType: Literal["text/plain", "text/markdown"]
    createdAt: str
    updatedAt: str
    isInternal: NotRequired[bool]


class HerpTimelineCommentsListResponse(TypedDict):
    """Timeline comments list response schema"""

    comments: List[HerpTimelineCommentResponse]


# ============================================================================
# File Schemas
# ============================================================================


class HerpFileResponse(TypedDict):
    """File response schema"""

    id: str
    candidacyId: str
    fileName: str
    fileType: Literal["resume", "career_summary", "portfolio", "other"]
    fileSize: int  # bytes
    mimeType: str
    uploadedBy: str
    uploadedAt: str
    url: NotRequired[str]  # Pre-signed download URL (temporary)
    expiresAt: NotRequired[str]


class HerpFilesListResponse(TypedDict):
    """Files list response schema"""

    files: List[HerpFileResponse]


# ============================================================================
# Assignment Schemas
# ============================================================================


class HerpAssignmentResponse(TypedDict):
    """Assignment response schema"""

    id: str
    candidacyId: str
    userId: str
    role: Literal["recruiter", "hiring_manager", "interviewer", "coordinator"]
    assignedBy: str
    assignedAt: str


class HerpAssignmentsListResponse(TypedDict):
    """Assignments list response schema"""

    assignments: List[HerpAssignmentResponse]


# ============================================================================
# Requisition (Job Position) Schemas
# ============================================================================


class HerpRequisitionResponse(TypedDict):
    """Requisition (job position) response schema"""

    id: str
    title: str
    departmentId: NotRequired[str]
    status: Literal["open", "closed", "draft"]
    employmentType: NotRequired[Literal["full_time", "part_time", "contract", "intern"]]
    location: NotRequired[str]
    description: NotRequired[str]
    createdAt: str
    updatedAt: str


class HerpRequisitionsListResponse(TypedDict):
    """Requisitions list response schema"""

    requisitions: List[HerpRequisitionResponse]


# ============================================================================
# User Schemas
# ============================================================================


class HerpUserResponse(TypedDict):
    """User response schema"""

    id: str
    name: str
    email: str
    role: NotRequired[Literal["admin", "recruiter", "hiring_manager", "member"]]
    department: NotRequired[str]
    isActive: NotRequired[bool]


class HerpUsersListResponse(TypedDict):
    """Users list response schema"""

    users: List[HerpUserResponse]


# ============================================================================
# Error Response Schema
# ============================================================================


class HerpErrorResponse(TypedDict):
    """Error response schema"""

    error: str
    message: str
    status_code: int
    details: NotRequired[Dict[str, Any]]


# ============================================================================
# Pagination Metadata
# ============================================================================


class HerpPaginationMetadata(TypedDict):
    """Pagination metadata"""

    total: int
    page: int
    perPage: int
    hasMore: bool


# ============================================================================
# Type Aliases for Convenience
# ============================================================================

# Alias for candidacy data dict (what client methods return)
CandidacyDict = Dict[str, Any]
ContactDict = Dict[str, Any]
EvaluationDict = Dict[str, Any]
FileDict = Dict[str, Any]
