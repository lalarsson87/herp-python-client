#!/usr/bin/env python3
"""
HERP Async Master Data API Client

Async version of master data operations with caching.
"""

from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger
from ..utils.validators import validate_list_response
from .async_base_client import AsyncHerpBaseClient
from .schemas import (
    HerpRequisitionsListResponse,
    HerpUsersListResponse,
)

logger = get_logger(__name__)


class AsyncMasterDataAPI:
    """
    Async Master Data API Client with caching

    Provides async methods for accessing master data (requisitions, users).
    Supports caching to reduce API calls.
    """

    def __init__(self, client: AsyncHerpBaseClient):
        """
        Initialize async master data API client

        Args:
            client: Async base HERP client for HTTP requests
        """
        self.client = client

    async def _cached_fetch(
        self, cache_key: str, fetch_function, ttl: int = 300
    ) -> Any:
        """
        Fetch with caching (async version)

        Args:
            cache_key: Unique cache key
            fetch_function: Async function to call on cache miss
            ttl: Time-to-live in seconds

        Returns:
            Cached or freshly fetched data
        """
        # Check if cache manager available
        if (
            not hasattr(self.client, "cache_manager")
            or self.client.cache_manager is None
        ):
            return await fetch_function()

        cache_manager = self.client.cache_manager

        # Check cache
        cached = cache_manager.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        # Cache miss - fetch and store
        logger.debug(f"Cache miss for {cache_key}, fetching...")
        data = await fetch_function()
        cache_manager.set(cache_key, data, ttl=ttl)
        return data

    def _invalidate_cache(self, cache_key: str) -> None:
        """
        Invalidate cache entry

        Args:
            cache_key: Cache key to invalidate
        """
        if hasattr(self.client, "cache_manager") and self.client.cache_manager:
            self.client.cache_manager.delete(cache_key)

    @validate_list_response(HerpRequisitionsListResponse, strict=False)
    async def list_requisitions(
        self, use_cache: bool = True, ttl: int = 300
    ) -> List[Dict[str, Any]]:
        """
        List job requisitions (cached for 5 minutes by default)

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
            data = await self.client.get("/v1/requisitions")
            return data.get("requisitions", data.get("data", []))

        async def fetch():
            return await self.list_requisitions(use_cache=False)

        return await self._cached_fetch(
            cache_key="herp:master_data:requisitions", fetch_function=fetch, ttl=ttl
        )

    @validate_list_response(HerpUsersListResponse, strict=False)
    async def list_users(
        self, use_cache: bool = True, ttl: int = 600
    ) -> List[Dict[str, Any]]:
        """
        List team members (cached for 10 minutes by default)

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
            data = await self.client.get("/v1/users")
            return data.get("users", data.get("data", []))

        async def fetch():
            return await self.list_users(use_cache=False)

        return await self._cached_fetch(
            cache_key="herp:master_data:users", fetch_function=fetch, ttl=ttl
        )
