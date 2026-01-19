# HERP Webhooks Integration Guide

## Overview

HERP webhooks provide real-time notifications about candidacy changes, interviews, evaluations, and more. This guide covers webhook signature verification, event handling, retry logic, and integration with web frameworks.

## Benefits

✅ **Real-time Updates**: Receive instant notifications of candidacy changes
✅ **Secure**: HMAC-SHA256 signature verification
✅ **Reliable**: Automatic retry with exponential backoff
✅ **Flexible**: Filter and route events to custom handlers
✅ **Observable**: Dead letter queue for failed events
✅ **Framework Integration**: Works with FastAPI, Flask, Django

## Quick Start

```python
from src.core.herp.webhooks import (
    WebhookVerifier,
    WebhookHandler,
    WebhookRouter,
)

# 1. Verify webhook signature
verifier = WebhookVerifier(webhook_secret="your_secret_from_herp")

try:
    verifier.verify(
        payload=request.body,
        signature=request.headers["X-HERP-Signature"],
        timestamp=request.headers["X-HERP-Timestamp"]
    )
except WebhookVerificationError:
    return {"error": "Invalid signature"}, 401

# 2. Handle webhook events
handler = WebhookHandler()

@handler.on("candidacy.created")
def handle_new_candidacy(event):
    print(f"New candidacy: {event.candidacy_id}")
    # Send notification, update database, etc.

handler.handle(request.json)
```

## Core Concepts

### Webhook Events

HERP sends webhooks for these events:

**Candidacy Events**:
- `candidacy.created` - New candidacy created
- `candidacy.step_changed` - Hiring step changed
- `candidacy.status_changed` - Status changed
- `candidacy.terminated` - Candidacy terminated

**Interview Events**:
- `contact.created` - Interview scheduled
- `contact.updated` - Interview updated

**Evaluation Events**:
- `evaluation.submitted` - Evaluation submitted

**File Events**:
- `file.uploaded` - File uploaded

### Webhook Payload

```json
{
  "event": "candidacy.created",
  "event_id": "evt_abc123",
  "timestamp": "1706241600",
  "data": {
    "candidacy_id": "cand_123",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "requisition_id": "req_001",
    "step": "application"
  }
}
```

### Webhook Headers

```
X-HERP-Signature: 3f8c1b2a...
X-HERP-Timestamp: 1706241600
Content-Type: application/json
```

## Signature Verification

HERP uses HMAC-SHA256 to sign webhooks:

```python
from src.core.herp.webhooks import WebhookVerifier, WebhookVerificationError

# Initialize verifier with secret from HERP settings
verifier = WebhookVerifier(
    webhook_secret="your_webhook_secret",
    tolerance_seconds=300  # 5 minutes (prevents replay attacks)
)

# Verify in webhook endpoint
try:
    verifier.verify(
        payload=request.body,  # Raw bytes
        signature=request.headers.get("X-HERP-Signature"),
        timestamp=request.headers.get("X-HERP-Timestamp")
    )
    # Valid webhook
except WebhookVerificationError as e:
    # Invalid signature or expired
    return {"error": str(e)}, 401
```

### Verification Details

**Signature Computation**:
```
signature = HMAC-SHA256(secret, timestamp + payload)
```

**Security Features**:
- Constant-time signature comparison (prevents timing attacks)
- Timestamp verification (prevents replay attacks)
- 5-minute tolerance window (configurable)

### Convenience Function

```python
from src.core.herp.webhooks import verify_webhook

verify_webhook(
    payload=request.body,
    signature=request.headers["X-HERP-Signature"],
    timestamp=request.headers["X-HERP-Timestamp"],
    webhook_secret="your_secret"
)
```

## Event Handlers

### Basic Handler

```python
from src.core.herp.webhooks import WebhookHandler

handler = WebhookHandler()

# Register handler with decorator
@handler.on("candidacy.created")
def handle_candidacy_created(event):
    print(f"Candidacy created: {event.candidacy_id}")
    print(f"Name: {event.data['name']}")
    print(f"Email: {event.data['email']}")

# Or register directly
def handle_step_changed(event):
    print(f"Step changed: {event.data}")

handler.register("candidacy.step_changed", handle_step_changed)

# Process webhook
handler.handle(payload)
```

### Multiple Handlers

```python
handler = WebhookHandler()

@handler.on("candidacy.created")
def send_slack_notification(event):
    slack.send(f"New candidate: {event.data['name']}")

@handler.on("candidacy.created")
def update_database(event):
    db.candidates.insert(event.data)

@handler.on("candidacy.created")
def send_email(event):
    email.send_welcome(event.data['email'])

# All three handlers will be called
handler.handle(payload)
```

### Default Handler

```python
handler = WebhookHandler()

# Handle specific events
@handler.on("candidacy.created")
def handle_created(event):
    print("Created")

# Catch all other events
def handle_default(event):
    print(f"Unhandled event: {event.event_type}")

handler.register_default(handle_default)
```

### Async Handlers

```python
from src.core.herp.webhooks import AsyncWebhookHandler

handler = AsyncWebhookHandler()

@handler.on("candidacy.created")
async def handle_candidacy_created(event):
    await send_notification(event.candidacy_id)
    await update_database(event.data)

# Process asynchronously
await handler.handle(payload)
```

## Webhook Router

The router provides event filtering, retry logic, and dead letter queue.

### Basic Routing

```python
from src.core.herp.webhooks import WebhookRouter

router = WebhookRouter(enable_dlq=True)

# Add routes
router.add_route(
    event_type="candidacy.created",
    handler=handle_candidacy_created,
    max_retries=3,
    retry_delay=1.0,
    backoff_multiplier=2.0,
)

router.add_route(
    event_type="candidacy.step_changed",
    handler=handle_step_changed,
)

# Route event
router.route(payload)
```

### Event Filtering

```python
# Only handle offers
def is_offer(data):
    return data.get("to_step") == "offer"

router.add_route(
    event_type="candidacy.step_changed",
    handler=handle_offer_extended,
    filter=is_offer,
)

# Only handle senior positions
def is_senior(data):
    requisition_id = data.get("requisition_id")
    return requisition_id in ["req_senior_001", "req_senior_002"]

router.add_route(
    event_type="candidacy.created",
    handler=handle_senior_candidate,
    filter=is_senior,
)
```

### Catch-All Route

```python
# Handle all events
router.add_route(
    event_type="*",
    handler=log_all_events,
)
```

### Retry Configuration

```python
router.add_route(
    event_type="candidacy.created",
    handler=send_slack_notification,
    max_retries=5,              # Retry up to 5 times
    retry_delay=1.0,            # Start with 1 second delay
    backoff_multiplier=2.0,     # Double delay each retry
    max_retry_delay=60.0,       # Cap at 60 seconds
)

# Retry sequence:
# Attempt 1: fails
# Wait 1s, Attempt 2: fails
# Wait 2s, Attempt 3: fails
# Wait 4s, Attempt 4: fails
# Wait 8s, Attempt 5: fails
# Wait 16s, Attempt 6: fails (max retries exceeded)
```

### Dead Letter Queue

```python
router = WebhookRouter(enable_dlq=True)

# Add routes
router.add_route("candidacy.created", handle_created, max_retries=3)

# Process events
router.route(payload1)  # Success
router.route(payload2)  # Fails after 3 retries -> DLQ

# Check DLQ
failed_events = router.get_dead_letter_queue()
for event in failed_events:
    print(f"Failed: {event.payload['event']}")
    print(f"Error: {event.error}")
    print(f"Retries: {event.retries}")

# Replay failed event
router.replay_failed_event(failed_events[0])

# Clear DLQ
router.clear_dead_letter_queue()
```

### Router Statistics

```python
stats = router.get_stats()
print(f"Routes: {stats['routes']}")
print(f"Processed: {stats['processed']}")
print(f"Failed: {stats['failed']}")
print(f"DLQ size: {stats['dlq_size']}")
```

## Framework Integration

### FastAPI

```python
from fastapi import FastAPI, Request, HTTPException
from src.core.herp.webhooks import WebhookVerifier, WebhookHandler

app = FastAPI()

verifier = WebhookVerifier(webhook_secret="your_secret")
handler = WebhookHandler()

@handler.on("candidacy.created")
def handle_created(event):
    print(f"New candidacy: {event.candidacy_id}")

@app.post("/webhooks/herp")
async def herp_webhook(request: Request):
    # Get raw body
    body = await request.body()

    # Verify signature
    try:
        verifier.verify(
            payload=body,
            signature=request.headers.get("X-HERP-Signature"),
            timestamp=request.headers.get("X-HERP-Timestamp")
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse and handle
    payload = await request.json()
    handler.handle(payload)

    return {"status": "ok"}
```

### Flask

```python
from flask import Flask, request, jsonify
from src.core.herp.webhooks import WebhookVerifier, WebhookHandler

app = Flask(__name__)

verifier = WebhookVerifier(webhook_secret="your_secret")
handler = WebhookHandler()

@handler.on("candidacy.created")
def handle_created(event):
    print(f"New candidacy: {event.candidacy_id}")

@app.route("/webhooks/herp", methods=["POST"])
def herp_webhook():
    # Verify signature
    try:
        verifier.verify(
            payload=request.data,
            signature=request.headers.get("X-HERP-Signature"),
            timestamp=request.headers.get("X-HERP-Timestamp")
        )
    except Exception as e:
        return jsonify({"error": "Invalid signature"}), 401

    # Handle event
    handler.handle(request.json)

    return jsonify({"status": "ok"})
```

### Django

```python
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from src.core.herp.webhooks import WebhookVerifier, WebhookHandler
import json

verifier = WebhookVerifier(webhook_secret="your_secret")
handler = WebhookHandler()

@handler.on("candidacy.created")
def handle_created(event):
    print(f"New candidacy: {event.candidacy_id}")

@csrf_exempt
def herp_webhook(request):
    if request.method != "POST":
        return HttpResponseForbidden()

    # Verify signature
    try:
        verifier.verify(
            payload=request.body,
            signature=request.META.get("HTTP_X_HERP_SIGNATURE"),
            timestamp=request.META.get("HTTP_X_HERP_TIMESTAMP")
        )
    except Exception:
        return HttpResponseForbidden("Invalid signature")

    # Handle event
    payload = json.loads(request.body)
    handler.handle(payload)

    return JsonResponse({"status": "ok"})
```

## Production Patterns

### Complete Example

```python
from src.core.herp.webhooks import (
    WebhookVerifier,
    WebhookRouter,
    WebhookVerificationError,
)
import logging

logger = logging.getLogger(__name__)

# Initialize components
verifier = WebhookVerifier(
    webhook_secret="prod_secret",
    tolerance_seconds=300
)

router = WebhookRouter(enable_dlq=True)

# Handlers
def handle_candidacy_created(event):
    logger.info(f"New candidacy: {event.candidacy_id}")
    # Send to Slack
    slack_client.send_message(f"New candidate: {event.data['name']}")
    # Update database
    db.candidates.insert(event.data)

def handle_step_changed(event):
    logger.info(f"Step changed: {event.candidacy_id}")
    # Send notification
    notify_recruiters(event.candidacy_id, event.data['to_step'])

def handle_offer_extended(event):
    logger.info(f"Offer extended: {event.candidacy_id}")
    # Special handling for offers
    send_offer_notification(event.data)

# Routes
router.add_route(
    event_type="candidacy.created",
    handler=handle_candidacy_created,
    max_retries=5,
)

router.add_route(
    event_type="candidacy.step_changed",
    handler=handle_step_changed,
    max_retries=3,
)

router.add_route(
    event_type="candidacy.step_changed",
    handler=handle_offer_extended,
    filter=lambda data: data.get("to_step") == "offer",
    max_retries=5,
)

# Webhook endpoint
@app.post("/webhooks/herp")
async def herp_webhook(request: Request):
    body = await request.body()

    # Verify
    try:
        verifier.verify(
            payload=body,
            signature=request.headers.get("X-HERP-Signature"),
            timestamp=request.headers.get("X-HERP-Timestamp")
        )
    except WebhookVerificationError as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Route
    payload = await request.json()
    router.route(payload)

    # Check DLQ periodically
    if router.get_stats()["dlq_size"] > 10:
        logger.error(f"DLQ has {router.get_stats()['dlq_size']} events")
        # Alert ops team

    return {"status": "ok"}
```

### Monitoring & Alerting

```python
# Periodic DLQ check
@app.on_event("startup")
@repeat_every(seconds=300)  # Every 5 minutes
async def check_dlq():
    stats = router.get_stats()

    if stats["dlq_size"] > 0:
        logger.warning(f"DLQ has {stats['dlq_size']} failed events")

        # Replay failed events
        for failed_event in router.get_dead_letter_queue():
            logger.info(f"Replaying event: {failed_event.payload['event_id']}")
            router.replay_failed_event(failed_event)

        # Clear DLQ after replay
        router.clear_dead_letter_queue()

    # Log stats
    logger.info(f"Webhook stats: {stats}")
```

## Best Practices

### 1. Always Verify Signatures

```python
# ✅ Good - verify signature
verifier.verify(payload, signature, timestamp)
handler.handle(payload)

# ❌ Bad - skip verification
handler.handle(payload)
```

### 2. Use Retry Logic

```python
# ✅ Good - use router with retries
router.add_route("candidacy.created", handler, max_retries=3)
router.route(payload)

# ⭕ OK but less resilient
handler.handle(payload)
```

### 3. Monitor DLQ

```python
# ✅ Good - monitor and replay
stats = router.get_stats()
if stats["dlq_size"] > 10:
    alert_ops_team()
    replay_failed_events()

# ❌ Bad - ignore failures
# No DLQ monitoring
```

### 4. Use Filters for Efficiency

```python
# ✅ Good - filter at routing level
router.add_route(
    "candidacy.step_changed",
    handle_offer,
    filter=lambda d: d.get("to_step") == "offer"
)

# ⭕ OK but less efficient
@handler.on("candidacy.step_changed")
def handle_step(event):
    if event.data.get("to_step") == "offer":
        handle_offer(event)
```

### 5. Log Webhook Events

```python
# ✅ Good - comprehensive logging
@handler.on("*")
def log_event(event):
    logger.info(f"Webhook: {event.event_type} (id={event.event_id})")

# Add to router
from src.core.herp.webhooks import log_event_handler
router.add_route("*", log_event_handler)
```

## Testing

### Mock Webhook Payloads

```python
# Test payload
test_payload = {
    "event": "candidacy.created",
    "event_id": "evt_test_123",
    "timestamp": "1706241600",
    "data": {
        "candidacy_id": "cand_test",
        "name": "Test Candidate",
        "email": "test@example.com",
    }
}

# Test handler
handler = WebhookHandler()

@handler.on("candidacy.created")
def test_handler(event):
    assert event.candidacy_id == "cand_test"
    assert event.data["name"] == "Test Candidate"

handler.handle(test_payload)
```

### Mock Signature Verification

```python
import pytest
from src.core.herp.webhooks import WebhookVerifier, WebhookVerificationError

def test_signature_verification():
    secret = "test_secret"
    verifier = WebhookVerifier(secret)

    payload = b'{"event": "test"}'
    timestamp = "1706241600"

    # Compute valid signature
    signature = verifier._compute_signature(payload, timestamp)

    # Should succeed
    verifier.verify(payload, signature, timestamp)

    # Should fail with wrong signature
    with pytest.raises(WebhookVerificationError):
        verifier.verify(payload, "wrong_signature", timestamp)
```

## Summary

✅ **Signature Verification**: HMAC-SHA256 with timestamp validation
✅ **Event Handlers**: Decorator-based registration with multiple handlers per event
✅ **Routing**: Event filtering, retry logic, exponential backoff
✅ **Reliability**: Dead letter queue for failed events
✅ **Async Support**: Full async/await support
✅ **Framework Integration**: FastAPI, Flask, Django examples
✅ **Production Ready**: Monitoring, alerting, replay capabilities

Webhooks provide real-time integration with HERP, enabling instant notifications and automated workflows for candidacy changes, interviews, and evaluations.
