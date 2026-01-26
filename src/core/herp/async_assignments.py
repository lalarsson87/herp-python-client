#!/usr/bin/env python3
"""
HERP Async Assignments API Client

Async version of team assignment operations.
"""

from typing import Any, Dict, List

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response
from .async_base_client import AsyncHerpBaseClient
from .schemas import HerpAssignmentsListResponse

logger = get_logger(__name__)


class AsyncAssignmentsAPI:
    """
    Async Assignments API Client

    Provides async methods for team assignment operations.
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async assignments API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpAssignmentsListResponse, strict=False)
    async def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List assignments for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of assignment records (user IDs and roles)
        """
        data = await self.client.get(f"/v1/candidacies/{candidacy_id}/assignments")
        return data.get("assignments", data.get("data", []))

    async def assign(
        self, candidacy_id: str, user_id: str, role: str = "recruiter"
    ) -> Dict[str, Any]:
        """
        Assign user to candidacy

        Args:
            candidacy_id: Candidacy ID
            user_id: User ID to assign
            role: User role (recruiter, hiring_manager, interviewer)

        Returns:
            Assignment record
        """
        assignment_data = {"user_id": user_id, "role": role}
        data = await self.client.post(
            f"/v1/candidacies/{candidacy_id}/assignments", json=assignment_data
        )
        logger.info(f"Assigned {user_id} as {role} to candidacy {candidacy_id}")
        return data.get("assignment", data.get("data", data))

    async def unassign(self, candidacy_id: str, user_id: str) -> None:
        """
        Unassign user from candidacy

        Args:
            candidacy_id: Candidacy ID
            user_id: User ID to unassign
        """
        await self.client.delete(
            f"/v1/candidacies/{candidacy_id}/assignments/{user_id}"
        )
        logger.info(f"Unassigned {user_id} from candidacy {candidacy_id}")
