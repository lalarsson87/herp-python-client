"""
Tests for HERP Async Timeline API Client
"""

from unittest.mock import AsyncMock

import pytest

from src.core.herp.async_timeline import AsyncTimelineAPI


class TestAsyncTimelineAPIInitialization:
    """Test AsyncTimelineAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncTimelineAPI(mock_client)

        assert api.client == mock_client


class TestAsyncTimelineAPIList:
    """Test list method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncTimelineAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_timeline_comments(self, api):
        """Test listing timeline comments"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "timeline_comments": [
                    {
                        "id": "comment_1",
                        "comment": "Great interview",
                        "format": "text/plain",
                    },
                    {
                        "id": "comment_2",
                        "comment": "## Technical Skills\n\n- Python",
                        "format": "text/markdown",
                    },
                ]
            }
        )

        result = await api_instance.list("cand_123")

        mock_client.get.assert_called_once_with(
            "/v1/candidacies/cand_123/timeline-comments"
        )
        assert len(result) == 2
        assert result[0]["comment"] == "Great interview"
        assert result[1]["format"] == "text/markdown"

    @pytest.mark.asyncio
    async def test_list_timeline_comments_data_key_fallback(self, api):
        """Test list falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "data": [
                    {
                        "id": "comment_1",
                        "comment": "Great candidate",
                        "format": "text/plain",
                    }
                ]
            }
        )

        result = await api_instance.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "comment_1"

    @pytest.mark.asyncio
    async def test_list_timeline_comments_empty(self, api):
        """Test listing when no comments"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"timeline_comments": []})

        result = await api_instance.list("cand_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_constructs_correct_url(self, api):
        """Test list constructs correct URL"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"timeline_comments": []})

        await api_instance.list("cand_xyz")

        mock_client.get.assert_called_once_with(
            "/v1/candidacies/cand_xyz/timeline-comments"
        )


class TestAsyncTimelineAPIAdd:
    """Test add method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncTimelineAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_add_comment_plain_text(self, api):
        """Test adding plain text comment"""
        api_instance, mock_client = api

        comment_text = "Excellent technical skills demonstrated"

        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_123",
                    "comment": comment_text,
                    "format": "text/plain",
                }
            }
        )

        result = await api_instance.add("cand_123", comment_text)

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_123/timeline-comments",
            json={"comment": comment_text, "format": "text/plain"},
        )
        assert result["id"] == "comment_123"
        assert result["comment"] == comment_text

    @pytest.mark.asyncio
    async def test_add_comment_markdown(self, api):
        """Test adding markdown comment"""
        api_instance, mock_client = api

        comment_text = (
            "## Technical Interview\n\n- Strong problem solving\n- Great communication"
        )

        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_123",
                    "comment": comment_text,
                    "format": "text/markdown",
                }
            }
        )

        result = await api_instance.add(
            "cand_123", comment_text, format="text/markdown"
        )

        # Verify format was passed correctly
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["format"] == "text/markdown"

    @pytest.mark.asyncio
    async def test_add_comment_default_format(self, api):
        """Test add uses text/plain as default format"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_123",
                    "comment": "Test",
                    "format": "text/plain",
                }
            }
        )

        await api_instance.add("cand_123", "Test comment")

        # Verify default format
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["format"] == "text/plain"

    @pytest.mark.asyncio
    async def test_add_comment_data_key_fallback(self, api):
        """Test add falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={
                "data": {"id": "comment_123", "comment": "Test", "format": "text/plain"}
            }
        )

        result = await api_instance.add("cand_123", "Test")

        assert result["id"] == "comment_123"

    @pytest.mark.asyncio
    async def test_add_constructs_correct_url(self, api):
        """Test add constructs correct URL"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(return_value={"timeline_comment": {}})

        await api_instance.add("cand_xyz", "Test comment")

        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "/v1/candidacies/cand_xyz/timeline-comments"


class TestAsyncTimelineAPIIntegration:
    """Integration-style tests for AsyncTimelineAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncTimelineAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_and_add_workflow(self, api):
        """Test typical workflow: list, then add"""
        api_instance, mock_client = api

        # First, list existing comments
        mock_client.get = AsyncMock(return_value={"timeline_comments": []})
        comments = await api_instance.list("cand_123")
        assert len(comments) == 0

        # Add new comment
        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_1",
                    "comment": "Great candidate",
                    "format": "text/plain",
                }
            }
        )
        new_comment = await api_instance.add("cand_123", "Great candidate")
        assert new_comment["id"] == "comment_1"

        # List again (should show new comment)
        mock_client.get = AsyncMock(
            return_value={
                "timeline_comments": [
                    {
                        "id": "comment_1",
                        "comment": "Great candidate",
                        "format": "text/plain",
                    }
                ]
            }
        )
        comments = await api_instance.list("cand_123")
        assert len(comments) == 1

    @pytest.mark.asyncio
    async def test_add_multiple_comments_sequentially(self, api):
        """Test adding multiple comments in sequence"""
        api_instance, mock_client = api

        comments_to_add = [
            ("Phone screen completed", "text/plain"),
            ("## Technical Interview\n\n- Strong coding", "text/markdown"),
            ("Final decision: proceed to offer", "text/plain"),
        ]

        for i, (comment_text, format_type) in enumerate(comments_to_add):
            mock_client.post = AsyncMock(
                return_value={
                    "timeline_comment": {
                        "id": f"comment_{i}",
                        "comment": comment_text,
                        "format": format_type,
                    }
                }
            )
            result = await api_instance.add(
                "cand_123", comment_text, format=format_type
            )
            assert result["format"] == format_type


class TestAsyncTimelineAPIEdgeCases:
    """Test edge cases for async timeline API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncTimelineAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_add_returns_direct_response(self, api):
        """Test add when response doesn't have wrapper key"""
        api_instance, mock_client = api

        # Response without wrapper key
        mock_client.post = AsyncMock(
            return_value={
                "id": "comment_123",
                "comment": "Test",
                "format": "text/plain",
            }
        )

        result = await api_instance.add("cand_123", "Test")

        assert result["id"] == "comment_123"

    @pytest.mark.asyncio
    async def test_list_with_malformed_response(self, api):
        """Test list handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'timeline_comments' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list("cand_123")

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_add_comment_with_unicode(self, api):
        """Test adding comment with unicode characters"""
        api_instance, mock_client = api

        comment_text = "候補者は優秀です - Excellent candidate 🌟"

        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_123",
                    "comment": comment_text,
                    "format": "text/plain",
                }
            }
        )

        result = await api_instance.add("cand_123", comment_text)

        assert result["comment"] == comment_text

    @pytest.mark.asyncio
    async def test_add_empty_comment(self, api):
        """Test adding empty comment"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={
                "timeline_comment": {
                    "id": "comment_123",
                    "comment": "",
                    "format": "text/plain",
                }
            }
        )

        result = await api_instance.add("cand_123", "")

        # Should still work, API will handle validation
        assert result["id"] == "comment_123"

    @pytest.mark.asyncio
    async def test_concurrent_adds(self, api):
        """Test concurrent comment additions"""
        import asyncio

        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            side_effect=[
                {
                    "timeline_comment": {
                        "id": f"comment_{i}",
                        "comment": f"Comment {i}",
                        "format": "text/plain",
                    }
                }
                for i in range(3)
            ]
        )

        # Add multiple comments concurrently
        tasks = [api_instance.add("cand_123", f"Comment {i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert mock_client.post.call_count == 3
