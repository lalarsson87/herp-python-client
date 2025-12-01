#!/usr/bin/env python3
"""
HERP Files API Client

Handles file operations including uploading, downloading, and listing
candidate documents (resumes, portfolios, etc.).
"""

from typing import Dict, Any, List
from pathlib import Path

from ..utils.validators import validate_list_response
from ..utils.logging import get_logger
from .base_client import HerpBaseClient
from .schemas import HerpFilesListResponse
from .mixins import BatchFetchMixin


logger = get_logger(__name__)


class FilesAPI(BatchFetchMixin):
    """
    Files API Client

    Provides methods for managing candidate files and documents.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize files API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpFilesListResponse, strict=False)
    def list(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """
        List files attached to a candidacy

        Args:
            candidacy_id: Candidacy ID

        Returns:
            List of file metadata
        """
        data = self.client.get(f"/v1/candidacies/{candidacy_id}/files")
        return data.get("files", data.get("data", []))

    def list_for_multiple(
        self,
        candidacy_ids: List[str],
        max_workers: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch files for multiple candidacies efficiently (solves N+1 problem)

        Args:
            candidacy_ids: List of candidacy IDs
            max_workers: Maximum concurrent requests

        Returns:
            Dictionary mapping candidacy_id to list of files
        """
        results = self._batch_fetch(
            ids=candidacy_ids,
            fetch_function=self.list,
            max_workers=max_workers,
            resource_name="files"
        )

        # Log total file count (additional info beyond mixin logging)
        total_files = sum(len(files) for files in results.values())
        logger.info(f"Total files fetched: {total_files}")

        return results

    def download(
        self,
        candidacy_id: str,
        file_id: str
    ) -> bytes:
        """
        Download a file

        Args:
            candidacy_id: Candidacy ID
            file_id: File ID

        Returns:
            File content as bytes
        """
        response = self.client._make_request(
            "GET",
            f"/v1/candidacies/{candidacy_id}/files/{file_id}/download"
        )
        return response.content

    def upload(
        self,
        candidacy_id: str,
        file_path: Path,
        file_type: str = "other"
    ) -> Dict[str, Any]:
        """
        Upload a file

        Args:
            candidacy_id: Candidacy ID
            file_path: Path to file to upload
            file_type: File type (resume, career_summary, or other)

        Returns:
            Uploaded file metadata
        """
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            data = {'fileType': file_type}

            response = self.client._make_request(
                "POST",
                f"/v1/candidacies/{candidacy_id}/files",
                files=files,
                data=data
            )
            return response.json()
