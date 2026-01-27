#!/usr/bin/env python3
"""
HERP Async Timeline API Client

Async version of timeline comment operations.
"""

from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response, validate_single_response
from .async_base_client import AsyncHerpBaseClient
from .schemas import HerpTimelineCommentResponse, HerpTimelineCommentsListResponse

logger = get_logger(__name__)


class AsyncTimelineAPI:
    """
    Async Timeline API Client

    Provides async methods for timeline comment operations.
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async timeline API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpTimelineCommentsListResponse, strict=False)
    async def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List timeline comments for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of timeline comment records
        """
        data = await self.client.get(
            f"/v1/candidacies/{candidacy_id}/timeline-comments"
        )
        return data.get("timeline_comments", data.get("data", []))

    @validate_single_response(HerpTimelineCommentResponse, strict=False)
    async def add(
        self, candidacy_id: str, comment: str, format: str = "text/plain"
    ) -> Dict[str, Any]:
        """
        Add timeline comment

        Args:
            candidacy_id: Candidacy ID
            comment: Comment text
            format: Comment format (text/plain or text/markdown)

        Returns:
            Created comment record

        Usage:
            comment = await api.add(
                "cand_123",
                "Great technical interview, strong problem solving"
            )

            # With markdown
            comment = await api.add(
                "cand_123",
                "## Technical Interview\\n\\n- Strong coding skills\\n- Good communication",
                format="text/markdown"
            )
        """
        comment_data = {"comment": comment, "format": format}
        data = await self.client.post(
            f"/v1/candidacies/{candidacy_id}/timeline-comments", json=comment_data
        )
        logger.info(f"Added timeline comment to candidacy {candidacy_id}")
        return data.get("timeline_comment", data.get("data", data))
