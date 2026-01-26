#!/usr/bin/env python3
"""
HERP Evaluations API Client

Handles candidate evaluation operations for interview feedback.
"""

from typing import Any, Dict

from ..utils.logging import get_logger
from ..utils.validators import validate_response
from .base_client import HerpBaseClient
from .schemas import HerpEvaluationResponse

logger = get_logger(__name__)


class EvaluationsAPI:
    """
    Evaluations API Client

    Provides methods for managing candidate evaluations and interview feedback.
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize evaluations API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_response(HerpEvaluationResponse, strict=False)
    def get(self, evaluation_id: str) -> Dict[str, Any]:
        """
        Get evaluation details

        Args:
            evaluation_id: Evaluation ID

        Returns:
            Evaluation record
        """
        return self.client.get(f"/v1/evaluations/{evaluation_id}")

    def submit(self, evaluation_id: str, responses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit evaluation responses

        Args:
            evaluation_id: Evaluation ID
            responses: Evaluation responses

        Returns:
            Updated evaluation record

        Note:
            Uses PUT as per HERP API documentation (not PATCH)
        """
        return self.client.put(
            f"/v1/evaluations/{evaluation_id}", json={"responses": responses}
        )
