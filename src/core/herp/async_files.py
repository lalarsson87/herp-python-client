#!/usr/bin/env python3
"""
HERP Async Files API Client

Async version of file upload/download operations.
"""

import asyncio
from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path

from ..utils.validators import validate_list_response, validate_single_response
from ..utils.logging import get_logger
from .async_base_client import AsyncHerpBaseClient
from .schemas import HerpFilesListResponse, HerpFileResponse


logger = get_logger(__name__)


class AsyncFilesAPI:
    """
    Async Files API Client

    Provides async methods for file operations.

    Usage:
        async with AsyncHerpBaseClient(config) as base_client:
            api = AsyncFilesAPI(base_client)
            files = await api.list("candidacy_123")
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async files API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpFilesListResponse, strict=False)
    async def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List files for a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of file records
        """
        data = await self.client.get(f"/v1/candidacies/{candidacy_id}/files")
        return data.get("files", data.get("data", []))

    async def list_for_multiple(
        self,
        candidacy_ids: List[str],
        max_concurrency: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch fetch files for multiple candidacies (async)

        Args:
            candidacy_ids: List of candidacy IDs
            max_concurrency: Maximum concurrent requests

        Returns:
            Dictionary mapping candidacy_id to list of files
        """
        results = {}
        errors = {}

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)

        async def fetch_files(candidacy_id: str):
            async with semaphore:
                try:
                    files = await self.list(candidacy_id)
                    return candidacy_id, files, None
                except Exception as e:
                    logger.warning(f"Failed to fetch files for {candidacy_id}: {e}")
                    return candidacy_id, [], str(e)

        # Fetch concurrently
        tasks = [fetch_files(cid) for cid in candidacy_ids]
        responses = await asyncio.gather(*tasks)

        # Process results
        for candidacy_id, files, error in responses:
            results[candidacy_id] = files
            if error:
                errors[candidacy_id] = error
                if hasattr(self.client, 'metrics'):
                    self.client.metrics.increment_counter(
                        "herp.batch.files.errors",
                        labels={"error": "fetch_failed"}
                    )

        # Log summary
        total_files = sum(len(files) for files in results.values())
        logger.info(
            f"Batch fetched files for {len(candidacy_ids)} candidacies: "
            f"{len(results)} successful, {len(errors)} errors, "
            f"{total_files} total files"
        )

        # Record metrics
        if hasattr(self.client, 'metrics'):
            self.client.metrics.increment_counter(
                "herp.batch.files.operations",
                labels={"status": "success"}
            )

        return results

    @validate_single_response(HerpFileResponse, strict=False)
    async def upload(
        self,
        candidacy_id: str,
        file_path: str,
        file_type: str = "other",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload file to candidacy

        Args:
            candidacy_id: Candidacy ID
            file_path: Path to file to upload
            file_type: File type (resume, career_summary, other)
            description: Optional file description

        Returns:
            Uploaded file record

        Usage:
            file = await api.upload(
                "cand_123",
                "/path/to/resume.pdf",
                file_type="resume"
            )
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Prepare multipart upload
        files = {
            "file": (path.name, file_content, "application/octet-stream")
        }
        data_fields = {"type": file_type}
        if description:
            data_fields["description"] = description

        # Upload
        response_data = await self.client.post(
            f"/v1/candidacies/{candidacy_id}/files",
            files=files,
            data=data_fields
        )

        logger.info(f"Uploaded {path.name} for candidacy {candidacy_id}")
        return response_data.get("file", response_data.get("data", response_data))

    async def download(
        self,
        candidacy_id: str,
        file_id: str,
        save_path: Optional[str] = None
    ) -> bytes:
        """
        Download file from candidacy

        Args:
            candidacy_id: Candidacy ID
            file_id: File ID
            save_path: Optional path to save file (if not provided, returns bytes)

        Returns:
            File content as bytes

        Usage:
            # Download to memory
            content = await api.download("cand_123", "file_456")

            # Download to file
            await api.download("cand_123", "file_456", "/path/to/save.pdf")
        """
        content = await self.client.download_file(
            f"/v1/candidacies/{candidacy_id}/files/{file_id}/download"
        )

        if save_path:
            path = Path(save_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(content)
            logger.info(f"Downloaded file {file_id} to {save_path}")

        return content

    async def delete(self, candidacy_id: str, file_id: str) -> None:
        """
        Delete file from candidacy

        Args:
            candidacy_id: Candidacy ID
            file_id: File ID
        """
        await self.client.delete(
            f"/v1/candidacies/{candidacy_id}/files/{file_id}"
        )
        logger.info(f"Deleted file {file_id} from candidacy {candidacy_id}")
