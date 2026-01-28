"""
Tests for HERP Files API Client
"""

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.core.herp.files import FilesAPI


class TestFilesAPI:
    """Test FilesAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create FilesAPI instance"""
        return FilesAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = FilesAPI(mock_client)

        assert api.client == mock_client

    def test_list_files(self, api, mock_client):
        """Test listing files for candidacy"""
        mock_client.get.return_value = {
            "files": [
                {"id": "file_1", "filename": "resume.pdf", "fileType": "resume"},
                {
                    "id": "file_2",
                    "filename": "portfolio.pdf",
                    "fileType": "career_summary",
                },
            ]
        }

        result = api.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/files")
        assert len(result) == 2
        assert result[0]["filename"] == "resume.pdf"
        assert result[1]["fileType"] == "career_summary"

    def test_list_files_returns_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key if 'files' not present"""
        mock_client.get.return_value = {"data": [{"id": "file_1"}]}

        result = api.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "file_1"

    def test_list_files_empty(self, api, mock_client):
        """Test listing files when none exist"""
        mock_client.get.return_value = {"files": []}

        result = api.list("cand_123")

        assert result == []

    def test_list_files_no_data(self, api, mock_client):
        """Test list returns empty list when no data"""
        mock_client.get.return_value = {}

        result = api.list("cand_123")

        assert result == []

    def test_list_for_multiple(self, api, mock_client):
        """Test batch fetching files for multiple candidacies"""

        def mock_list(candidacy_id):
            return [{"id": f"file_{candidacy_id}"}]

        with patch.object(api, "list", side_effect=mock_list):
            result = api.list_for_multiple(
                candidacy_ids=["cand_1", "cand_2", "cand_3"], max_workers=2
            )

            # Should return dict mapping candidacy_id to files
            assert len(result) == 3
            assert result["cand_1"] == [{"id": "file_cand_1"}]
            assert result["cand_2"] == [{"id": "file_cand_2"}]
            assert result["cand_3"] == [{"id": "file_cand_3"}]

    def test_list_for_multiple_logs_total_count(self, api, mock_client):
        """Test list_for_multiple logs total file count"""

        def mock_list(candidacy_id):
            # Return different number of files for each candidacy
            if candidacy_id == "cand_1":
                return [{"id": "f1"}, {"id": "f2"}]
            elif candidacy_id == "cand_2":
                return [{"id": "f3"}]
            return []

        with patch.object(api, "list", side_effect=mock_list):
            with patch("src.core.herp.files.logger") as mock_logger:
                api.list_for_multiple(["cand_1", "cand_2", "cand_3"])

                # Should log total file count
                assert mock_logger.info.called
                call_args = str(mock_logger.info.call_args)
                assert "3" in call_args  # Total of 3 files

    def test_list_for_multiple_empty_ids(self, api):
        """Test batch fetch with empty ID list"""
        result = api.list_for_multiple(candidacy_ids=[])

        assert result == {}

    def test_download_file(self, api, mock_client):
        """Test downloading a file"""
        mock_response = Mock()
        mock_response.content = b"PDF file content here"
        mock_client._make_request.return_value = mock_response

        result = api.download("cand_123", "file_456")

        mock_client._make_request.assert_called_once_with(
            "GET", "/v1/candidacies/cand_123/files/file_456/download"
        )
        assert result == b"PDF file content here"
        assert isinstance(result, bytes)

    def test_download_file_empty_content(self, api, mock_client):
        """Test downloading empty file"""
        mock_response = Mock()
        mock_response.content = b""
        mock_client._make_request.return_value = mock_response

        result = api.download("cand_123", "file_456")

        assert result == b""

    def test_download_file_large_content(self, api, mock_client):
        """Test downloading large file"""
        large_content = b"X" * 10_000_000  # 10MB
        mock_response = Mock()
        mock_response.content = large_content
        mock_client._make_request.return_value = mock_response

        result = api.download("cand_123", "file_456")

        assert len(result) == 10_000_000

    def test_upload_file(self, api, mock_client):
        """Test uploading a file"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "file_new",
            "filename": "resume.pdf",
            "fileType": "resume",
        }
        mock_client._make_request.return_value = mock_response

        file_path = Path("/tmp/resume.pdf")

        with patch("builtins.open", mock_open(read_data=b"PDF content")):
            result = api.upload("cand_123", file_path, file_type="resume")

        # Should make POST request with file
        assert mock_client._make_request.called
        call_args = mock_client._make_request.call_args
        assert call_args[0][0] == "POST"
        assert "/v1/candidacies/cand_123/files" in call_args[0][1]
        assert result["id"] == "file_new"

    def test_upload_file_default_type(self, api, mock_client):
        """Test upload uses 'other' as default file type"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new"}
        mock_client._make_request.return_value = mock_response

        file_path = Path("/tmp/document.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            api.upload("cand_123", file_path)

        # Should use 'other' as default
        call_args = mock_client._make_request.call_args
        assert call_args[1]["data"]["fileType"] == "other"

    def test_upload_file_career_summary(self, api, mock_client):
        """Test uploading career summary"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "file_new",
            "fileType": "career_summary",
        }
        mock_client._make_request.return_value = mock_response

        file_path = Path("/tmp/career_summary.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            result = api.upload("cand_123", file_path, file_type="career_summary")

        assert result["fileType"] == "career_summary"

    def test_upload_file_preserves_filename(self, api, mock_client):
        """Test upload preserves original filename"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new"}
        mock_client._make_request.return_value = mock_response

        file_path = Path("/tmp/my_resume_2026.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            api.upload("cand_123", file_path)

        # Should preserve filename
        call_args = mock_client._make_request.call_args
        files_arg = call_args[1]["files"]
        assert "my_resume_2026.pdf" in str(files_arg)

    def test_inherits_from_batch_fetch_mixin(self, api):
        """Test FilesAPI inherits from BatchFetchMixin"""
        from src.core.herp.mixins import BatchFetchMixin

        assert isinstance(api, BatchFetchMixin)

    def test_has_batch_fetch_method(self, api):
        """Test FilesAPI has _batch_fetch method from mixin"""
        assert hasattr(api, "_batch_fetch")
        assert callable(api._batch_fetch)


class TestFilesAPIIntegration:
    """Integration-style tests for FilesAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return FilesAPI(mock_client)

    def test_upload_and_list_workflow(self, api, mock_client):
        """Test typical workflow of uploading then listing files"""
        # First upload a file
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new", "filename": "resume.pdf"}
        mock_client._make_request.return_value = mock_response

        file_path = Path("/tmp/resume.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            uploaded = api.upload("cand_123", file_path)
        assert uploaded["id"] == "file_new"

        # Then list files
        mock_client.get.return_value = {
            "files": [{"id": "file_new", "filename": "resume.pdf"}]
        }
        files = api.list("cand_123")
        assert len(files) == 1

    def test_upload_download_roundtrip(self, api, mock_client):
        """Test uploading then downloading a file"""
        # Upload
        mock_upload_response = Mock()
        mock_upload_response.json.return_value = {"id": "file_123"}
        mock_client._make_request.return_value = mock_upload_response

        file_content = b"Original file content"
        file_path = Path("/tmp/test.pdf")

        with patch("builtins.open", mock_open(read_data=file_content)):
            uploaded = api.upload("cand_123", file_path)

        # Download
        mock_download_response = Mock()
        mock_download_response.content = file_content
        mock_client._make_request.return_value = mock_download_response

        downloaded = api.download("cand_123", uploaded["id"])

        # Should get same content back
        assert downloaded == file_content

    def test_batch_fetch_files_for_multiple_candidacies(self, api, mock_client):
        """Test fetching files for multiple candidacies"""
        responses = {
            "cand_1": {"files": [{"id": "f1"}, {"id": "f2"}]},
            "cand_2": {"files": [{"id": "f3"}]},
            "cand_3": {"files": []},
        }

        def mock_get(path, **kwargs):
            for cand_id, response in responses.items():
                if cand_id in path:
                    return response
            return {"files": []}

        mock_client.get.side_effect = mock_get

        result = api.list_for_multiple(["cand_1", "cand_2", "cand_3"])

        # Should have fetched files for all candidacies
        assert len(result["cand_1"]) == 2
        assert len(result["cand_2"]) == 1
        assert len(result["cand_3"]) == 0


class TestFilesAPIEdgeCases:
    """Test edge cases for FilesAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return FilesAPI(Mock())

    def test_download_binary_content(self, api):
        """Test downloading various binary file types"""
        mock_response = Mock()
        mock_response.content = bytes([0, 1, 2, 255, 254, 253])  # Binary data
        api.client._make_request.return_value = mock_response

        result = api.download("cand_123", "file_456")

        # Should handle binary content
        assert result == bytes([0, 1, 2, 255, 254, 253])

    def test_upload_file_with_spaces_in_name(self, api):
        """Test uploading file with spaces in filename"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new"}
        api.client._make_request.return_value = mock_response

        file_path = Path("/tmp/My Resume 2026.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            result = api.upload("cand_123", file_path)

        # Should handle spaces in filename
        assert result["id"] == "file_new"

    def test_upload_file_with_unicode_in_name(self, api):
        """Test uploading file with unicode characters in filename"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new"}
        api.client._make_request.return_value = mock_response

        file_path = Path("/tmp/履歴書.pdf")  # "Resume" in Japanese

        with patch("builtins.open", mock_open(read_data=b"content")):
            result = api.upload("cand_123", file_path)

        assert result["id"] == "file_new"

    def test_list_for_multiple_with_varying_file_counts(self, api):
        """Test batch fetch with varying number of files per candidacy"""

        def mock_list(candidacy_id):
            counts = {"cand_1": 0, "cand_2": 5, "cand_3": 1, "cand_4": 10}
            count = counts.get(candidacy_id, 0)
            return [{"id": f"file_{i}"} for i in range(count)]

        with patch.object(api, "list", side_effect=mock_list):
            result = api.list_for_multiple(["cand_1", "cand_2", "cand_3", "cand_4"])

            # Should handle varying counts
            assert len(result["cand_1"]) == 0
            assert len(result["cand_2"]) == 5
            assert len(result["cand_3"]) == 1
            assert len(result["cand_4"]) == 10

    def test_upload_file_path_object(self, api):
        """Test upload accepts Path object"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "file_new"}
        api.client._make_request.return_value = mock_response

        # Use Path object (not string)
        file_path = Path("/tmp/test.pdf")

        with patch("builtins.open", mock_open(read_data=b"content")):
            result = api.upload("cand_123", file_path)

        assert result["id"] == "file_new"

    def test_download_file_with_special_id(self, api):
        """Test downloading file with special characters in ID"""
        mock_response = Mock()
        mock_response.content = b"content"
        api.client._make_request.return_value = mock_response

        # File ID with special characters
        api.download("cand_123", "file_abc-123_def")

        # Should handle special characters
        assert api.client._make_request.called
