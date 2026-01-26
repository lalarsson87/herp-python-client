#!/usr/bin/env python3
"""
HERP Async Client (Main)

Main async client that composes all specialized async API clients.
"""

from typing import Optional

from ..cache.manager import CacheManager
from ..circuit_breaker import CircuitBreakerConfig
from ..metrics.collector import MetricsCollector, get_metrics_collector
from ..utils.config import HerpConfig
from ..utils.logging import get_logger
from .async_assignments import AsyncAssignmentsAPI
from .async_base_client import AsyncHerpBaseClient
from .async_candidates import AsyncCandidaciesAPI
from .async_contacts import AsyncContactsAPI
from .async_evaluations import AsyncEvaluationsAPI
from .async_files import AsyncFilesAPI
from .async_master_data import AsyncMasterDataAPI
from .async_timeline import AsyncTimelineAPI

logger = get_logger(__name__)


class AsyncHerpClient:
    """
    Async HERP API Client (Main)

    Composes all specialized async API clients into a single interface.

    Provides two usage patterns:

    1. **Modular API** (Recommended):
        async with AsyncHerpClient(config) as client:
            candidacies = await client.candidacies.list()
            contacts = await client.contacts.list("candidacy_123")

    2. **Async Context Manager**:
        async with AsyncHerpClient(config) as client:
            # All async operations here
            candidacies = await client.candidacies.list()

    Attributes:
        candidacies: AsyncCandidaciesAPI - Candidacy operations
        contacts: AsyncContactsAPI - Interview/contact operations
        files: AsyncFilesAPI - File operations
        evaluations: AsyncEvaluationsAPI - Evaluation operations
        assignments: AsyncAssignmentsAPI - Team assignment operations
        timeline: AsyncTimelineAPI - Timeline comment operations
        master_data: AsyncMasterDataAPI - Requisitions and users
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
        Initialize async HERP client

        Args:
            config: HERP configuration
            cache_manager: Optional cache manager for response caching
            enable_circuit_breaker: Whether to enable circuit breaker
            circuit_breaker_config: Circuit breaker configuration
            metrics_collector: Optional metrics collector
        """
        self.config = config
        self._cache_manager = cache_manager
        self._enable_circuit_breaker = enable_circuit_breaker
        self._circuit_breaker_config = circuit_breaker_config
        self._metrics = metrics_collector or get_metrics_collector()

        # Base client will be created in __aenter__
        self._base_client: Optional[AsyncHerpBaseClient] = None

        # Specialized clients (will be initialized in __aenter__)
        self.candidacies: Optional[AsyncCandidaciesAPI] = None
        self.contacts: Optional[AsyncContactsAPI] = None
        self.files: Optional[AsyncFilesAPI] = None
        self.evaluations: Optional[AsyncEvaluationsAPI] = None
        self.assignments: Optional[AsyncAssignmentsAPI] = None
        self.timeline: Optional[AsyncTimelineAPI] = None
        self.master_data: Optional[AsyncMasterDataAPI] = None

    async def __aenter__(self):
        """Async context manager entry"""
        # Create base client
        self._base_client = AsyncHerpBaseClient(
            config=self.config,
            cache_manager=self._cache_manager,
            enable_circuit_breaker=self._enable_circuit_breaker,
            circuit_breaker_config=self._circuit_breaker_config,
            metrics_collector=self._metrics,
        )
        await self._base_client.__aenter__()

        # Initialize specialized API clients
        self.candidacies = AsyncCandidaciesAPI(self._base_client)
        self.contacts = AsyncContactsAPI(self._base_client)
        self.files = AsyncFilesAPI(self._base_client)
        self.evaluations = AsyncEvaluationsAPI(self._base_client)
        self.assignments = AsyncAssignmentsAPI(self._base_client)
        self.timeline = AsyncTimelineAPI(self._base_client)
        self.master_data = AsyncMasterDataAPI(self._base_client)

        logger.info("Async HERP client initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._base_client:
            await self._base_client.__aexit__(exc_type, exc_val, exc_tb)
            self._base_client = None

        # Clear specialized clients
        self.candidacies = None
        self.contacts = None
        self.files = None
        self.evaluations = None
        self.assignments = None
        self.timeline = None
        self.master_data = None

        logger.info("Async HERP client closed")

    @property
    def rate_limiter(self):
        """Get rate limiter from base client"""
        return self._base_client.rate_limiter if self._base_client else None

    @property
    def metrics(self):
        """Get metrics collector"""
        return self._metrics

    @property
    def cache_manager(self):
        """Get cache manager"""
        return self._cache_manager
