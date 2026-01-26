#!/usr/bin/env python3
"""
HERP Webhook Handlers

Provides webhook event handlers for processing HERP webhook events.

HERP webhooks notify about candidacy changes:
- candidacy.created - New candidacy created
- candidacy.step_changed - Hiring step changed
- candidacy.terminated - Candidacy terminated
- contact.created - Interview scheduled
- contact.updated - Interview updated
- evaluation.submitted - Evaluation submitted
- file.uploaded - File uploaded
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ...utils.logging import get_logger

logger = get_logger(__name__)


class WebhookEvent:
    """
    Webhook event wrapper

    Provides convenient access to webhook event data.
    """

    def __init__(self, raw_payload: Dict[str, Any]):
        """
        Initialize webhook event

        Args:
            raw_payload: Parsed webhook JSON payload
        """
        self.raw_payload = raw_payload
        self.event_type = raw_payload.get("event")
        self.event_id = raw_payload.get("event_id")
        self.timestamp = raw_payload.get("timestamp")
        self.data = raw_payload.get("data", {})

    @property
    def candidacy_id(self) -> Optional[str]:
        """Get candidacy ID from event"""
        return self.data.get("candidacy_id")

    @property
    def contact_id(self) -> Optional[str]:
        """Get contact ID from event"""
        return self.data.get("contact_id")

    @property
    def evaluation_id(self) -> Optional[str]:
        """Get evaluation ID from event"""
        return self.data.get("evaluation_id")

    @property
    def file_id(self) -> Optional[str]:
        """Get file ID from event"""
        return self.data.get("file_id")

    def __repr__(self) -> str:
        return f"WebhookEvent(type={self.event_type}, id={self.event_id})"


HandlerFunc = Callable[[WebhookEvent], None]


class WebhookHandler:
    """
    Webhook event handler

    Routes webhook events to registered handlers based on event type.

    Usage:
        handler = WebhookHandler()

        # Register handlers
        @handler.on("candidacy.created")
        def handle_candidacy_created(event: WebhookEvent):
            print(f"New candidacy: {event.candidacy_id}")

        @handler.on("candidacy.step_changed")
        def handle_step_changed(event: WebhookEvent):
            print(f"Step changed: {event.data}")

        # Process webhook
        handler.handle(payload)
    """

    def __init__(self):
        """Initialize webhook handler"""
        self.handlers: Dict[str, List[HandlerFunc]] = {}
        self.default_handler: Optional[HandlerFunc] = None

    def on(self, event_type: str) -> Callable:
        """
        Decorator to register event handler

        Args:
            event_type: Event type to handle (e.g., "candidacy.created")

        Returns:
            Decorator function
        """

        def decorator(func: HandlerFunc) -> HandlerFunc:
            self.register(event_type, func)
            return func

        return decorator

    def register(self, event_type: str, handler: HandlerFunc) -> None:
        """
        Register event handler

        Args:
            event_type: Event type to handle
            handler: Handler function
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    def register_default(self, handler: HandlerFunc) -> None:
        """
        Register default handler for unhandled events

        Args:
            handler: Default handler function
        """
        self.default_handler = handler
        logger.debug("Registered default handler")

    def handle(self, payload: Dict[str, Any]) -> None:
        """
        Handle webhook event

        Args:
            payload: Webhook payload (parsed JSON)
        """
        event = WebhookEvent(payload)

        logger.info(
            f"Processing webhook event: {event.event_type} (id={event.event_id})"
        )

        # Get handlers for event type
        handlers = self.handlers.get(event.event_type, [])

        if handlers:
            # Execute all registered handlers
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in handler for {event.event_type}: {e}", exc_info=True
                    )
        elif self.default_handler:
            # Use default handler
            try:
                self.default_handler(event)
            except Exception as e:
                logger.error(
                    f"Error in default handler for {event.event_type}: {e}",
                    exc_info=True,
                )
        else:
            logger.warning(f"No handler registered for {event.event_type}")

    def handle_raw(self, raw_payload: bytes) -> None:
        """
        Handle webhook from raw bytes

        Args:
            raw_payload: Raw webhook payload bytes
        """
        try:
            payload = json.loads(raw_payload)
            self.handle(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")


class AsyncWebhookHandler:
    """
    Async webhook event handler

    Routes webhook events to registered async handlers.

    Usage:
        handler = AsyncWebhookHandler()

        @handler.on("candidacy.created")
        async def handle_candidacy_created(event: WebhookEvent):
            await send_notification(event.candidacy_id)

        await handler.handle(payload)
    """

    def __init__(self):
        """Initialize async webhook handler"""
        self.handlers: Dict[str, List[Callable]] = {}
        self.default_handler: Optional[Callable] = None

    def on(self, event_type: str) -> Callable:
        """
        Decorator to register async event handler

        Args:
            event_type: Event type to handle

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            self.register(event_type, func)
            return func

        return decorator

    def register(self, event_type: str, handler: Callable) -> None:
        """
        Register async event handler

        Args:
            event_type: Event type to handle
            handler: Async handler function
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []

        self.handlers[event_type].append(handler)
        logger.debug(f"Registered async handler for {event_type}")

    def register_default(self, handler: Callable) -> None:
        """
        Register default async handler

        Args:
            handler: Default async handler function
        """
        self.default_handler = handler
        logger.debug("Registered default async handler")

    async def handle(self, payload: Dict[str, Any]) -> None:
        """
        Handle webhook event asynchronously

        Args:
            payload: Webhook payload (parsed JSON)
        """
        event = WebhookEvent(payload)

        logger.info(
            f"Processing webhook event: {event.event_type} (id={event.event_id})"
        )

        # Get handlers for event type
        handlers = self.handlers.get(event.event_type, [])

        if handlers:
            # Execute all registered handlers
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(
                        f"Error in async handler for {event.event_type}: {e}",
                        exc_info=True,
                    )
        elif self.default_handler:
            # Use default handler
            try:
                await self.default_handler(event)
            except Exception as e:
                logger.error(
                    f"Error in default async handler for {event.event_type}: {e}",
                    exc_info=True,
                )
        else:
            logger.warning(f"No handler registered for {event.event_type}")

    async def handle_raw(self, raw_payload: bytes) -> None:
        """
        Handle webhook from raw bytes asynchronously

        Args:
            raw_payload: Raw webhook payload bytes
        """
        try:
            payload = json.loads(raw_payload)
            await self.handle(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse webhook payload: {e}")


# Common event handlers


def log_event_handler(event: WebhookEvent) -> None:
    """
    Simple logging handler

    Logs all webhook events to logger.
    """
    logger.info(f"Webhook event: {event.event_type} - {event.data}")


def print_event_handler(event: WebhookEvent) -> None:
    """
    Simple print handler

    Prints all webhook events to stdout.
    """
    print(f"[{datetime.now().isoformat()}] {event.event_type}: {event.data}")
