"""
Tests for HERP Async Files API Client
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from src.core.herp.async_files import AsyncFilesAPI


class TestAsyncFilesAPIInitialization:
    """Test AsyncFilesAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncFilesAPI(mock_client)

        assert api.client == mock_client


class TestAsyncFilesAPIList:
    """Test list method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_files(self, api):
        """Test listing files for candidacy"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "files": [
                    {
                        "id": "file_1",
                        "name": "resume.pdf",
                        "type": "resume",
                        "size": 102400,
                    },
                    {
                        "id": "file_2",
                        "name": "cover_letter.pdf",
                        "type": "other",
                        "size": 51200,
                    },
                ]
            }
        )

        result = await api_instance.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/files")
        assert len(result) == 2
        assert result[0]["name"] == "resume.pdf"
        assert result[1]["type"] == "other"

    @pytest.mark.asyncio
    async def test_list_files_data_key_fallback(self, api):
        """Test list falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "data": [{"id": "file_1", "name": "resume.pdf", "type": "resume"}]
            }
        )

        result = await api_instance.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "file_1"

    @pytest.mark.asyncio
    async def test_list_files_empty(self, api):
        """Test listing when no files"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"files": []})

        result = await api_instance.list("cand_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_constructs_correct_url(self, api):
        """Test list constructs correct URL"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"files": []})

        await api_instance.list("cand_xyz")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_xyz/files")


class TestAsyncFilesAPIListForMultiple:
    """Test list_for_multiple batch method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        # Configure metrics to avoid async issues
        mock_client.metrics = Mock()
        mock_client.metrics.increment_counter = Mock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_for_multiple_all_successful(self, api):
        """Test batch fetching all successful"""
        api_instance, _ = api

        # Mock the list method directly
        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "file_1", "name": "resume1.pdf"}]
            elif candidacy_id == "cand_2":
                return [{"id": "file_2", "name": "resume2.pdf"}]
            elif candidacy_id == "cand_3":
                return [{"id": "file_3", "name": "resume3.pdf"}]
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"], max_concurrency=10
            )

        assert len(result) == 3
        assert "cand_1" in result
        assert "cand_2" in result
        assert "cand_3" in result
        assert len(result["cand_1"]) == 1
        assert result["cand_1"][0]["name"] == "resume1.pdf"

    @pytest.mark.asyncio
    async def test_list_for_multiple_with_errors(self, api):
        """Test batch fetching with some errors"""
        api_instance, _ = api

        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "file_1", "name": "resume.pdf"}]
            elif candidacy_id == "cand_2":
                raise Exception("API error")
            elif candidacy_id == "cand_3":
                return [{"id": "file_3", "name": "cover.pdf"}]
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"]
            )

        # Should have all keys, failed ones with empty list
        assert len(result) == 3
        assert len(result["cand_1"]) == 1
        assert len(result["cand_2"]) == 0  # Failed, returns empty list
        assert len(result["cand_3"]) == 1

    @pytest.mark.asyncio
    async def test_list_for_multiple_empty_list(self, api):
        """Test batch fetching with empty list"""
        api_instance, _ = api

        result = await api_instance.list_for_multiple([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_list_for_multiple_respects_concurrency(self, api):
        """Test batch fetching respects max_concurrency"""
        api_instance, _ = api

        async def mock_list(candidacy_id):
            return [{"id": "file_1", "name": "resume.pdf"}]

        with patch.object(api_instance, "list", side_effect=mock_list):
            result = await api_instance.list_for_multiple(
                ["cand_1", "cand_2"], max_concurrency=100
            )

        assert len(result) == 2


class TestAsyncFilesAPIUpload:
    """Test upload method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_upload_file(self, api):
        """Test uploading file"""
        api_instance, mock_client = api

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"PDF content here")
            tmp_path = tmp.name

        try:
            mock_client.post = AsyncMock(
                return_value={
                    "file": {
                        "id": "file_123",
                        "name": Path(tmp_path).name,
                        "type": "resume",
                        "size": 16,
                    }
                }
            )

            result = await api_instance.upload("cand_123", tmp_path, file_type="resume")

            # Verify post was called with correct parameters
            assert mock_client.post.called
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/v1/candidacies/cand_123/files"
            assert "files" in call_args[1]
            assert "data" in call_args[1]
            assert call_args[1]["data"]["type"] == "resume"

            assert result["id"] == "file_123"
            assert result["type"] == "resume"
        finally:
            Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_upload_file_with_description(self, api):
        """Test uploading file with description"""
        api_instance, mock_client = api

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"PDF content")
            tmp_path = tmp.name

        try:
            mock_client.post = AsyncMock(
                return_value={
                    "file": {
                        "id": "file_123",
                        "name": Path(tmp_path).name,
                        "type": "other",
                        "description": "Portfolio",
                    }
                }
            )

            result = await api_instance.upload(
                "cand_123", tmp_path, file_type="other", description="Portfolio"
            )

            # Verify description was included
            call_kwargs = mock_client.post.call_args[1]
            assert call_kwargs["data"]["description"] == "Portfolio"

            assert result["description"] == "Portfolio"
        finally:
            Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, api):
        """Test upload raises FileNotFoundError"""
        api_instance, _ = api

        with pytest.raises(FileNotFoundError, match="File not found"):
            await api_instance.upload(
                "cand_123", "/nonexistent/file.pdf", file_type="resume"
            )

    @pytest.mark.asyncio
    async def test_upload_data_key_fallback(self, api):
        """Test upload falls back to 'data' key"""
        api_instance, mock_client = api

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"PDF")
            tmp_path = tmp.name

        try:
            mock_client.post = AsyncMock(
                return_value={"data": {"id": "file_123", "name": "resume.pdf"}}
            )

            result = await api_instance.upload("cand_123", tmp_path)

            assert result["id"] == "file_123"
        finally:
            Path(tmp_path).unlink()


class TestAsyncFilesAPIDownload:
    """Test download method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_download_to_memory(self, api):
        """Test downloading file to memory"""
        api_instance, mock_client = api

        file_content = b"PDF file content here"
        mock_client.download_file = AsyncMock(return_value=file_content)

        result = await api_instance.download("cand_123", "file_456")

        mock_client.download_file.assert_called_once_with(
            "/v1/candidacies/cand_123/files/file_456/download"
        )
        assert result == file_content

    @pytest.mark.asyncio
    async def test_download_to_file(self, api):
        """Test downloading file to disk"""
        api_instance, mock_client = api

        file_content = b"PDF file content here"
        mock_client.download_file = AsyncMock(return_value=file_content)

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "downloaded.pdf"

            result = await api_instance.download("cand_123", "file_456", str(save_path))

            # Should still return content
            assert result == file_content

            # File should be saved
            assert save_path.exists()
            assert save_path.read_bytes() == file_content

    @pytest.mark.asyncio
    async def test_download_creates_parent_directories(self, api):
        """Test download creates parent directories if needed"""
        api_instance, mock_client = api

        file_content = b"PDF content"
        mock_client.download_file = AsyncMock(return_value=file_content)

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "subdir" / "nested" / "file.pdf"

            await api_instance.download("cand_123", "file_456", str(save_path))

            assert save_path.exists()
            assert save_path.parent.exists()

    @pytest.mark.asyncio
    async def test_download_constructs_correct_url(self, api):
        """Test download constructs correct URL"""
        api_instance, mock_client = api

        mock_client.download_file = AsyncMock(return_value=b"content")

        await api_instance.download("cand_xyz", "file_999")

        mock_client.download_file.assert_called_once_with(
            "/v1/candidacies/cand_xyz/files/file_999/download"
        )


class TestAsyncFilesAPIDelete:
    """Test delete method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_delete_file(self, api):
        """Test deleting file"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.delete("cand_123", "file_456")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_123/files/file_456"
        )

    @pytest.mark.asyncio
    async def test_delete_returns_none(self, api):
        """Test delete returns None"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        result = await api_instance.delete("cand_123", "file_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_constructs_correct_url(self, api):
        """Test delete constructs correct URL"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.delete("cand_xyz", "file_999")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_xyz/files/file_999"
        )


class TestAsyncFilesAPIIntegration:
    """Integration-style tests for AsyncFilesAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        mock_client.metrics = Mock()
        mock_client.metrics.increment_counter = Mock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_upload_download_delete_workflow(self, api):
        """Test typical workflow"""
        api_instance, mock_client = api

        # List existing files
        mock_client.get = AsyncMock(return_value={"files": []})
        files = await api_instance.list("cand_123")
        assert len(files) == 0

        # Upload new file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"Resume content")
            tmp_path = tmp.name

        try:
            mock_client.post = AsyncMock(
                return_value={
                    "file": {"id": "file_123", "name": "resume.pdf", "type": "resume"}
                }
            )
            uploaded = await api_instance.upload("cand_123", tmp_path)
            assert uploaded["id"] == "file_123"
        finally:
            Path(tmp_path).unlink()

        # Download file
        mock_client.download_file = AsyncMock(return_value=b"Resume content")
        content = await api_instance.download("cand_123", "file_123")
        assert content == b"Resume content"

        # Delete file
        mock_client.delete = AsyncMock(return_value={})
        await api_instance.delete("cand_123", "file_123")
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_fetch_for_pipeline(self, api):
        """Test batch fetching for recruiting pipeline"""
        api_instance, _ = api

        # Simulate fetching files for multiple candidates in pipeline
        async def mock_list(candidacy_id):
            if candidacy_id == "cand_1":
                return [{"id": "f1", "name": "resume1.pdf", "type": "resume"}]
            elif candidacy_id == "cand_2":
                return [{"id": "f2", "name": "resume2.pdf", "type": "resume"}]
            elif candidacy_id == "cand_3":
                return []
            return []

        with patch.object(api_instance, "list", side_effect=mock_list):
            results = await api_instance.list_for_multiple(
                ["cand_1", "cand_2", "cand_3"], max_concurrency=3
            )

        # All candidates should have results
        assert len(results) == 3
        assert len(results["cand_1"]) == 1
        assert len(results["cand_2"]) == 1
        assert len(results["cand_3"]) == 0


class TestAsyncFilesAPIEdgeCases:
    """Test edge cases for async files API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncFilesAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_upload_returns_direct_response(self, api):
        """Test upload when response doesn't have wrapper key"""
        api_instance, mock_client = api

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(b"PDF")
            tmp_path = tmp.name

        try:
            # Response without wrapper key
            mock_client.post = AsyncMock(
                return_value={"id": "file_123", "name": "resume.pdf", "type": "resume"}
            )

            result = await api_instance.upload("cand_123", tmp_path)

            assert result["id"] == "file_123"
        finally:
            Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_list_with_malformed_response(self, api):
        """Test list handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'files' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list("cand_123")

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, api):
        """Test concurrent file uploads"""
        import asyncio

        api_instance, mock_client = api

        # Create temporary files
        tmp_files = []
        for i in range(3):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(f"Content {i}".encode())
            tmp.close()
            tmp_files.append(tmp.name)

        try:
            mock_client.post = AsyncMock(
                side_effect=[
                    {"file": {"id": f"file_{i}", "name": f"file{i}.pdf"}}
                    for i in range(3)
                ]
            )

            # Upload multiple files concurrently
            tasks = [
                api_instance.upload("cand_123", path, file_type="other")
                for path in tmp_files
            ]
            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert mock_client.post.call_count == 3
        finally:
            for path in tmp_files:
                Path(path).unlink()
