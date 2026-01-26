#!/usr/bin/env python3
"""
HERP API Client

Unified facade client for interacting with the HERP Hire API.
Provides a high-level interface that composes specialized API clients.

This client maintains backward compatibility while delegating to focused modules:
- candidates: Candidacy operations
- contacts: Interview/contact operations
- files: File operations
- evaluations: Evaluation operations
- assignments: Team assignment operations
- timeline: Timeline comment operations
- master_data: Requisitions and users
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..cache import CacheManager
from ..observability.metrics import MetricsCollector
from ..utils.circuit_breaker import CircuitBreakerConfig
from ..utils.config import HerpConfig
from ..utils.logging import get_logger
from .assignments import AssignmentsAPI
from .base_client import HerpBaseClient
from .candidates import CandidaciesAPI
from .contacts import ContactsAPI
from .evaluations import EvaluationsAPI
from .files import FilesAPI
from .master_data import MasterDataAPI
from .query_dsl import Query
from .timeline import TimelineAPI

logger = get_logger(__name__)


class HerpClient:
    """
    HERP API Client (Facade)

    Provides a high-level interface for interacting with the HERP Hire API
    with built-in rate limiting, retries, and error handling.

    This is a facade that composes specialized API clients for different domains.
    Access specialized clients via properties:
    - client.candidacies: Candidacy operations
    - client.contacts: Interview/contact operations
    - client.files: File operations
    - client.evaluations: Evaluation operations
    - client.assignments: Team assignment operations
    - client.timeline: Timeline comment operations
    - client.master_data: Requisitions and users

    Legacy methods are still available for backward compatibility.
    """

    def __init__(
        self,
        config: HerpConfig,
        cache_manager: Optional[CacheManager] = None,
        enable_circuit_breaker: bool = False,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize HERP client

        Args:
            config: HERP configuration object
            cache_manager: Optional cache manager for response caching
            enable_circuit_breaker: Enable circuit breaker pattern (default: False)
            circuit_breaker_config: Circuit breaker configuration (uses defaults if not provided)
            metrics_collector: Optional metrics collector (uses global if not provided)
        """
        # Create base client
        self._base_client = HerpBaseClient(
            config=config,
            cache_manager=cache_manager,
            enable_circuit_breaker=enable_circuit_breaker,
            circuit_breaker_config=circuit_breaker_config,
            metrics_collector=metrics_collector,
        )

        # Initialize specialized API clients
        self.candidacies = CandidaciesAPI(self._base_client)
        self.contacts = ContactsAPI(self._base_client)
        self.files = FilesAPI(self._base_client)
        self.evaluations = EvaluationsAPI(self._base_client)
        self.assignments = AssignmentsAPI(self._base_client)
        self.timeline = TimelineAPI(self._base_client)
        self.master_data = MasterDataAPI(self._base_client)

        # Expose common attributes for backward compatibility
        self.config = config
        self.base_url = config.base_url
        self.cache_manager = cache_manager
        self.rate_limiter = self._base_client.rate_limiter
        self.metrics = self._base_client.metrics
        self.circuit_breaker = self._base_client.circuit_breaker
        self.session = self._base_client.session

        logger.debug("HerpClient initialized with modular architecture")

    # ========================================================================
    # HTTP Methods (delegated to base client)
    # ========================================================================

    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request (delegates to base client)"""
        return self._base_client.get(endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request (delegates to base client)"""
        return self._base_client.post(endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PATCH request (delegates to base client)"""
        return self._base_client.patch(endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT request (delegates to base client)"""
        return self._base_client.put(endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request (delegates to base client)"""
        return self._base_client.delete(endpoint, **kwargs)

    # ========================================================================
    # Candidacies (delegated for backward compatibility)
    # ========================================================================

    def list_candidacies(
        self, updated_since: Optional[str] = None, page: int = 1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List candidacies (delegates to candidacies.list)"""
        return self.candidacies.list(updated_since, page, limit)

    def iter_candidacies(
        self,
        updated_since: Optional[str] = None,
        limit: int = 100,
        max_pages: Optional[int] = None,
    ):
        """Iterate candidacies (delegates to candidacies.iter)"""
        return self.candidacies.iter(updated_since, limit, max_pages)

    def list_all_candidacies(
        self,
        updated_since: Optional[str] = None,
        limit: int = 100,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all candidacies (delegates to candidacies.fetch_all)"""
        return self.candidacies.fetch_all(updated_since, limit, max_pages)

    def search_candidacies(
        self,
        query: Optional[Query] = None,
        limit: Optional[int] = None,
        **filters,
    ) -> List[Dict[str, Any]]:
        """Search candidacies (delegates to candidacies.search)"""
        return self.candidacies.search(query, limit, **filters)

    def get_candidacy(self, candidacy_id: str) -> Dict[str, Any]:
        """Get candidacy details (delegates to candidacies.get)"""
        return self.candidacies.get(candidacy_id)

    def create_candidacy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create candidacy (delegates to candidacies.create)"""
        return self.candidacies.create(data)

    def update_candidacy_step(self, candidacy_id: str, step: str) -> Dict[str, Any]:
        """Update candidacy step (delegates to candidacies.update_step)"""
        return self.candidacies.update_step(candidacy_id, step)

    def terminate_candidacy(
        self, candidacy_id: str, termination_reason: str
    ) -> Dict[str, Any]:
        """Terminate candidacy (delegates to candidacies.terminate)"""
        return self.candidacies.terminate(candidacy_id, termination_reason)

    # ========================================================================
    # Contacts (delegated for backward compatibility)
    # ========================================================================

    def list_contacts(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """List contacts (delegates to contacts.list)"""
        return self.contacts.list(candidacy_id)

    def list_contacts_for_multiple(
        self, candidacy_ids: List[str], max_workers: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Batch fetch contacts (delegates to contacts.list_for_multiple)"""
        return self.contacts.list_for_multiple(candidacy_ids, max_workers)

    def create_contact(
        self, candidacy_id: str, contact_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create contact (delegates to contacts.create)"""
        return self.contacts.create(candidacy_id, contact_data)

    # ========================================================================
    # Timeline (delegated for backward compatibility)
    # ========================================================================

    def list_timeline_comments(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """List timeline comments (delegates to timeline.list)"""
        return self.timeline.list(candidacy_id)

    def add_timeline_comment(
        self, candidacy_id: str, comment: str, content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """Add timeline comment (delegates to timeline.add_comment)"""
        return self.timeline.add_comment(candidacy_id, comment, content_type)

    # ========================================================================
    # Files (delegated for backward compatibility)
    # ========================================================================

    def list_files(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """List files (delegates to files.list)"""
        return self.files.list(candidacy_id)

    def list_files_for_multiple(
        self, candidacy_ids: List[str], max_workers: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Batch fetch files (delegates to files.list_for_multiple)"""
        return self.files.list_for_multiple(candidacy_ids, max_workers)

    def download_file(self, candidacy_id: str, file_id: str) -> bytes:
        """Download file (delegates to files.download)"""
        return self.files.download(candidacy_id, file_id)

    def upload_file(
        self, candidacy_id: str, file_path: Path, file_type: str = "other"
    ) -> Dict[str, Any]:
        """Upload file (delegates to files.upload)"""
        return self.files.upload(candidacy_id, file_path, file_type)

    # ========================================================================
    # Evaluations (delegated for backward compatibility)
    # ========================================================================

    def get_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """Get evaluation (delegates to evaluations.get)"""
        return self.evaluations.get(evaluation_id)

    def submit_evaluation(
        self, evaluation_id: str, responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit evaluation (delegates to evaluations.submit)"""
        return self.evaluations.submit(evaluation_id, responses)

    # ========================================================================
    # Assignments (delegated for backward compatibility)
    # ========================================================================

    def list_assignments(self, candidacy_id: str) -> List[Dict[str, Any]]:
        """List assignments (delegates to assignments.list)"""
        return self.assignments.list(candidacy_id)

    def assign_team_member(self, candidacy_id: str, user_id: str) -> Dict[str, Any]:
        """Assign team member (delegates to assignments.assign)"""
        return self.assignments.assign(candidacy_id, user_id)

    def remove_team_member(
        self, candidacy_id: str, assignment_id: str
    ) -> Dict[str, Any]:
        """Remove team member (delegates to assignments.remove)"""
        return self.assignments.remove(candidacy_id, assignment_id)

    # ========================================================================
    # Master Data (delegated for backward compatibility)
    # ========================================================================

    def list_requisitions(self) -> List[Dict[str, Any]]:
        """List requisitions (delegates to master_data.list_requisitions)"""
        return self.master_data.list_requisitions()

    def list_users(self) -> List[Dict[str, Any]]:
        """List users (delegates to master_data.list_users)"""
        return self.master_data.list_users()
