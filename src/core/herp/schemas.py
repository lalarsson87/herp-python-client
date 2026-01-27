"""
Schema definitions for HERP API responses
"""

from typing import Any, Dict


# Placeholder TypedDict classes
# In a real implementation, these would be proper TypedDict definitions
class HerpCandidacyResponse(Dict[str, Any]):
    """Candidacy response schema"""
    pass


class HerpCandidaciesListResponse(Dict[str, Any]):
    """Candidacies list response schema"""
    pass


class HerpAssignmentsListResponse(Dict[str, Any]):
    """Assignments list response schema"""
    pass


class HerpContactResponse(Dict[str, Any]):
    """Contact response schema"""
    pass


class HerpContactsListResponse(Dict[str, Any]):
    """Contacts list response schema"""
    pass


class HerpEvaluationResponse(Dict[str, Any]):
    """Evaluation response schema"""
    pass


class HerpFileResponse(Dict[str, Any]):
    """File response schema"""
    pass


class HerpFilesListResponse(Dict[str, Any]):
    """Files list response schema"""
    pass


class HerpTimelineCommentResponse(Dict[str, Any]):
    """Timeline comment response schema"""
    pass


class HerpTimelineCommentsListResponse(Dict[str, Any]):
    """Timeline comments list response schema"""
    pass


class HerpRequisitionsListResponse(Dict[str, Any]):
    """Requisitions list response schema"""
    pass


class HerpUsersListResponse(Dict[str, Any]):
    """Users list response schema"""
    pass
