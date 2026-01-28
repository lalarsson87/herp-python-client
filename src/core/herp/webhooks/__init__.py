"""
HERP Webhooks Module

Provides webhook signature verification, event handling, and routing.

Components:
- WebhookVerifier: Signature verification (HMAC-SHA256)
- WebhookHandler: Event handler with registration
- WebhookRouter: Event routing with retry logic
- WebhookEvent: Event wrapper

Usage:
    from src.core.herp.webhooks import (
        WebhookVerifier,
        WebhookHandler,
        WebhookRouter,
        verify_webhook,
    )

    # Verify webhook
    verifier = WebhookVerifier(webhook_secret="your_secret")
    verifier.verify(payload, signature, timestamp)

    # Handle events
    handler = WebhookHandler()

    @handler.on("candidacy.created")
    def handle_created(event):
        print(f"New candidacy: {event.candidacy_id}")

    handler.handle(payload)

    # Route with retries
    router = WebhookRouter()
    router.add_route("candidacy.created", handle_created, max_retries=3)
    router.route(payload)
"""

from .handlers import (
    AsyncWebhookHandler,
    HandlerFunc,
    WebhookEvent,
    WebhookHandler,
    log_event_handler,
    print_event_handler,
)
from .replay import EventReplayer, EventStore
from .router import (
    AsyncWebhookRouter,
    FailedEvent,
    WebhookRoute,
    WebhookRouter,
)
from .verifier import (
    WebhookVerificationError,
    WebhookVerifier,
    verify_webhook,
)

__all__ = [
    # Verifier
    "WebhookVerifier",
    "WebhookVerificationError",
    "verify_webhook",
    # Handlers
    "WebhookEvent",
    "WebhookHandler",
    "AsyncWebhookHandler",
    "HandlerFunc",
    "log_event_handler",
    "print_event_handler",
    # Router
    "WebhookRoute",
    "WebhookRouter",
    "AsyncWebhookRouter",
    "FailedEvent",
    # Replay
    "EventStore",
    "EventReplayer",
]
