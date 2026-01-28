"""
Tests for HERP Assignments API Client
"""

from unittest.mock import Mock

import pytest

from src.core.herp.assignments import AssignmentsAPI


class TestAssignmentsAPI:
    """Test AssignmentsAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create AssignmentsAPI instance"""
        return AssignmentsAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = AssignmentsAPI(mock_client)

        assert api.client == mock_client

    def test_list_assignments(self, api, mock_client):
        """Test listing assignments for candidacy"""
        mock_client.get.return_value = {
            "assignments": [
                {
                    "id": "assign_1",
                    "userId": "user_1",
                    "userName": "Alice",
                    "role": "recruiter",
                },
                {
                    "id": "assign_2",
                    "userId": "user_2",
                    "userName": "Bob",
                    "role": "hiring_manager",
                },
            ]
        }

        result = api.list("cand_123")

        mock_client.get.assert_called_once_with("/v1/candidacies/cand_123/assignments")
        assert len(result) == 2
        assert result[0]["userName"] == "Alice"
        assert result[1]["role"] == "hiring_manager"

    def test_list_assignments_data_key_fallback(self, api, mock_client):
        """Test list falls back to 'data' key"""
        mock_client.get.return_value = {"data": [{"id": "assign_1"}]}

        result = api.list("cand_123")

        assert len(result) == 1
        assert result[0]["id"] == "assign_1"

    def test_list_assignments_empty(self, api, mock_client):
        """Test listing assignments when none exist"""
        mock_client.get.return_value = {"assignments": []}

        result = api.list("cand_123")

        assert result == []

    def test_list_assignments_no_data(self, api, mock_client):
        """Test list returns empty list when no data"""
        mock_client.get.return_value = {}

        result = api.list("cand_123")

        assert result == []

    def test_assign_user(self, api, mock_client):
        """Test assigning user to candidacy"""
        mock_client.post.return_value = {
            "id": "assign_new",
            "userId": "user_123",
            "candidacyId": "cand_456",
        }

        result = api.assign("cand_456", "user_123")

        mock_client.post.assert_called_once_with(
            "/v1/candidacies/cand_456/assignments", json={"userId": "user_123"}
        )
        assert result["id"] == "assign_new"
        assert result["userId"] == "user_123"

    def test_assign_user_minimal_response(self, api, mock_client):
        """Test assign with minimal response data"""
        mock_client.post.return_value = {"id": "assign_123"}

        result = api.assign("cand_456", "user_123")

        assert result["id"] == "assign_123"

    def test_assign_multiple_users_sequentially(self, api, mock_client):
        """Test assigning multiple users to same candidacy"""
        mock_client.post.side_effect = [
            {"id": "assign_1", "userId": "user_1"},
            {"id": "assign_2", "userId": "user_2"},
        ]

        result1 = api.assign("cand_123", "user_1")
        result2 = api.assign("cand_123", "user_2")

        # Should create separate assignments
        assert result1["userId"] == "user_1"
        assert result2["userId"] == "user_2"
        assert mock_client.post.call_count == 2

    def test_remove_assignment(self, api, mock_client):
        """Test removing assignment"""
        mock_client.delete.return_value = {}

        result = api.remove("cand_123", "assign_456")

        mock_client.delete.assert_called_once_with(
            "/v1/candidacies/cand_123/assignments/assign_456"
        )
        assert result == {}

    def test_remove_assignment_with_response_data(self, api, mock_client):
        """Test remove with response data"""
        mock_client.delete.return_value = {"success": True, "message": "Removed"}

        result = api.remove("cand_123", "assign_456")

        # Should return whatever the API returns
        assert result["success"] is True

    def test_remove_nonexistent_assignment(self, api, mock_client):
        """Test removing nonexistent assignment raises error"""
        mock_client.delete.side_effect = Exception("Not found")

        with pytest.raises(Exception, match="Not found"):
            api.remove("cand_123", "nonexistent")


class TestAssignmentsAPIIntegration:
    """Integration-style tests for AssignmentsAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return AssignmentsAPI(mock_client)

    def test_list_assign_remove_workflow(self, api, mock_client):
        """Test typical workflow: list, assign, list, remove"""
        # First, list existing assignments
        mock_client.get.return_value = {"assignments": []}
        assignments = api.list("cand_123")
        assert len(assignments) == 0

        # Assign a user
        mock_client.post.return_value = {"id": "assign_1", "userId": "user_1"}
        new_assignment = api.assign("cand_123", "user_1")
        assert new_assignment["id"] == "assign_1"

        # List again (should have 1 assignment)
        mock_client.get.return_value = {"assignments": [new_assignment]}
        assignments = api.list("cand_123")
        assert len(assignments) == 1

        # Remove assignment
        mock_client.delete.return_value = {}
        api.remove("cand_123", "assign_1")

        # List again (should be empty)
        mock_client.get.return_value = {"assignments": []}
        assignments = api.list("cand_123")
        assert len(assignments) == 0

    def test_assign_multiple_users_workflow(self, api, mock_client):
        """Test assigning multiple users to build a team"""
        # Assign recruiter
        mock_client.post.return_value = {
            "id": "assign_1",
            "userId": "user_1",
            "role": "recruiter",
        }
        api.assign("cand_123", "user_1")

        # Assign hiring manager
        mock_client.post.return_value = {
            "id": "assign_2",
            "userId": "user_2",
            "role": "hiring_manager",
        }
        api.assign("cand_123", "user_2")

        # List all assignments
        mock_client.get.return_value = {
            "assignments": [
                {"id": "assign_1", "userId": "user_1", "role": "recruiter"},
                {"id": "assign_2", "userId": "user_2", "role": "hiring_manager"},
            ]
        }
        assignments = api.list("cand_123")

        # Should have both team members
        assert len(assignments) == 2
        roles = [a["role"] for a in assignments]
        assert "recruiter" in roles
        assert "hiring_manager" in roles

    def test_reassign_user_workflow(self, api, mock_client):
        """Test reassigning a candidacy to different user"""
        # Remove old assignment
        mock_client.delete.return_value = {}
        api.remove("cand_123", "old_assign")

        # Assign new user
        mock_client.post.return_value = {"id": "new_assign", "userId": "new_user"}
        new_assignment = api.assign("cand_123", "new_user")

        assert new_assignment["userId"] == "new_user"


class TestAssignmentsAPIEdgeCases:
    """Test edge cases for AssignmentsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return AssignmentsAPI(Mock())

    def test_list_with_special_characters_in_id(self, api):
        """Test list with special characters in candidacy ID"""
        api.client.get.return_value = {"assignments": []}

        # Should handle special characters in URL
        api.list("cand_123-abc_456")

        # Should have made request
        assert api.client.get.called

    def test_assign_with_special_user_id(self, api):
        """Test assign with special characters in user ID"""
        api.client.post.return_value = {"id": "assign_1"}

        api.assign("cand_123", "user_abc-123_def")

        # Should preserve user ID
        call_args = api.client.post.call_args
        assert call_args[1]["json"]["userId"] == "user_abc-123_def"

    def test_remove_with_special_assignment_id(self, api):
        """Test remove with special characters in assignment ID"""
        api.client.delete.return_value = {}

        api.remove("cand_123", "assign_abc-123_def")

        # Should include assignment ID in URL
        call_args = api.client.delete.call_args
        assert "assign_abc-123_def" in call_args[0][0]

    def test_list_large_number_of_assignments(self, api):
        """Test list with many assignments"""
        large_dataset = [
            {"id": f"assign_{i}", "userId": f"user_{i}"} for i in range(100)
        ]
        api.client.get.return_value = {"assignments": large_dataset}

        result = api.list("cand_123")

        # Should handle large number of assignments
        assert len(result) == 100

    def test_assign_same_user_twice(self, api):
        """Test assigning same user twice (should work, server validates)"""
        api.client.post.side_effect = [
            {"id": "assign_1", "userId": "user_123"},
            {"id": "assign_2", "userId": "user_123"},  # Same user
        ]

        # Client allows this (server will validate/prevent duplicates)
        result1 = api.assign("cand_123", "user_123")
        result2 = api.assign("cand_123", "user_123")

        assert result1["userId"] == "user_123"
        assert result2["userId"] == "user_123"

    def test_remove_already_removed_assignment(self, api):
        """Test removing already removed assignment"""
        api.client.delete.side_effect = Exception("Assignment not found")

        # Should propagate error from server
        with pytest.raises(Exception, match="Assignment not found"):
            api.remove("cand_123", "assign_123")

    def test_list_returns_assignments_with_full_data(self, api):
        """Test list returns complete assignment data"""
        api.client.get.return_value = {
            "assignments": [
                {
                    "id": "assign_1",
                    "userId": "user_1",
                    "userName": "Alice Smith",
                    "userEmail": "alice@company.com",
                    "role": "recruiter",
                    "assignedAt": "2026-01-28T10:00:00Z",
                }
            ]
        }

        result = api.list("cand_123")

        # Should preserve all fields
        assert result[0]["userName"] == "Alice Smith"
        assert result[0]["userEmail"] == "alice@company.com"
        assert result[0]["assignedAt"] == "2026-01-28T10:00:00Z"

    def test_assign_wraps_user_id_correctly(self, api):
        """Test assign wraps userId in correct JSON structure"""
        api.client.post.return_value = {"id": "assign_1"}

        api.assign("cand_123", "user_456")

        # Should wrap userId in {"userId": "..."}
        call_args = api.client.post.call_args
        assert "userId" in call_args[1]["json"]
        assert call_args[1]["json"]["userId"] == "user_456"

    def test_list_with_empty_user_names(self, api):
        """Test list with assignments that have empty user names"""
        api.client.get.return_value = {
            "assignments": [
                {"id": "assign_1", "userId": "user_1", "userName": ""},
                {"id": "assign_2", "userId": "user_2", "userName": None},
            ]
        }

        result = api.list("cand_123")

        # Should handle empty/null user names
        assert result[0]["userName"] == ""
        assert result[1]["userName"] is None
