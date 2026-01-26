#!/usr/bin/env python3
"""
HERP Async Evaluations API Client

Async version of evaluation operations.
"""

from typing import Any, Dict

from ..utils.logging import get_logger
from ..utils.validators import validate_single_response
from .async_base_client import AsyncHerpBaseClient
from .schemas import HerpEvaluationResponse

logger = get_logger(__name__)


class AsyncEvaluationsAPI:
    """
    Async Evaluations API Client

    Provides async methods for evaluation operations.
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async evaluations API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    @validate_single_response(HerpEvaluationResponse, strict=False)
    async def get(self, evaluation_id: str) -> Dict[str, Any]:
        """
        Get evaluation details

        Args:
            evaluation_id: Evaluation ID

        Returns:
            Evaluation record
        """
        data = await self.client.get(f"/v1/evaluations/{evaluation_id}")
        return data.get("evaluation", data.get("data", data))

    @validate_single_response(HerpEvaluationResponse, strict=False)
    async def submit(
        self, evaluation_id: str, responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit evaluation responses

        Args:
            evaluation_id: Evaluation ID
            responses: Evaluation responses (answers to questions)

        Returns:
            Updated evaluation record

        Usage:
            evaluation = await api.submit("eval_123", {
                "responses": [
                    {"question_id": "q1", "answer": "Excellent communication"},
                    {"question_id": "q2", "score": 5, "max_score": 5}
                ],
                "recommendation": "strong_yes"
            })
        """
        data = await self.client.put(f"/v1/evaluations/{evaluation_id}", json=responses)
        return data.get("evaluation", data.get("data", data))
