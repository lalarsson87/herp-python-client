"""
Tests for HERP Evaluations API Client
"""

from unittest.mock import Mock

import pytest

from src.core.herp.evaluations import EvaluationsAPI


class TestEvaluationsAPI:
    """Test EvaluationsAPI class"""

    @pytest.fixture
    def mock_client(self):
        """Create mock HERP base client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create EvaluationsAPI instance"""
        return EvaluationsAPI(mock_client)

    def test_initialization(self, mock_client):
        """Test API initialization"""
        api = EvaluationsAPI(mock_client)

        assert api.client == mock_client

    def test_get_evaluation(self, api, mock_client):
        """Test getting evaluation details"""
        mock_client.get.return_value = {
            "id": "eval_123",
            "candidacyId": "cand_456",
            "contactId": "contact_789",
            "status": "pending",
            "questions": [
                {
                    "id": "q1",
                    "question": "Technical skills?",
                    "type": "rating",
                }
            ],
        }

        result = api.get("eval_123")

        mock_client.get.assert_called_once_with("/v1/evaluations/eval_123")
        assert result["id"] == "eval_123"
        assert result["status"] == "pending"
        assert len(result["questions"]) == 1

    def test_get_evaluation_not_found(self, api, mock_client):
        """Test getting nonexistent evaluation raises error"""
        mock_client.get.side_effect = Exception("Not found")

        with pytest.raises(Exception, match="Not found"):
            api.get("nonexistent")

    def test_get_evaluation_completed(self, api, mock_client):
        """Test getting completed evaluation with responses"""
        mock_client.get.return_value = {
            "id": "eval_123",
            "status": "completed",
            "responses": {
                "q1": {"rating": 5, "comment": "Excellent technical skills"},
                "q2": {"rating": 4, "comment": "Good communication"},
            },
        }

        result = api.get("eval_123")

        assert result["status"] == "completed"
        assert "responses" in result
        assert result["responses"]["q1"]["rating"] == 5

    def test_submit_evaluation(self, api, mock_client):
        """Test submitting evaluation responses"""
        responses = {
            "q1": {"rating": 5, "comment": "Excellent technical skills"},
            "q2": {"rating": 4, "comment": "Good communication"},
        }

        mock_client.put.return_value = {
            "id": "eval_123",
            "status": "completed",
            "responses": responses,
        }

        result = api.submit("eval_123", responses)

        mock_client.put.assert_called_once_with(
            "/v1/evaluations/eval_123", json={"responses": responses}
        )
        assert result["id"] == "eval_123"
        assert result["status"] == "completed"

    def test_submit_evaluation_uses_put(self, api, mock_client):
        """Test submit uses PUT method (not PATCH)"""
        mock_client.put.return_value = {"id": "eval_123"}

        api.submit("eval_123", {"q1": {"rating": 5}})

        # Should use PUT, not PATCH
        assert mock_client.put.called
        assert not mock_client.patch.called

    def test_submit_evaluation_empty_responses(self, api, mock_client):
        """Test submitting evaluation with empty responses"""
        mock_client.put.return_value = {"id": "eval_123", "responses": {}}

        result = api.submit("eval_123", {})

        # Should allow empty responses (server validation)
        assert result["id"] == "eval_123"

    def test_submit_evaluation_partial_responses(self, api, mock_client):
        """Test submitting partial evaluation responses"""
        responses = {"q1": {"rating": 5}}  # Only one question answered

        mock_client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        assert result["responses"] == responses

    def test_submit_evaluation_complex_responses(self, api, mock_client):
        """Test submitting complex evaluation responses"""
        responses = {
            "q1": {
                "rating": 5,
                "comment": "Excellent",
                "metadata": {"confidence": "high"},
            },
            "q2": {
                "rating": 4,
                "strengths": ["communication", "teamwork"],
                "weaknesses": ["experience"],
            },
        }

        mock_client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        # Should preserve complex nested structure
        assert result["responses"]["q1"]["metadata"]["confidence"] == "high"
        assert "communication" in result["responses"]["q2"]["strengths"]


class TestEvaluationsAPIIntegration:
    """Integration-style tests for EvaluationsAPI"""

    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()

    @pytest.fixture
    def api(self, mock_client):
        """Create API instance"""
        return EvaluationsAPI(mock_client)

    def test_get_and_submit_workflow(self, api, mock_client):
        """Test typical workflow of getting then submitting evaluation"""
        # First, get evaluation
        mock_client.get.return_value = {
            "id": "eval_123",
            "status": "pending",
            "questions": [{"id": "q1", "question": "Skills?"}],
        }
        evaluation = api.get("eval_123")
        assert evaluation["status"] == "pending"

        # Then submit responses
        responses = {"q1": {"rating": 5, "comment": "Great"}}
        mock_client.put.return_value = {
            "id": "eval_123",
            "status": "completed",
            "responses": responses,
        }
        submitted = api.submit("eval_123", responses)
        assert submitted["status"] == "completed"

    def test_multiple_submissions(self, api, mock_client):
        """Test submitting evaluation multiple times (updates)"""
        mock_client.put.return_value = {"id": "eval_123"}

        # First submission
        api.submit("eval_123", {"q1": {"rating": 4}})

        # Second submission (update)
        api.submit("eval_123", {"q1": {"rating": 5, "comment": "Updated"}})

        # Should have made 2 PUT requests
        assert mock_client.put.call_count == 2


class TestEvaluationsAPIEdgeCases:
    """Test edge cases for EvaluationsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        return EvaluationsAPI(Mock())

    def test_get_with_special_characters_in_id(self, api):
        """Test get with special characters in evaluation ID"""
        api.client.get.return_value = {"id": "eval_123-abc_456"}

        # Should handle special characters in URL
        api.get("eval_123-abc_456")

        # Should have made request
        assert api.client.get.called

    def test_submit_with_unicode_comments(self, api):
        """Test submit with unicode characters in comments"""
        responses = {
            "q1": {
                "rating": 5,
                "comment": "優秀な候補者です",  # "Excellent candidate" in Japanese
            }
        }

        api.client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        # Should preserve unicode
        assert "優秀" in result["responses"]["q1"]["comment"]

    def test_submit_with_long_comments(self, api):
        """Test submit with very long comments"""
        long_comment = "A" * 10000  # 10,000 characters
        responses = {"q1": {"rating": 5, "comment": long_comment}}

        api.client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        # Should handle long comments
        assert len(result["responses"]["q1"]["comment"]) == 10000

    def test_submit_with_special_characters_in_responses(self, api):
        """Test submit preserves special characters"""
        responses = {
            "q1": {"comment": 'Comment with "quotes", <tags>, and symbols: @#$%^&*()'}
        }

        api.client.put.return_value = {"id": "eval_123"}

        api.submit("eval_123", responses)

        # Should preserve special characters in request
        call_args = api.client.put.call_args
        assert '"quotes"' in str(call_args[1]["json"]["responses"])

    def test_submit_with_numeric_question_ids(self, api):
        """Test submit with numeric question IDs"""
        responses = {
            "1": {"rating": 5},
            "2": {"rating": 4},
            "3": {"rating": 3},
        }

        api.client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        # Should handle numeric keys
        assert "1" in result["responses"]

    def test_submit_with_null_values(self, api):
        """Test submit with null values in responses"""
        responses = {"q1": {"rating": None, "comment": None}}

        api.client.put.return_value = {"id": "eval_123"}

        api.submit("eval_123", responses)

        # Should allow null values (server validation)
        call_args = api.client.put.call_args
        assert call_args[1]["json"]["responses"]["q1"]["rating"] is None

    def test_get_returns_minimal_data(self, api):
        """Test get with minimal response data"""
        api.client.get.return_value = {"id": "eval_123"}

        result = api.get("eval_123")

        # Should handle minimal response
        assert result["id"] == "eval_123"

    def test_submit_with_nested_arrays(self, api):
        """Test submit with nested arrays in responses"""
        responses = {
            "q1": {
                "selectedOptions": ["option1", "option2", "option3"],
                "rankings": [
                    {"item": "skill1", "rank": 1},
                    {"item": "skill2", "rank": 2},
                ],
            }
        }

        api.client.put.return_value = {"id": "eval_123", "responses": responses}

        result = api.submit("eval_123", responses)

        # Should preserve nested arrays
        assert len(result["responses"]["q1"]["selectedOptions"]) == 3
        assert result["responses"]["q1"]["rankings"][0]["rank"] == 1

    def test_submit_wraps_responses_in_object(self, api):
        """Test submit wraps responses in correct JSON structure"""
        responses = {"q1": {"rating": 5}}

        api.client.put.return_value = {"id": "eval_123"}

        api.submit("eval_123", responses)

        # Should wrap responses in {"responses": {...}}
        call_args = api.client.put.call_args
        assert "responses" in call_args[1]["json"]
        assert call_args[1]["json"]["responses"] == responses
