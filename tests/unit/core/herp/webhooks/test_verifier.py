"""
Tests for webhook signature verification
"""

import hashlib
import hmac
import time
from unittest.mock import patch

import pytest

from src.core.herp.webhooks.verifier import (
    WebhookVerificationError,
    WebhookVerifier,
    verify_webhook,
)


class TestWebhookVerifier:
    """Test WebhookVerifier class"""

    @pytest.fixture
    def secret(self):
        """Test webhook secret"""
        return "test_webhook_secret_123"

    @pytest.fixture
    def verifier(self, secret):
        """Create verifier instance"""
        return WebhookVerifier(secret, tolerance_seconds=300)

    @pytest.fixture
    def payload(self):
        """Test payload"""
        return b'{"event": "candidacy.created", "data": {"id": "123"}}'

    def compute_valid_signature(
        self, secret: str, payload: bytes, timestamp: str
    ) -> str:
        """Helper to compute valid signature"""
        signed_payload = timestamp.encode("utf-8") + payload
        return hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

    def test_initialization(self, secret):
        """Test verifier initialization"""
        verifier = WebhookVerifier(secret, tolerance_seconds=600)

        assert verifier.webhook_secret == secret.encode("utf-8")
        assert verifier.tolerance_seconds == 600

    def test_initialization_default_tolerance(self, secret):
        """Test verifier uses default tolerance"""
        verifier = WebhookVerifier(secret)

        assert verifier.tolerance_seconds == 300

    def test_verify_valid_signature(self, verifier, secret, payload):
        """Test verification succeeds with valid signature"""
        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(secret, payload, timestamp)

        # Should not raise
        verifier.verify(payload, signature, timestamp)

    def test_verify_invalid_signature(self, verifier, payload):
        """Test verification fails with invalid signature"""
        timestamp = str(int(time.time()))
        invalid_signature = "invalid_signature_123"

        with pytest.raises(WebhookVerificationError, match="Invalid webhook signature"):
            verifier.verify(payload, invalid_signature, timestamp)

    def test_verify_wrong_signature(self, verifier, secret, payload):
        """Test verification fails with signature for different payload"""
        timestamp = str(int(time.time()))
        # Compute signature for different payload
        wrong_payload = b'{"event": "different"}'
        signature = self.compute_valid_signature(secret, wrong_payload, timestamp)

        with pytest.raises(WebhookVerificationError, match="Invalid webhook signature"):
            verifier.verify(payload, signature, timestamp)

    def test_verify_wrong_secret(self, payload):
        """Test verification fails with wrong secret"""
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"

        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(correct_secret, payload, timestamp)

        verifier = WebhookVerifier(wrong_secret)

        with pytest.raises(WebhookVerificationError, match="Invalid webhook signature"):
            verifier.verify(payload, signature, timestamp)

    def test_verify_timestamp_too_old(self, verifier, secret, payload):
        """Test verification fails with old timestamp"""
        # Timestamp from 10 minutes ago (tolerance is 5 minutes)
        old_timestamp = str(int(time.time()) - 600)
        signature = self.compute_valid_signature(secret, payload, old_timestamp)

        with pytest.raises(WebhookVerificationError, match="Webhook timestamp too old"):
            verifier.verify(payload, signature, old_timestamp)

    def test_verify_timestamp_from_future(self, verifier, secret, payload):
        """Test verification fails with future timestamp"""
        # Timestamp from 10 minutes in the future
        future_timestamp = str(int(time.time()) + 600)
        signature = self.compute_valid_signature(secret, payload, future_timestamp)

        with pytest.raises(
            WebhookVerificationError, match="Webhook timestamp from future"
        ):
            verifier.verify(payload, signature, future_timestamp)

    def test_verify_timestamp_within_tolerance(self, verifier, secret, payload):
        """Test verification succeeds with timestamp within tolerance"""
        # Timestamp from 4 minutes ago (within 5 minute tolerance)
        recent_timestamp = str(int(time.time()) - 240)
        signature = self.compute_valid_signature(secret, payload, recent_timestamp)

        # Should not raise
        verifier.verify(payload, signature, recent_timestamp)

    def test_verify_invalid_timestamp_format(self, verifier, payload):
        """Test verification fails with invalid timestamp format"""
        invalid_timestamp = "not_a_timestamp"
        signature = "some_signature"

        with pytest.raises(WebhookVerificationError, match="Invalid timestamp format"):
            verifier.verify(payload, signature, invalid_timestamp)

    def test_verify_none_timestamp(self, verifier, payload):
        """Test verification fails with None timestamp"""
        signature = "some_signature"

        with pytest.raises(WebhookVerificationError, match="Invalid timestamp format"):
            verifier.verify(payload, signature, None)

    def test_verify_custom_tolerance(self, secret, payload):
        """Test verifier respects custom tolerance"""
        # Very short tolerance: 10 seconds
        verifier = WebhookVerifier(secret, tolerance_seconds=10)

        # Timestamp from 30 seconds ago (outside 10s tolerance)
        old_timestamp = str(int(time.time()) - 30)
        signature = self.compute_valid_signature(secret, payload, old_timestamp)

        with pytest.raises(WebhookVerificationError, match="Webhook timestamp too old"):
            verifier.verify(payload, signature, old_timestamp)

    def test_verify_or_none_valid(self, verifier, secret, payload):
        """Test verify_or_none returns True for valid signature"""
        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(secret, payload, timestamp)

        result = verifier.verify_or_none(payload, signature, timestamp)

        assert result is True

    def test_verify_or_none_invalid(self, verifier, payload):
        """Test verify_or_none returns False for invalid signature"""
        timestamp = str(int(time.time()))
        invalid_signature = "invalid"

        result = verifier.verify_or_none(payload, invalid_signature, timestamp)

        assert result is False

    def test_verify_or_none_missing_signature(self, verifier, payload):
        """Test verify_or_none returns False when signature is None"""
        timestamp = str(int(time.time()))

        result = verifier.verify_or_none(payload, None, timestamp)

        assert result is False

    def test_verify_or_none_missing_timestamp(self, verifier, payload):
        """Test verify_or_none returns False when timestamp is None"""
        result = verifier.verify_or_none(payload, "signature", None)

        assert result is False

    def test_verify_or_none_both_missing(self, verifier, payload):
        """Test verify_or_none returns False when both are None"""
        result = verifier.verify_or_none(payload, None, None)

        assert result is False

    def test_compute_signature_deterministic(self, verifier, payload):
        """Test signature computation is deterministic"""
        timestamp = str(int(time.time()))

        sig1 = verifier._compute_signature(payload, timestamp)
        sig2 = verifier._compute_signature(payload, timestamp)

        assert sig1 == sig2

    def test_compute_signature_different_for_different_payloads(self, verifier):
        """Test different payloads produce different signatures"""
        timestamp = str(int(time.time()))
        payload1 = b'{"event": "test1"}'
        payload2 = b'{"event": "test2"}'

        sig1 = verifier._compute_signature(payload1, timestamp)
        sig2 = verifier._compute_signature(payload2, timestamp)

        assert sig1 != sig2

    def test_compute_signature_different_for_different_timestamps(
        self, verifier, payload
    ):
        """Test different timestamps produce different signatures"""
        timestamp1 = str(int(time.time()))
        timestamp2 = str(int(time.time()) + 1)

        sig1 = verifier._compute_signature(payload, timestamp1)
        sig2 = verifier._compute_signature(payload, timestamp2)

        assert sig1 != sig2

    def test_empty_payload(self, verifier, secret):
        """Test verification works with empty payload"""
        payload = b""
        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(secret, payload, timestamp)

        # Should not raise
        verifier.verify(payload, signature, timestamp)

    def test_large_payload(self, verifier, secret):
        """Test verification works with large payload"""
        payload = b"x" * 1_000_000  # 1MB payload
        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(secret, payload, timestamp)

        # Should not raise
        verifier.verify(payload, signature, timestamp)

    def test_special_characters_in_payload(self, verifier, secret):
        """Test verification works with special characters"""
        payload = (
            b'{"text": "\xe2\x9c\x93 \xc2\xa9 \xf0\x9f\x8e\x89"}'  # Unicode characters
        )
        timestamp = str(int(time.time()))
        signature = self.compute_valid_signature(secret, payload, timestamp)

        # Should not raise
        verifier.verify(payload, signature, timestamp)


class TestVerifyWebhookFunction:
    """Test verify_webhook convenience function"""

    def test_verify_webhook_success(self):
        """Test verify_webhook succeeds with valid signature"""
        secret = "test_secret"
        payload = b'{"event": "test"}'
        timestamp = str(int(time.time()))

        # Compute valid signature
        signed_payload = timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # Should not raise
        verify_webhook(payload, signature, timestamp, secret)

    def test_verify_webhook_failure(self):
        """Test verify_webhook fails with invalid signature"""
        secret = "test_secret"
        payload = b'{"event": "test"}'
        timestamp = str(int(time.time()))
        invalid_signature = "invalid"

        with pytest.raises(WebhookVerificationError):
            verify_webhook(payload, invalid_signature, timestamp, secret)

    def test_verify_webhook_custom_tolerance(self):
        """Test verify_webhook uses custom tolerance"""
        secret = "test_secret"
        payload = b'{"event": "test"}'
        # Timestamp from 30 seconds ago
        old_timestamp = str(int(time.time()) - 30)

        signed_payload = old_timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # With 60s tolerance, should succeed
        verify_webhook(payload, signature, old_timestamp, secret, tolerance_seconds=60)

        # With 10s tolerance, should fail
        with pytest.raises(WebhookVerificationError):
            verify_webhook(
                payload, signature, old_timestamp, secret, tolerance_seconds=10
            )


class TestWebhookVerificationEdgeCases:
    """Test edge cases for webhook verification"""

    def test_timing_attack_resistance(self):
        """Test verification uses constant-time comparison"""
        # WebhookVerifier uses hmac.compare_digest which is timing-safe
        secret = "secret"
        payload = b"payload"
        timestamp = str(int(time.time()))

        verifier = WebhookVerifier(secret)

        # Compute valid signature
        signed_payload = timestamp.encode("utf-8") + payload
        valid_sig = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # Valid signature should succeed
        verifier.verify(payload, valid_sig, timestamp)

        # Invalid signature should fail (even if same length)
        invalid_sig = "a" * len(valid_sig)
        with pytest.raises(WebhookVerificationError):
            verifier.verify(payload, invalid_sig, timestamp)

    def test_signature_case_sensitivity(self):
        """Test signature verification is case-sensitive"""
        secret = "secret"
        payload = b"payload"
        timestamp = str(int(time.time()))

        verifier = WebhookVerifier(secret)

        # Compute valid signature
        signed_payload = timestamp.encode("utf-8") + payload
        valid_sig = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # Valid signature (lowercase) should work
        verifier.verify(payload, valid_sig, timestamp)

        # Uppercase signature should fail
        with pytest.raises(WebhookVerificationError):
            verifier.verify(payload, valid_sig.upper(), timestamp)

    def test_replay_attack_prevention(self):
        """Test replay attack prevention via timestamp validation"""
        secret = "secret"
        payload = b"payload"

        # Create signature for old timestamp
        old_timestamp = str(int(time.time()) - 1000)  # 16 minutes ago
        signed_payload = old_timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        verifier = WebhookVerifier(secret, tolerance_seconds=300)  # 5 minute tolerance

        # Should reject old timestamp (replay attack)
        with pytest.raises(WebhookVerificationError, match="Webhook timestamp too old"):
            verifier.verify(payload, signature, old_timestamp)

    def test_zero_tolerance(self):
        """Test verifier with zero tolerance"""
        secret = "secret"
        payload = b"payload"
        verifier = WebhookVerifier(secret, tolerance_seconds=0)

        # Even 1 second old should fail
        old_timestamp = str(int(time.time()) - 1)
        signed_payload = old_timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        with pytest.raises(WebhookVerificationError):
            verifier.verify(payload, signature, old_timestamp)

    def test_very_large_tolerance(self):
        """Test verifier with very large tolerance"""
        secret = "secret"
        payload = b"payload"
        verifier = WebhookVerifier(secret, tolerance_seconds=86400)  # 24 hours

        # 12 hours old should succeed
        old_timestamp = str(int(time.time()) - 43200)
        signed_payload = old_timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # Should not raise
        verifier.verify(payload, signature, old_timestamp)

    @patch("time.time")
    def test_timestamp_validation_uses_current_time(self, mock_time):
        """Test timestamp validation uses current time correctly"""
        mock_time.return_value = 1000000.0  # Fixed current time

        secret = "secret"
        payload = b"payload"
        verifier = WebhookVerifier(secret, tolerance_seconds=100)

        # Timestamp from mock current time - 50 seconds (within tolerance)
        timestamp = str(int(mock_time.return_value) - 50)
        signed_payload = timestamp.encode("utf-8") + payload
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()

        # Should succeed
        verifier.verify(payload, signature, timestamp)

        # Timestamp from mock current time - 150 seconds (outside tolerance)
        old_timestamp = str(int(mock_time.return_value) - 150)
        signed_payload_old = old_timestamp.encode("utf-8") + payload
        signature_old = hmac.new(
            secret.encode("utf-8"), signed_payload_old, hashlib.sha256
        ).hexdigest()

        # Should fail
        with pytest.raises(WebhookVerificationError):
            verifier.verify(payload, signature_old, old_timestamp)
