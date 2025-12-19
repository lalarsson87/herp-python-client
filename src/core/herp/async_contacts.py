#!/usr/bin/env python3
"""
HERP Async Contacts API Client

Async version of interview/contact operations.
"""

import asyncio
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from ..utils.validators import validate_list_response, validate_single_response
from ..utils.logging import get_logger
from .async_base_client import AsyncHerpBaseClient
from .schemas import HerpContactsListResponse, HerpContactResponse
from .mixins import BatchFetchMixin


logger = get_logger(__name__)


class AsyncContactsAPI:
    """
    Async Contacts API Client

    Provides async methods for interview/contact operations.

    Usage:
        async with AsyncHerpBaseClient(config) as base_client:
            api = AsyncContactsAPI(base_client)
            contacts = await api.list("candidacy_123")
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async contacts API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpContactsListResponse, strict=False)
    async def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List contacts/interviews for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of contact records
        """
        data = await self.client.get(f"/v1/candidacies/{candidacy_id}/contacts")
        return data.get("contacts", data.get("data", []))

    async def list_for_multiple(
        self,
        candidacy_ids: List[str],
        max_concurrency: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch fetch contacts for multiple candidacies (async)

        Args:
            candidacy_ids: List of candidacy IDs
            max_concurrency: Maximum concurrent requests

        Returns:
            Dictionary mapping candidacy_id to list of contacts

        Usage:
            contacts_map = await api.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"],
                max_concurrency=10
            )
            # Returns: {
            #     "cand_1": [contact1, contact2],
            #     "cand_2": [contact3],
            #     "cand_3": []
            # }
        """
        results = {}
        errors = {}

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)

        async def fetch_contacts(candidacy_id: str):
            async with semaphore:
                try:
                    contacts = await self.list(candidacy_id)
                    return candidacy_id, contacts, None
                except Exception as e:
                    logger.warning(f"Failed to fetch contacts for {candidacy_id}: {e}")
                    return candidacy_id, [], str(e)

        # Fetch concurrently
        tasks = [fetch_contacts(cid) for cid in candidacy_ids]
        responses = await asyncio.gather(*tasks)

        # Process results
        for candidacy_id, contacts, error in responses:
            results[candidacy_id] = contacts
            if error:
                errors[candidacy_id] = error
                if hasattr(self.client, 'metrics'):
                    self.client.metrics.increment_counter(
                        "herp.batch.contacts.errors",
                        labels={"error": "fetch_failed"}
                    )

        # Log summary
        logger.info(
            f"Batch fetched contacts for {len(candidacy_ids)} candidacies: "
            f"{len(results)} successful, {len(errors)} errors"
        )

        # Record metrics
        if hasattr(self.client, 'metrics'):
            self.client.metrics.increment_counter(
                "herp.batch.contacts.operations",
                labels={"status": "success"}
            )

        return results

    @validate_single_response(HerpContactResponse, strict=False)
    async def create(
        self,
        candidacy_id: str,
        contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create new contact/interview

        Args:
            candidacy_id: Candidacy ID
            contact_data: Contact data (type, scheduled_at, interviewer_ids, etc.)

        Returns:
            Created contact record

        Usage:
            contact = await api.create("cand_123", {
                "type": "technical_interview",
                "scheduled_at": "2026-02-01T14:00:00Z",
                "interviewer_ids": ["user_456"]
            })
        """
        data = await self.client.post(
            f"/v1/candidacies/{candidacy_id}/contacts",
            json=contact_data
        )
        return data.get("contact", data.get("data", data))

    @validate_single_response(HerpContactResponse, strict=False)
    async def update(
        self,
        candidacy_id: str,
        contact_id: str,
        contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact/interview

        Args:
            candidacy_id: Candidacy ID
            contact_id: Contact ID
            contact_data: Updated contact data

        Returns:
            Updated contact record
        """
        data = await self.client.patch(
            f"/v1/candidacies/{candidacy_id}/contacts/{contact_id}",
            json=contact_data
        )
        return data.get("contact", data.get("data", data))

    async def delete(self, candidacy_id: str, contact_id: str) -> None:
        """
        Delete contact/interview

        Args:
            candidacy_id: Candidacy ID
            contact_id: Contact ID
        """
        await self.client.delete(
            f"/v1/candidacies/{candidacy_id}/contacts/{contact_id}"
        )
        logger.info(f"Deleted contact {contact_id} for candidacy {candidacy_id}")
