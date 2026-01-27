#!/usr/bin/env python3
"""
HERP Webhook Router

Provides webhook event routing with filtering, retries, and error handling.

Features:
- Event filtering by type, candidacy ID, etc.
- Retry logic with exponential backoff
- Dead letter queue for failed events
- Event replay for failed events
"""

import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ...utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WebhookRoute:
    """
    Webhook route configuration

    Defines how to route and process webhook events.
    """

    # Event type pattern (exact match or "*" for all)
    event_type: str

    # Handler function
    handler: Callable

    # Filter function (optional)
    filter: Optional[Callable[[Dict[str, Any]], bool]] = None

    # Max retries
    max_retries: int = 3

    # Retry delay in seconds
    retry_delay: float = 1.0

    # Exponential backoff multiplier
    backoff_multiplier: float = 2.0

    # Max retry delay in seconds
    max_retry_delay: float = 60.0


@dataclass
class FailedEvent:
    """
    Failed webhook event for dead letter queue
    """

    payload: Dict[str, Any]
    error: str
    failed_at: datetime = field(default_factory=datetime.now)
    retries: int = 0
    route: Optional[WebhookRoute] = None


class WebhookRouter:
    """
    Webhook event router with retry logic

    Routes webhook events to handlers with filtering, retries, and DLQ.

    Usage:
        router = WebhookRouter()

        # Add routes
        router.add_route(
            event_type="candidacy.created",
            handler=handle_candidacy_created,
            max_retries=3
        )

        router.add_route(
            event_type="candidacy.step_changed",
            handler=handle_step_changed,
            filter=lambda data: data.get("to_step") == "offer"
        )

        # Route event
        router.route(payload)
    """

    def __init__(self, enable_dlq: bool = True):
        """
        Initialize webhook router

        Args:
            enable_dlq: Enable dead letter queue for failed events
        """
        self.routes: List[WebhookRoute] = []
        self.enable_dlq = enable_dlq
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.processed_count = 0
        self.failed_count = 0

    def add_route(
        self,
        event_type: str,
        handler: Callable,
        filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        """
        Add route

        Args:
            event_type: Event type pattern ("candidacy.created", "*" for all)
            handler: Handler function
            filter: Optional filter function
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            backoff_multiplier: Exponential backoff multiplier
            max_retry_delay: Maximum retry delay in seconds
        """
        route = WebhookRoute(
            event_type=event_type,
            handler=handler,
            filter=filter,
            max_retries=max_retries,
            retry_delay=retry_delay,
            backoff_multiplier=backoff_multiplier,
            max_retry_delay=max_retry_delay,
        )

        self.routes.append(route)
        logger.debug(f"Added route for {event_type}")

    def route(self, payload: Dict[str, Any]) -> None:
        """
        Route webhook event

        Args:
            payload: Webhook payload
        """
        event_type = payload.get("event")
        event_id = payload.get("event_id")

        logger.info(f"Routing webhook event: {event_type} (id={event_id})")

        # Find matching routes
        matching_routes = self._find_matching_routes(payload)

        if not matching_routes:
            logger.warning(f"No matching routes for {event_type}")
            return

        # Process each matching route
        for route in matching_routes:
            self._process_route(payload, route)

    def route_raw(self, raw_payload: bytes) -> None:
        """
        Route webhook from raw bytes

        Args:
            raw_payload: Raw webhook payload bytes
        """
        try:
            payload = json.loads(raw_payload)
            self.route(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")

    def _find_matching_routes(self, payload: Dict[str, Any]) -> List[WebhookRoute]:
        """Find routes matching event"""
        event_type = payload.get("event")
        matching = []

        for route in self.routes:
            # Check event type
            if route.event_type != "*" and route.event_type != event_type:
                continue

            # Check filter
            if route.filter and not route.filter(payload.get("data", {})):
                continue

            matching.append(route)

        return matching

    def _process_route(self, payload: Dict[str, Any], route: WebhookRoute) -> None:
        """
        Process route with retry logic

        Args:
            payload: Webhook payload
            route: Route to process
        """
        retries = 0
        delay = route.retry_delay

        while retries <= route.max_retries:
            try:
                # Execute handler
                route.handler(payload)

                # Success
                self.processed_count += 1
                logger.debug(
                    f"Successfully processed event with {route.event_type} handler"
                )
                return

            except Exception as e:
                retries += 1
                logger.warning(
                    f"Error in handler (attempt {retries}/{route.max_retries + 1}): {e}"
                )

                if retries <= route.max_retries:
                    # Retry with exponential backoff
                    logger.debug(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * route.backoff_multiplier, route.max_retry_delay)
                else:
                    # Max retries exceeded
                    self.failed_count += 1
                    logger.error(
                        f"Max retries exceeded for {payload.get('event')}",
                        exc_info=True,
                    )

                    # Add to dead letter queue
                    if self.enable_dlq:
                        failed_event = FailedEvent(
                            payload=payload,
                            error=str(e),
                            retries=retries,
                            route=route,
                        )
                        self.dead_letter_queue.append(failed_event)
                        logger.debug(
                            f"Added event to DLQ (size={len(self.dead_letter_queue)})"
                        )

    def get_dead_letter_queue(self) -> List[FailedEvent]:
        """
        Get failed events from dead letter queue

        Returns:
            List of failed events
        """
        return list(self.dead_letter_queue)

    def replay_failed_event(self, failed_event: FailedEvent) -> None:
        """
        Replay failed event

        Args:
            failed_event: Failed event to replay
        """
        logger.info(f"Replaying failed event: {failed_event.payload.get('event_id')}")

        if failed_event.route:
            self._process_route(failed_event.payload, failed_event.route)
        else:
            self.route(failed_event.payload)

    def clear_dead_letter_queue(self) -> None:
        """Clear dead letter queue"""
        self.dead_letter_queue.clear()
        logger.info("Cleared dead letter queue")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get router statistics

        Returns:
            Dictionary with stats
        """
        return {
            "routes": len(self.routes),
            "processed": self.processed_count,
            "failed": self.failed_count,
            "dlq_size": len(self.dead_letter_queue),
        }


class AsyncWebhookRouter:
    """
    Async webhook event router

    Async version of WebhookRouter for async handlers.

    Usage:
        router = AsyncWebhookRouter()

        router.add_route(
            event_type="candidacy.created",
            handler=async_handle_candidacy_created
        )

        await router.route(payload)
    """

    def __init__(self, enable_dlq: bool = True):
        """Initialize async webhook router"""
        self.routes: List[WebhookRoute] = []
        self.enable_dlq = enable_dlq
        self.dead_letter_queue: deque = deque(maxlen=1000)
        self.processed_count = 0
        self.failed_count = 0

    def add_route(
        self,
        event_type: str,
        handler: Callable,
        filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        """Add async route"""
        route = WebhookRoute(
            event_type=event_type,
            handler=handler,
            filter=filter,
            max_retries=max_retries,
            retry_delay=retry_delay,
            backoff_multiplier=backoff_multiplier,
            max_retry_delay=max_retry_delay,
        )

        self.routes.append(route)
        logger.debug(f"Added async route for {event_type}")

    async def route(self, payload: Dict[str, Any]) -> None:
        """Route webhook event asynchronously"""
        event_type = payload.get("event")
        event_id = payload.get("event_id")

        logger.info(f"Routing webhook event: {event_type} (id={event_id})")

        # Find matching routes
        matching_routes = self._find_matching_routes(payload)

        if not matching_routes:
            logger.warning(f"No matching routes for {event_type}")
            return

        # Process each matching route
        for route in matching_routes:
            await self._process_route(payload, route)

    async def route_raw(self, raw_payload: bytes) -> None:
        """Route webhook from raw bytes asynchronously"""
        try:
            payload = json.loads(raw_payload)
            await self.route(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")

    def _find_matching_routes(self, payload: Dict[str, Any]) -> List[WebhookRoute]:
        """Find routes matching event"""
        event_type = payload.get("event")
        matching = []

        for route in self.routes:
            # Check event type
            if route.event_type != "*" and route.event_type != event_type:
                continue

            # Check filter
            if route.filter and not route.filter(payload.get("data", {})):
                continue

            matching.append(route)

        return matching

    async def _process_route(
        self, payload: Dict[str, Any], route: WebhookRoute
    ) -> None:
        """Process route with retry logic asynchronously"""
        import asyncio

        retries = 0
        delay = route.retry_delay

        while retries <= route.max_retries:
            try:
                # Execute async handler
                await route.handler(payload)

                # Success
                self.processed_count += 1
                logger.debug(
                    f"Successfully processed event with {route.event_type} handler"
                )
                return

            except Exception as e:
                retries += 1
                logger.warning(
                    f"Error in async handler (attempt {retries}/{route.max_retries + 1}): {e}"
                )

                if retries <= route.max_retries:
                    # Retry with exponential backoff
                    logger.debug(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay = min(delay * route.backoff_multiplier, route.max_retry_delay)
                else:
                    # Max retries exceeded
                    self.failed_count += 1
                    logger.error(
                        f"Max retries exceeded for {payload.get('event')}",
                        exc_info=True,
                    )

                    # Add to dead letter queue
                    if self.enable_dlq:
                        failed_event = FailedEvent(
                            payload=payload,
                            error=str(e),
                            retries=retries,
                            route=route,
                        )
                        self.dead_letter_queue.append(failed_event)
                        logger.debug(
                            f"Added event to DLQ (size={len(self.dead_letter_queue)})"
                        )

    def get_dead_letter_queue(self) -> List[FailedEvent]:
        """Get failed events from dead letter queue"""
        return list(self.dead_letter_queue)

    async def replay_failed_event(self, failed_event: FailedEvent) -> None:
        """Replay failed event asynchronously"""
        logger.info(f"Replaying failed event: {failed_event.payload.get('event_id')}")

        if failed_event.route:
            await self._process_route(failed_event.payload, failed_event.route)
        else:
            await self.route(failed_event.payload)

    def clear_dead_letter_queue(self) -> None:
        """Clear dead letter queue"""
        self.dead_letter_queue.clear()
        logger.info("Cleared dead letter queue")

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        return {
            "routes": len(self.routes),
            "processed": self.processed_count,
            "failed": self.failed_count,
            "dlq_size": len(self.dead_letter_queue),
        }
