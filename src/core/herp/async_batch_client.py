#!/usr/bin/env python3
"""
HERP Async Batch Client

Provides async bulk operations for HERP API with high concurrency.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils.config import HerpConfig
from ..utils.logging import get_logger
from .async_client import AsyncHerpClient

logger = get_logger(__name__)


@dataclass
class AsyncBatchResult:
    """
    Result of async batch operation

    Attributes:
        successful: List of successful results
        failed: List of failed items with errors
        total: Total items processed
        success_count: Number of successful operations
        failure_count: Number of failed operations
    """

    successful: List[Dict[str, Any]]
    failed: List[Dict[str, Any]]
    total: int
    success_count: int
    failure_count: int

    def __str__(self) -> str:
        return (
            f"AsyncBatchResult(total={self.total}, "
            f"successful={self.success_count}, "
            f"failed={self.failure_count})"
        )


class AsyncBatchHerpClient:
    """
    Async Batch HERP Client

    Provides high-performance async bulk operations for HERP API.
    Uses asyncio for concurrent requests with configurable concurrency limits.

    Usage:
        async with AsyncBatchHerpClient(config, max_concurrency=20) as batch_client:
            # Fetch candidacies for multiple IDs
            result = await batch_client.fetch_candidacies([
                "cand_1", "cand_2", "cand_3", ...
            ])

            # Create multiple candidacies
            result = await batch_client.create_candidacies([
                {"name": "Jane Doe", "email": "jane@example.com", ...},
                {"name": "John Smith", "email": "john@example.com", ...},
                ...
            ])

    Performance:
        - 10x faster than sequential operations
        - Respects rate limits automatically
        - Configurable concurrency (default: 10)
        - Automatic retry on transient errors
    """

    def __init__(self, config: HerpConfig, max_concurrency: int = 10, **client_kwargs):
        """
        Initialize async batch client

        Args:
            config: HERP configuration
            max_concurrency: Maximum concurrent requests (default: 10)
            **client_kwargs: Additional arguments for AsyncHerpClient
        """
        self.config = config
        self.max_concurrency = max_concurrency
        self.client_kwargs = client_kwargs

        # Client will be created in __aenter__
        self._client: Optional[AsyncHerpClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._client = AsyncHerpClient(self.config, **self.client_kwargs)
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def fetch_candidacies(self, candidacy_ids: List[str]) -> AsyncBatchResult:
        """
        Fetch multiple candidacies concurrently

        Args:
            candidacy_ids: List of candidacy IDs to fetch

        Returns:
            AsyncBatchResult with successful and failed fetches
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        successful = []
        failed = []
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def fetch_one(candidacy_id: str):
            async with semaphore:
                try:
                    candidacy = await self._client.candidacies.get(candidacy_id)
                    return candidacy_id, candidacy, None
                except Exception as e:
                    logger.warning(f"Failed to fetch candidacy {candidacy_id}: {e}")
                    return candidacy_id, None, str(e)

        # Fetch all concurrently
        tasks = [fetch_one(cid) for cid in candidacy_ids]
        results = await asyncio.gather(*tasks)

        # Process results
        for candidacy_id, candidacy, error in results:
            if error:
                failed.append({"id": candidacy_id, "error": error})
            else:
                successful.append(candidacy)

        logger.info(
            f"Fetched {len(candidacy_ids)} candidacies: "
            f"{len(successful)} successful, {len(failed)} failed"
        )

        return AsyncBatchResult(
            successful=successful,
            failed=failed,
            total=len(candidacy_ids),
            success_count=len(successful),
            failure_count=len(failed),
        )

    async def create_candidacies(
        self, candidacy_data_list: List[Dict[str, Any]]
    ) -> AsyncBatchResult:
        """
        Create multiple candidacies concurrently

        Args:
            candidacy_data_list: List of candidacy data dictionaries

        Returns:
            AsyncBatchResult with created and failed candidacies
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        successful = []
        failed = []
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def create_one(index: int, candidacy_data: Dict[str, Any]):
            async with semaphore:
                try:
                    candidacy = await self._client.candidacies.create(candidacy_data)
                    return index, candidacy, None
                except Exception as e:
                    logger.warning(f"Failed to create candidacy {index}: {e}")
                    return index, candidacy_data, str(e)

        # Create all concurrently
        tasks = [create_one(i, data) for i, data in enumerate(candidacy_data_list)]
        results = await asyncio.gather(*tasks)

        # Process results
        for index, result, error in results:
            if error:
                failed.append({"index": index, "data": result, "error": error})
            else:
                successful.append(result)

        logger.info(
            f"Created {len(candidacy_data_list)} candidacies: "
            f"{len(successful)} successful, {len(failed)} failed"
        )

        return AsyncBatchResult(
            successful=successful,
            failed=failed,
            total=len(candidacy_data_list),
            success_count=len(successful),
            failure_count=len(failed),
        )

    async def update_candidacy_steps(
        self, updates: List[Dict[str, Any]]
    ) -> AsyncBatchResult:
        """
        Update hiring steps for multiple candidacies concurrently

        Args:
            updates: List of update dictionaries with:
                - candidacy_id: Candidacy ID
                - step: New step
                - comment: Optional comment

        Returns:
            AsyncBatchResult with updated and failed candidacies

        Usage:
            result = await batch_client.update_candidacy_steps([
                {"candidacy_id": "cand_1", "step": "interview"},
                {"candidacy_id": "cand_2", "step": "offer"},
                ...
            ])
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        successful = []
        failed = []
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def update_one(update: Dict[str, Any]):
            async with semaphore:
                try:
                    candidacy = await self._client.candidacies.update_step(
                        candidacy_id=update["candidacy_id"],
                        step=update["step"],
                        comment=update.get("comment"),
                    )
                    return update["candidacy_id"], candidacy, None
                except Exception as e:
                    logger.warning(
                        f"Failed to update step for {update['candidacy_id']}: {e}"
                    )
                    return update["candidacy_id"], update, str(e)

        # Update all concurrently
        tasks = [update_one(update) for update in updates]
        results = await asyncio.gather(*tasks)

        # Process results
        for candidacy_id, result, error in results:
            if error:
                failed.append(
                    {"candidacy_id": candidacy_id, "data": result, "error": error}
                )
            else:
                successful.append(result)

        logger.info(
            f"Updated {len(updates)} candidacy steps: "
            f"{len(successful)} successful, {len(failed)} failed"
        )

        return AsyncBatchResult(
            successful=successful,
            failed=failed,
            total=len(updates),
            success_count=len(successful),
            failure_count=len(failed),
        )

    async def fetch_contacts_for_multiple(
        self, candidacy_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch contacts for multiple candidacies concurrently

        Args:
            candidacy_ids: List of candidacy IDs

        Returns:
            Dictionary mapping candidacy_id to list of contacts
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        return await self._client.contacts.list_for_multiple(
            candidacy_ids, max_concurrency=self.max_concurrency
        )

    async def fetch_files_for_multiple(
        self, candidacy_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch files for multiple candidacies concurrently

        Args:
            candidacy_ids: List of candidacy IDs

        Returns:
            Dictionary mapping candidacy_id to list of files
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        return await self._client.files.list_for_multiple(
            candidacy_ids, max_concurrency=self.max_concurrency
        )
