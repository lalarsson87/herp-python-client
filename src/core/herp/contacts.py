#!/usr/bin/env python3
"""
HERP Contacts API Client

Handles interview and contact-related operations for candidates.
"""

from typing import Any, Dict, List

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response
from .base_client import HerpBaseClient
from .mixins import BatchFetchMixin
from .schemas import HerpContactsListResponse

logger = get_logger(__name__)


class ContactsAPI(BatchFetchMixin):
    """
    Contacts API Client

    Provides methods for managing candidate interviews and contacts.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize contacts API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpContactsListResponse, strict=False)
    def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List contacts/interviews for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of contact records
        """
        data = self.client.get(f"/v1/candidacies/{candidacy_id}/contacts")
        return data.get("contacts", data.get("data", []))

    def list_for_multiple(
        self, candidacy_ids: List[str], max_workers: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch contacts for multiple candidacies efficiently (solves N+1 problem)

        Uses concurrent requests with rate limiting to minimize API calls.
        For 1000 candidacies, reduces from 1001 calls to ~200 concurrent batches.

        Args:
            candidacy_ids: List of candidacy IDs
            max_workers: Maximum concurrent requests (respects rate limits)

        Returns:
            Dictionary mapping candidacy_id to list of contacts

        Example:
            >>> contacts_map = client.contacts.list_for_multiple(candidacy_ids)
            >>> for candidacy_id, contacts in contacts_map.items():
            ...     print(f"Candidacy {candidacy_id}: {len(contacts)} contacts")
        """
        return self._batch_fetch(
            ids=candidacy_ids,
            fetch_function=self.list,
            max_workers=max_workers,
            resource_name="contacts",
        )

    def create(self, candidacy_id: str, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new contact/interview

        Args:
            candidacy_id: Candidacy ID
            contact_data: Contact data

        Returns:
            Created contact record
        """
        return self.client.post(
            f"/v1/candidacies/{candidacy_id}/contacts", json=contact_data
        )
