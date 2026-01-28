"""
Tests for HERP Timeline API Client
"""

from unittest.mock import Mock

import pytest

from src.core.herp.timeline import TimelineAPI


class TestTimelineAPI:
    """Test TimelineAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create TimelineAPI instance"""
        return TimelineAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = TimelineAPI(mock_client)

        assert api.client == mock_client

    def test_list_comments(self, api, mock_client):
        """Test listing timeline comments"""
        mock_client.get.return_value = {
            "comments": [
                {
                    "id": "comment_1",
                    "comment": "Called candidate",
                    "createdAt": "2026-01-28T10:00:00Z",
                },
                {
                    "id": "comment_2",
                    "comment": "Scheduled interview",
                    "createdAt": "2026-01-28T11:00:00Z",
                },
            ]
        }

        result = api.list("cand_123")

        mock_client.get.assert_called_once_with(
            "/v1/candidacies/cand_123/timeline-comments"
        )
        assert len(result) == 2
        assert result[0]["id"] == "comment_1"
        assert result[1]["comment"] == "Scheduled interview"

    def test_list_comments_returns_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key if 'comments' not present"""
        mock_client.get.return_value = {"data": [{"id": "comment_1"}]}

        result = api.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "comment_1"

    def test_list_comments_empty(self, api, mock_client):
        """Test listing comments when none exist"""
        mock_client.get.return_value = {"comments": []}

        result = api.list("cand_123")

        assert result == []

    def test_list_comments_no_data(self, api, mock_client):
        """Test list returns empty list when no data"""
        mock_client.get.return_value = {}

        result = api.list("cand_123")

        assert result == []

    def test_add_comment_text(self, api, mock_client):
        """Test adding plain text comment"""
        mock_client.post.return_value = {
            "id": "comment_new",
            "comment": "Great candidate!",
            "contentType": "text/plain",
        }

        result = api.add_comment("cand_123", "Great candidate!")

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_123/timeline-comments",
            json={"comment": "Great candidate!", "contentType": "text/plain"},
        )
        assert result["id"] == "comment_new"
        assert result["comment"] == "Great candidate!"

    def test_add_comment_markdown(self, api, mock_client):
        """Test adding markdown comment"""
        comment_text = (
            "# Interview Notes\n\n- Strong technical skills\n- Good culture fit"
        )
        mock_client.post.return_value = {
            "id": "comment_new",
            "comment": comment_text,
            "contentType": "text/markdown",
        }

        result = api.add_comment("cand_123", comment_text, content_type="text/markdown")

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["contentType"] == "text/markdown"
        assert result["contentType"] == "text/markdown"

    def test_add_comment_default_content_type(self, api, mock_client):
        """Test add_comment uses text/plain by default"""
        mock_client.post.return_value = {"id": "comment_new"}

        api.add_comment("cand_123", "Test comment")

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["contentType"] == "text/plain"

    def test_add_comment_empty_string(self, api, mock_client):
        """Test adding empty comment"""
        mock_client.post.return_value = {"id": "comment_new", "comment": ""}

        result = api.add_comment("cand_123", "")

        # Should allow empty comment (server validation)
        assert result["id"] == "comment_new"

    def test_add_comment_long_text(self, api, mock_client):
        """Test adding long comment"""
        long_comment = "A" * 10000  # 10,000 characters
        mock_client.post.return_value = {
            "id": "comment_new",
            "comment": long_comment,
        }

        result = api.add_comment("cand_123", long_comment)

        # Should handle long comments
        assert result["id"] == "comment_new"

    def test_add_comment_special_characters(self, api, mock_client):
        """Test adding comment with special characters"""
        comment_with_special = 'Comment with "quotes", <tags>, and émojis! 🎉'
        mock_client.post.return_value = {
            "id": "comment_new",
            "comment": comment_with_special,
        }

        result = api.add_comment("cand_123", comment_with_special)

        # Should preserve special characters
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["comment"] == comment_with_special


class TestTimelineAPIIntegration:
    """Integration-style tests for TimelineAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return TimelineAPI(mock_client)

    def test_list_and_add_workflow(self, api, mock_client):
        """Test typical workflow of listing then adding comment"""
        # First, list existing comments
        mock_client.get.return_value = {
            "comments": [{"id": "existing_1", "comment": "Existing comment"}]
        }
        existing = api.list("cand_123")
        assert len(existing) == 1

        # Then add new comment
        mock_client.post.return_value = {
            "id": "new_comment",
            "comment": "New comment",
        }
        new_comment = api.add_comment("cand_123", "New comment")
        assert new_comment["id"] == "new_comment"

    def test_multiple_comments_sequence(self, api, mock_client):
        """Test adding multiple comments in sequence"""
        mock_client.post.return_value = {"id": "comment_1"}

        # Add multiple comments
        api.add_comment("cand_123", "First comment")
        api.add_comment("cand_123", "Second comment")
        api.add_comment("cand_123", "Third comment")

        # Should have made 3 POST requests
        assert mock_client.post.call_count == 3

    def test_comment_with_different_content_types(self, api, mock_client):
        """Test adding comments with different content types"""
        mock_client.post.return_value = {"id": "comment_1"}

        # Add plain text comment
        api.add_comment("cand_123", "Plain text", content_type="text/plain")

        # Add markdown comment
        api.add_comment("cand_123", "# Markdown", content_type="text/markdown")

        # Should have made 2 requests with different content types
        assert mock_client.post.call_count == 2


class TestTimelineAPIEdgeCases:
    """Test edge cases for TimelineAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return TimelineAPI(Mock())

    def test_list_with_special_characters_in_id(self, api):
        """Test list with special characters in candidacy ID"""
        api.client.get.return_value = {"comments": []}

        # Should handle special characters in URL
        api.list("cand_123-abc_456")

        # Should have made request
        assert api.client.get.called

    def test_add_comment_unicode_characters(self, api):
        """Test add_comment with unicode characters"""
        comment = "日本語のコメント"  # Japanese text
        api.client.post.return_value = {"id": "comment_1", "comment": comment}

        result = api.add_comment("cand_123", comment)

        # Should preserve unicode
        call_args = api.client.post.call_args
        assert call_args[1]["json"]["comment"] == comment

    def test_add_comment_newlines(self, api):
        """Test add_comment preserves newlines"""
        comment = "Line 1\nLine 2\nLine 3"
        api.client.post.return_value = {"id": "comment_1"}

        api.add_comment("cand_123", comment)

        # Should preserve newlines
        call_args = api.client.post.call_args
        assert "\n" in call_args[1]["json"]["comment"]

    def test_add_comment_tabs(self, api):
        """Test add_comment preserves tabs"""
        comment = "Column1\tColumn2\tColumn3"
        api.client.post.return_value = {"id": "comment_1"}

        api.add_comment("cand_123", comment)

        # Should preserve tabs
        call_args = api.client.post.call_args
        assert "\t" in call_args[1]["json"]["comment"]

    def test_list_returns_chronological_order(self, api):
        """Test list returns comments in order"""
        api.client.get.return_value = {
            "comments": [
                {"id": "1", "createdAt": "2026-01-28T10:00:00Z"},
                {"id": "2", "createdAt": "2026-01-28T11:00:00Z"},
                {"id": "3", "createdAt": "2026-01-28T12:00:00Z"},
            ]
        }

        result = api.list("cand_123")

        # Should return in original order
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
        assert result[2]["id"] == "3"

    def test_add_comment_invalid_content_type(self, api):
        """Test add_comment with invalid content type (server should validate)"""
        api.client.post.return_value = {"id": "comment_1"}

        # Client allows any content_type, server validates
        api.add_comment("cand_123", "Test", content_type="application/json")

        # Should make request (server will validate)
        assert api.client.post.called
