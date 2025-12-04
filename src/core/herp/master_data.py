#!/usr/bin/env python3
"""
HERP Master Data API Client

Handles master data operations including requisitions (job postings)
and users (team members).
"""

from typing import Dict, Any, List

from ..utils.validators import validate_list_response
from ..utils.logging import get_logger
from .base_client import HerpBaseClient
from .schemas import (
    HerpRequisitionsListResponse,
    HerpUsersListResponse,
)
from .mixins import CacheMixin


logger = get_logger(__name__)


class MasterDataAPI(CacheMixin):
    """
    Master Data API Client

    Provides methods for accessing master data (requisitions, users).
    """

    def __init__(self, client: HerpBaseClient):
        """
        Initialize master data API client

        Args:
            client: Base HERP client for HTTP requests
        """
        self.client = client

    @validate_list_response(HerpRequisitionsListResponse, strict=False)
    def list_requisitions(self, use_cache: bool = True, ttl: int = 300) -> List[Dict[str, Any]]:
        """
        List job requisitions (open positions)

        Args:
            use_cache: Whether to use caching (default: True)
            ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)

        Returns:
            List of requisition records

        Note:
            Requisitions are cached by default for 5 minutes since they
            don't change frequently. Set use_cache=False to force fresh fetch.
        """
        if not use_cache:
            data = self.client.get("/v1/requisitions")
            return data.get("requisitions", data.get("data", []))

        return self._cached_fetch(
            cache_key="herp:master_data:requisitions",
            fetch_function=lambda: self.list_requisitions(use_cache=False),
            ttl=ttl
        )

    @validate_list_response(HerpUsersListResponse, strict=False)
    def list_users(self, use_cache: bool = True, ttl: int = 600) -> List[Dict[str, Any]]:
        """
        List team members and recruiters

        Args:
            use_cache: Whether to use caching (default: True)
            ttl: Cache time-to-live in seconds (default: 600 = 10 minutes)

        Returns:
            List of user records

        Note:
            Users are cached by default for 10 minutes since they
            don't change frequently. Set use_cache=False to force fresh fetch.
        """
        if not use_cache:
            data = self.client.get("/v1/users")
            return data.get("users", data.get("data", []))

        return self._cached_fetch(
            cache_key="herp:master_data:users",
            fetch_function=lambda: self.list_users(use_cache=False),
            ttl=ttl
        )
