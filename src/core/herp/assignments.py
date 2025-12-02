#!/usr/bin/env python3
"""
HERP Assignments API Client

Handles team member assignment operations for candidates.
"""

from typing import Dict, Any, List

from ..utils.logging import get_logger
from .base_client import HerpBaseClient


logger = get_logger(__name__)


class AssignmentsAPI:
    """
    Assignments API Client

    Provides methods for managing team member assignments to candidates.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize assignments API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List team member assignments for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of assignment records
        """
        data = self.client.get(f"/v1/candidacies/{candidacy_id}/assignments")
        return data.get("assignments", data.get("data", []))

    def assign(
        self,
        candidacy_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Assign team member to candidacy

        Args:
            candidacy_id: Candidacy ID
            user_id: User ID to assign

        Returns:
            Assignment record
        """
        return self.client.post(
            f"/v1/candidacies/{candidacy_id}/assignments",
            json={"userId": user_id}
        )

    def remove(
        self,
        candidacy_id: str,
        assignment_id: str
    ) -> Dict[str, Any]:
        """
        Remove team member assignment

        Args:
            candidacy_id: Candidacy ID
            assignment_id: Assignment ID

        Returns:
            Empty dict on success
        """
        return self.client.delete(
            f"/v1/candidacies/{candidacy_id}/assignments/{assignment_id}"
        )
