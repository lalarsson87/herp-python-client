#!/usr/bin/env python3
"""
HERP Webhook Signature Verifier

Provides secure webhook signature verification to ensure webhook requests
are authentic and from HERP.

HERP webhooks use HMAC-SHA256 for signature verification:
- Signature is sent in X-HERP-Signature header
- Timestamp is sent in X-HERP-Timestamp header
- Computed as: HMAC-SHA256(secret, timestamp + payload)
"""

import hmac
import hashlib
import time
from typing import Optional
from ...utils.logging import get_logger


logger = get_logger(__name__)


class WebhookVerificationError(Exception):
    """Raised when webhook verification fails"""
    pass


class WebhookVerifier:
    """
    Verifies HERP webhook signatures

    Usage:
        verifier = WebhookVerifier(webhook_secret="your_secret")

        # In your webhook endpoint
        verifier.verify(
            payload=request.body,
            signature=request.headers["X-HERP-Signature"],
            timestamp=request.headers["X-HERP-Timestamp"]
        )
    """

    def __init__(
        self,
        webhook_secret: str,
        tolerance_seconds: int = 300  # 5 minutes
    ):
        """
        Initialize webhook verifier

        Args:
            webhook_secret: Webhook secret from HERP settings
            tolerance_seconds: Maximum age of webhook in seconds (prevents replay attacks)
        """
        self.webhook_secret = webhook_secret.encode('utf-8')
        self.tolerance_seconds = tolerance_seconds

    def verify(
        self,
        payload: bytes,
        signature: str,
        timestamp: str
    ) -> None:
        """
        Verify webhook signature

        Args:
            payload: Raw webhook payload (bytes)
            signature: Signature from X-HERP-Signature header
            timestamp: Timestamp from X-HERP-Timestamp header

        Raises:
            WebhookVerificationError: If verification fails
        """
        # Verify timestamp is not too old (prevent replay attacks)
        self._verify_timestamp(timestamp)

        # Compute expected signature
        expected_signature = self._compute_signature(payload, timestamp)

        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Webhook signature verification failed")
            raise WebhookVerificationError("Invalid webhook signature")

        logger.debug(f"Webhook signature verified successfully")

    def _verify_timestamp(self, timestamp: str) -> None:
        """
        Verify timestamp is within tolerance

        Args:
            timestamp: Unix timestamp string

        Raises:
            WebhookVerificationError: If timestamp is too old or invalid
        """
        try:
            webhook_time = int(timestamp)
        except (ValueError, TypeError):
            raise WebhookVerificationError("Invalid timestamp format")

        current_time = int(time.time())
        age = current_time - webhook_time

        if age > self.tolerance_seconds:
            logger.warning(
                f"Webhook timestamp too old: {age}s (tolerance: {self.tolerance_seconds}s)"
            )
            raise WebhookVerificationError(
                f"Webhook timestamp too old: {age}s"
            )

        if age < -self.tolerance_seconds:
            logger.warning(f"Webhook timestamp from future: {age}s")
            raise WebhookVerificationError(
                "Webhook timestamp from future"
            )

    def _compute_signature(self, payload: bytes, timestamp: str) -> str:
        """
        Compute HMAC-SHA256 signature

        Args:
            payload: Raw payload bytes
            timestamp: Unix timestamp string

        Returns:
            Hex-encoded signature
        """
        # Signed payload: timestamp + payload
        signed_payload = timestamp.encode('utf-8') + payload

        # Compute HMAC-SHA256
        signature = hmac.new(
            self.webhook_secret,
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_or_none(
        self,
        payload: bytes,
        signature: Optional[str],
        timestamp: Optional[str]
    ) -> bool:
        """
        Verify webhook signature, returning boolean instead of raising

        Args:
            payload: Raw webhook payload
            signature: Signature from header (optional)
            timestamp: Timestamp from header (optional)

        Returns:
            True if valid, False otherwise
        """
        if not signature or not timestamp:
            return False

        try:
            self.verify(payload, signature, timestamp)
            return True
        except WebhookVerificationError:
            return False


def verify_webhook(
    payload: bytes,
    signature: str,
    timestamp: str,
    webhook_secret: str,
    tolerance_seconds: int = 300
) -> None:
    """
    Convenience function to verify webhook

    Args:
        payload: Raw webhook payload
        signature: Signature from X-HERP-Signature header
        timestamp: Timestamp from X-HERP-Timestamp header
        webhook_secret: Webhook secret from HERP
        tolerance_seconds: Maximum webhook age in seconds

    Raises:
        WebhookVerificationError: If verification fails
    """
    verifier = WebhookVerifier(webhook_secret, tolerance_seconds)
    verifier.verify(payload, signature, timestamp)
