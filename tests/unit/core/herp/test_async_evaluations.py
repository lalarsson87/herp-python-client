"""
Tests for HERP Async Evaluations API Client
"""

from unittest.mock import AsyncMock

import pytest

from src.core.herp.async_evaluations import AsyncEvaluationsAPI


class TestAsyncEvaluationsAPIInitialization:
    """Test AsyncEvaluationsAPI initialization"""

    def test_initialization(self):
        """Test API initialization"""
        mock_client = AsyncMock()

        api = AsyncEvaluationsAPI(mock_client)

        assert api.client == mock_client


class TestAsyncEvaluationsAPIGet:
    """Test get method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncEvaluationsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_get_evaluation(self, api):
        """Test getting evaluation by ID"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "candidacy_id": "cand_456",
                    "contact_id": "contact_789",
                    "evaluator_id": "user_101",
                    "status": "pending",
                    "questions": [
                        {
                            "id": "q1",
                            "text": "How was communication?",
                            "type": "text",
                        },
                        {"id": "q2", "text": "Overall score", "type": "score"},
                    ],
                }
            }
        )

        result = await api_instance.get("eval_123")

        mock_client.get.assert_called_once_with("/v1/evaluations/eval_123")
        assert result["id"] == "eval_123"
        assert result["status"] == "pending"
        assert len(result["questions"]) == 2

    @pytest.mark.asyncio
    async def test_get_evaluation_data_key_fallback(self, api):
        """Test get falls back to 'data' key"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={
                "data": {
                    "id": "eval_123",
                    "candidacy_id": "cand_456",
                    "status": "pending",
                }
            }
        )

        result = await api_instance.get("eval_123")

        assert result["id"] == "eval_123"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_constructs_correct_url(self, api):
        """Test get constructs correct URL"""
        api_instance, mock_client = api

        mock_client.get = AsyncMock(
            return_value={"evaluation": {"id": "eval_xyz", "status": "pending"}}
        )

        await api_instance.get("eval_xyz")

        mock_client.get.assert_called_once_with("/v1/evaluations/eval_xyz")


class TestAsyncEvaluationsAPISubmit:
    """Test submit method"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncEvaluationsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_submit_evaluation(self, api):
        """Test submitting evaluation responses"""
        api_instance, mock_client = api

        responses = {
            "responses": [
                {"question_id": "q1", "answer": "Excellent communication skills"},
                {"question_id": "q2", "score": 5, "max_score": 5},
            ],
            "recommendation": "strong_yes",
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "responses": responses["responses"],
                    "recommendation": "strong_yes",
                }
            }
        )

        result = await api_instance.submit("eval_123", responses)

        mock_client.put.assert_called_once_with(
            "/v1/evaluations/eval_123", json=responses
        )
        assert result["id"] == "eval_123"
        assert result["status"] == "submitted"
        assert result["recommendation"] == "strong_yes"

    @pytest.mark.asyncio
    async def test_submit_with_text_responses(self, api):
        """Test submitting evaluation with text responses"""
        api_instance, mock_client = api

        responses = {
            "responses": [
                {
                    "question_id": "q1",
                    "answer": "Strong technical skills. Good problem solving.",
                },
                {"question_id": "q2", "answer": "Great cultural fit for the team."},
            ]
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "responses": responses["responses"],
                }
            }
        )

        result = await api_instance.submit("eval_123", responses)

        # Verify responses were passed correctly
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs["json"]["responses"] == responses["responses"]

    @pytest.mark.asyncio
    async def test_submit_with_score_responses(self, api):
        """Test submitting evaluation with score responses"""
        api_instance, mock_client = api

        responses = {
            "responses": [
                {"question_id": "q1", "score": 4, "max_score": 5},
                {"question_id": "q2", "score": 5, "max_score": 5},
                {"question_id": "q3", "score": 3, "max_score": 5},
            ],
            "overall_score": 4,
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "overall_score": 4,
                }
            }
        )

        result = await api_instance.submit("eval_123", responses)

        assert result["overall_score"] == 4

    @pytest.mark.asyncio
    async def test_submit_with_recommendation(self, api):
        """Test submitting evaluation with hiring recommendation"""
        api_instance, mock_client = api

        responses = {
            "responses": [{"question_id": "q1", "answer": "Excellent candidate"}],
            "recommendation": "strong_yes",
            "comments": "Should definitely move forward",
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "recommendation": "strong_yes",
                }
            }
        )

        result = await api_instance.submit("eval_123", responses)

        # Verify recommendation was included
        call_kwargs = mock_client.put.call_args[1]
        assert call_kwargs["json"]["recommendation"] == "strong_yes"

    @pytest.mark.asyncio
    async def test_submit_data_key_fallback(self, api):
        """Test submit falls back to 'data' key"""
        api_instance, mock_client = api

        responses = {"responses": [{"question_id": "q1", "answer": "Good"}]}

        mock_client.put = AsyncMock(
            return_value={"data": {"id": "eval_123", "status": "submitted"}}
        )

        result = await api_instance.submit("eval_123", responses)

        assert result["id"] == "eval_123"

    @pytest.mark.asyncio
    async def test_submit_constructs_correct_url(self, api):
        """Test submit constructs correct URL"""
        api_instance, mock_client = api

        mock_client.put = AsyncMock(
            return_value={"evaluation": {"id": "eval_xyz", "status": "submitted"}}
        )

        await api_instance.submit("eval_xyz", {"responses": []})

        mock_client.put.assert_called_once_with(
            "/v1/evaluations/eval_xyz", json={"responses": []}
        )


class TestAsyncEvaluationsAPIIntegration:
    """Integration-style tests for AsyncEvaluationsAPI"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncEvaluationsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_get_and_submit_workflow(self, api):
        """Test typical workflow: get evaluation, then submit"""
        api_instance, mock_client = api

        # First, get evaluation
        mock_client.get = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "pending",
                    "questions": [
                        {"id": "q1", "text": "Communication?", "type": "text"}
                    ],
                }
            }
        )
        evaluation = await api_instance.get("eval_123")
        assert evaluation["status"] == "pending"

        # Submit responses
        responses = {
            "responses": [{"question_id": "q1", "answer": "Excellent"}],
            "recommendation": "strong_yes",
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "recommendation": "strong_yes",
                }
            }
        )
        submitted = await api_instance.submit("eval_123", responses)
        assert submitted["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_submit_multiple_evaluations_sequentially(self, api):
        """Test submitting multiple evaluations in sequence"""
        api_instance, mock_client = api

        evaluations = [
            ("eval_1", "strong_yes"),
            ("eval_2", "yes"),
            ("eval_3", "no"),
        ]

        for eval_id, recommendation in evaluations:
            mock_client.put = AsyncMock(
                return_value={
                    "evaluation": {
                        "id": eval_id,
                        "status": "submitted",
                        "recommendation": recommendation,
                    }
                }
            )

            result = await api_instance.submit(
                eval_id,
                {
                    "responses": [{"question_id": "q1", "answer": "Test"}],
                    "recommendation": recommendation,
                },
            )

            assert result["recommendation"] == recommendation


class TestAsyncEvaluationsAPIEdgeCases:
    """Test edge cases for async evaluations API"""

    @pytest.fixture
    def api(self):
        """Create API instance"""
        mock_client = AsyncMock()
        return AsyncEvaluationsAPI(mock_client), mock_client

    @pytest.mark.asyncio
    async def test_get_returns_direct_response(self, api):
        """Test get when response doesn't have wrapper key"""
        api_instance, mock_client = api

        # Response without wrapper key
        mock_client.get = AsyncMock(
            return_value={
                "id": "eval_123",
                "candidacy_id": "cand_456",
                "status": "pending",
            }
        )

        result = await api_instance.get("eval_123")

        assert result["id"] == "eval_123"

    @pytest.mark.asyncio
    async def test_submit_returns_direct_response(self, api):
        """Test submit when response doesn't have wrapper key"""
        api_instance, mock_client = api

        # Response without wrapper key
        mock_client.put = AsyncMock(
            return_value={"id": "eval_123", "status": "submitted"}
        )

        result = await api_instance.submit("eval_123", {"responses": []})

        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_submit_empty_responses(self, api):
        """Test submitting evaluation with empty responses"""
        api_instance, mock_client = api

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {"id": "eval_123", "status": "submitted", "responses": []}
            }
        )

        result = await api_instance.submit("eval_123", {"responses": []})

        # Should still work, API will handle validation
        assert result["id"] == "eval_123"

    @pytest.mark.asyncio
    async def test_concurrent_submissions(self, api):
        """Test concurrent evaluation submissions"""
        import asyncio

        api_instance, mock_client = api

        mock_client.put = AsyncMock(
            side_effect=[
                {"evaluation": {"id": f"eval_{i}", "status": "submitted"}}
                for i in range(3)
            ]
        )

        # Submit multiple evaluations concurrently
        tasks = [api_instance.submit(f"eval_{i}", {"responses": []}) for i in range(3)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert mock_client.put.call_count == 3

    @pytest.mark.asyncio
    async def test_submit_with_unicode_answers(self, api):
        """Test submitting evaluation with unicode answers"""
        api_instance, mock_client = api

        responses = {
            "responses": [
                {
                    "question_id": "q1",
                    "answer": "優秀な候補者です - Excellent candidate 🌟",
                }
            ]
        }

        mock_client.put = AsyncMock(
            return_value={
                "evaluation": {
                    "id": "eval_123",
                    "status": "submitted",
                    "responses": responses["responses"],
                }
            }
        )

        result = await api_instance.submit("eval_123", responses)

        assert result["id"] == "eval_123"
