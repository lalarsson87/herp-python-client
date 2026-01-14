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

from .verifier import (
    WebhookVerifier,
    WebhookVerificationError,
    verify_webhook,
)

from .handlers import (
    WebhookEvent,
    WebhookHandler,
    AsyncWebhookHandler,
    HandlerFunc,
    log_event_handler,
    print_event_handler,
)

from .router import (
    WebhookRoute,
    WebhookRouter,
    AsyncWebhookRouter,
    FailedEvent,
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
]
