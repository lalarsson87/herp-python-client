"""
Tests for HERP Async Assignments API Client
"""

import pytest
from unittest.mock import AsyncMock

from src.core.herp.async_assignments import AsyncAssignmentsAPI


class TestAsyncAssignmentsAPIInitialization:
    """Test AsyncAssignmentsAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncAssignmentsAPI(mock_client)

        assert api.client == mock_client


class TestAsyncAssignmentsAPIList:
    """Test list method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncAssignmentsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_assignments(self, api):
        """Test listing assignments for candidacy"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "assignments": [
                    {"user_id": "user_1", "role": "recruiter"},
                    {"user_id": "user_2", "role": "hiring_manager"},
                ]
            }
        )

        result = await api_instance.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/assignments")
        assert len(result) == 2
        assert result[0]["user_id"] == "user_1"
        assert result[0]["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_list_assignments_data_key_fallback(self, api):
        """Test list falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"data": [{"user_id": "user_1", "role": "interviewer"}]}
        )

        result = await api_instance.list("cand_123")

        assert len(result) == 1
        assert result[0]["user_id"] == "user_1"

    @pytest.mark.asyncio
    async def test_list_assignments_empty(self, api):
        """Test listing when no assignments"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"assignments": []})

        result = await api_instance.list("cand_123")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_constructs_correct_url(self, api):
        """Test list constructs correct URL"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(return_value={"assignments": []})

        await api_instance.list("cand_xyz")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_xyz/assignments")


class TestAsyncAssignmentsAPIAssign:
    """Test assign method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncAssignmentsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_assign_user(self, api):
        """Test assigning user to candidacy"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={
                "assignment": {
                    "user_id": "user_1",
                    "role": "recruiter",
                    "id": "assign_1",
                }
            }
        )

        result = await api_instance.assign("cand_123", "user_1")

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_123/assignments",
            json={"user_id": "user_1", "role": "recruiter"},
        )
        assert result["user_id"] == "user_1"
        assert result["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_assign_user_custom_role(self, api):
        """Test assigning user with custom role"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={"assignment": {"user_id": "user_1", "role": "hiring_manager"}}
        )

        result = await api_instance.assign("cand_123", "user_1", role="hiring_manager")

        # Verify role was passed correctly
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["role"] == "hiring_manager"

    @pytest.mark.asyncio
    async def test_assign_default_role_recruiter(self, api):
        """Test assign uses 'recruiter' as default role"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={"assignment": {"user_id": "user_1", "role": "recruiter"}}
        )

        await api_instance.assign("cand_123", "user_1")

        # Verify default role
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["role"] == "recruiter"

    @pytest.mark.asyncio
    async def test_assign_data_key_fallback(self, api):
        """Test assign falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            return_value={"data": {"user_id": "user_1", "role": "interviewer"}}
        )

        result = await api_instance.assign("cand_123", "user_1", role="interviewer")

        assert result["user_id"] == "user_1"

    @pytest.mark.asyncio
    async def test_assign_constructs_correct_url(self, api):
        """Test assign constructs correct URL"""
        api_instance, mock_client = api

        mock_client.post = AsyncMock(return_value={"assignment": {}})

        await api_instance.assign("cand_xyz", "user_999")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert call_args[0] == "/v1/candidacies/cand_xyz/assignments"


class TestAsyncAssignmentsAPIUnassign:
    """Test unassign method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncAssignmentsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_unassign_user(self, api):
        """Test unassigning user from candidacy"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.unassign("cand_123", "user_1")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_123/assignments/user_1"
        )

    @pytest.mark.asyncio
    async def test_unassign_returns_none(self, api):
        """Test unassign returns None"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        result = await api_instance.unassign("cand_123", "user_1")

        assert result is None

    @pytest.mark.asyncio
    async def test_unassign_constructs_correct_url(self, api):
        """Test unassign constructs correct URL"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value={})

        await api_instance.unassign("cand_xyz", "user_999")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_xyz/assignments/user_999"
        )


class TestAsyncAssignmentsAPIIntegration:
    """Integration-style tests for AsyncAssignmentsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncAssignmentsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_assign_unassign_workflow(self, api):
        """Test typical workflow: list, assign, list, unassign"""
        api_instance, mock_client = api

        # First, list existing assignments
        mock_client.get = AsyncMock(return_value={"assignments": []})
        assignments = await api_instance.list("cand_123")
        assert len(assignments) == 0

        # Assign a user
        mock_client.post = AsyncMock(
            return_value={"assignment": {"user_id": "user_1", "role": "recruiter"}}
        )
        new_assignment = await api_instance.assign("cand_123", "user_1")
        assert new_assignment["user_id"] == "user_1"

        # List again (should show new assignment)
        mock_client.get = AsyncMock(
            return_value={"assignments": [{"user_id": "user_1", "role": "recruiter"}]}
        )
        assignments = await api_instance.list("cand_123")
        assert len(assignments) == 1

        # Unassign user
        mock_client.delete = AsyncMock(return_value={})
        await api_instance.unassign("cand_123", "user_1")

        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_multiple_users(self, api):
        """Test assigning multiple users with different roles"""
        api_instance, mock_client = api

        assignments_to_create = [
            ("user_1", "recruiter"),
            ("user_2", "hiring_manager"),
            ("user_3", "interviewer"),
        ]

        for user_id, role in assignments_to_create:
            mock_client.post = AsyncMock(
                return_value={"assignment": {"user_id": user_id, "role": role}}
            )
            result = await api_instance.assign("cand_123", user_id, role=role)
            assert result["role"] == role


class TestAsyncAssignmentsAPIEdgeCases:
    """Test edge cases for async assignments API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncAssignmentsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_list_with_malformed_response(self, api):
        """Test list handles malformed response"""
        api_instance, mock_client = api

        # Response with neither 'assignments' nor 'data' key
        mock_client.get = AsyncMock(return_value={})

        result = await api_instance.list("cand_123")

        # Should return empty list
        assert result == []

    @pytest.mark.asyncio
    async def test_assign_returns_direct_response(self, api):
        """Test assign when response doesn't have assignment or data key"""
        api_instance, mock_client = api

        # Response without wrapper key
        mock_client.post = AsyncMock(
            return_value={"user_id": "user_1", "role": "recruiter", "id": "assign_1"}
        )

        result = await api_instance.assign("cand_123", "user_1")

        # Should return the direct response
        assert result["user_id"] == "user_1"

    @pytest.mark.asyncio
    async def test_concurrent_assignments(self, api):
        """Test concurrent assignment operations"""
        import asyncio

        api_instance, mock_client = api

        mock_client.post = AsyncMock(
            side_effect=[
                {"assignment": {"user_id": f"user_{i}", "role": "recruiter"}}
                for i in range(3)
            ]
        )

        # Assign multiple users concurrently
        tasks = [api_instance.assign("cand_123", f"user_{i}") for i in range(3)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_unassign_empty_response(self, api):
        """Test unassign with empty response"""
        api_instance, mock_client = api

        mock_client.delete = AsyncMock(return_value=None)

        # Should not raise error
        result = await api_instance.unassign("cand_123", "user_1")

        assert result is None
