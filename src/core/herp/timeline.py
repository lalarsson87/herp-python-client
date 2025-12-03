#!/usr/bin/env python3
"""
HERP Timeline API Client

Handles timeline comment operations for candidates.
"""

from typing import Dict, Any, List

from ..utils.validators import validate_list_response
from ..utils.logging import get_logger
from .base_client import HerpBaseClient
from .schemas import HerpTimelineCommentsListResponse


logger = get_logger(__name__)


class TimelineAPI:
    """
    Timeline API Client

    Provides methods for managing candidate timeline comments.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize timeline API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpTimelineCommentsListResponse, strict=False)
    def list(
        self,
        candidacy_id: str
    ) -> List[Dict[str, Any]]:
        """
        List timeline comments for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of timeline comment records
        """
        data = self.client.get(f"/v1/candidacies/{candidacy_id}/timeline-comments")
        return data.get("comments", data.get("data", []))

    def add_comment(
        self,
        candidacy_id: str,
        comment: str,
        content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """
        Add timeline comment

        Args:
            candidacy_id: Candidacy ID
            comment: Comment text
            content_type: Content type (text/plain or text/markdown)

        Returns:
            Created comment record
        """
        return self.client.post(
            f"/v1/candidacies/{candidacy_id}/timeline-comments",
            json={
                "comment": comment,
                "contentType": content_type
            }
        )
