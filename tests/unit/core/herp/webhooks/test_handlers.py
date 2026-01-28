"""
Tests for webhook event handlers
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.core.herp.webhooks.handlers import (
    AsyncWebhookHandler,
    WebhookEvent,
    WebhookHandler,
    log_event_handler,
    print_event_handler,
)


class TestWebhookEvent:
    """Test WebhookEvent wrapper"""

    def test_initialization(self):
        """Test event initialization"""
        payload = {
            "event": "candidacy.created",
            "event_id": "evt_123",
            "timestamp": "2026-01-28T10:00:00Z",
            "data": {
                "candidacy_id": "cand_456",
                "name": "John Doe",
            },
        }

        event = WebhookEvent(payload)

        assert event.raw_payload == payload
        assert event.event_type == "candidacy.created"
        assert event.event_id == "evt_123"
        assert event.timestamp == "2026-01-28T10:00:00Z"
        assert event.data == payload["data"]

    def test_initialization_missing_fields(self):
        """Test event with missing fields"""
        payload = {}

        event = WebhookEvent(payload)

        assert event.event_type is None
        assert event.event_id is None
        assert event.timestamp is None
        assert event.data == {}

    def test_candidacy_id_property(self):
        """Test candidacy_id property"""
        payload = {
            "event": "candidacy.created",
            "data": {"candidacy_id": "cand_123"},
        }

        event = WebhookEvent(payload)

        assert event.candidacy_id == "cand_123"

    def test_candidacy_id_none(self):
        """Test candidacy_id when not present"""
        payload = {"event": "test", "data": {}}

        event = WebhookEvent(payload)

        assert event.candidacy_id is None

    def test_contact_id_property(self):
        """Test contact_id property"""
        payload = {"event": "contact.created", "data": {"contact_id": "cont_789"}}

        event = WebhookEvent(payload)

        assert event.contact_id == "cont_789"

    def test_evaluation_id_property(self):
        """Test evaluation_id property"""
        payload = {
            "event": "evaluation.submitted",
            "data": {"evaluation_id": "eval_111"},
        }

        event = WebhookEvent(payload)

        assert event.evaluation_id == "eval_111"

    def test_file_id_property(self):
        """Test file_id property"""
        payload = {"event": "file.uploaded", "data": {"file_id": "file_222"}}

        event = WebhookEvent(payload)

        assert event.file_id == "file_222"

    def test_repr(self):
        """Test string representation"""
        payload = {"event": "candidacy.created", "event_id": "evt_123"}

        event = WebhookEvent(payload)

        repr_str = repr(event)

        assert "WebhookEvent" in repr_str
        assert "candidacy.created" in repr_str
        assert "evt_123" in repr_str


class TestWebhookHandler:
    """Test WebhookHandler (sync)"""

    @pytest.fixture
    def handler(self):
        """Create handler instance"""
        return WebhookHandler()

    @pytest.fixture
    def sample_payload(self):
        """Sample webhook payload"""
        return {
            "event": "candidacy.created",
            "event_id": "evt_123",
            "timestamp": "2026-01-28T10:00:00Z",
            "data": {"candidacy_id": "cand_456"},
        }

    def test_initialization(self):
        """Test handler initialization"""
        handler = WebhookHandler()

        assert handler.handlers == {}
        assert handler.default_handler is None

    def test_register_handler(self, handler):
        """Test registering a handler"""
        mock_func = Mock()

        handler.register("candidacy.created", mock_func)

        assert "candidacy.created" in handler.handlers
        assert mock_func in handler.handlers["candidacy.created"]

    def test_register_multiple_handlers_for_same_event(self, handler):
        """Test registering multiple handlers for same event"""
        mock_func1 = Mock()
        mock_func2 = Mock()

        handler.register("candidacy.created", mock_func1)
        handler.register("candidacy.created", mock_func2)

        handlers = handler.handlers["candidacy.created"]
        assert len(handlers) == 2
        assert mock_func1 in handlers
        assert mock_func2 in handlers

    def test_on_decorator(self, handler):
        """Test @handler.on decorator"""

        @handler.on("candidacy.created")
        def my_handler(event):
            pass

        assert "candidacy.created" in handler.handlers
        assert my_handler in handler.handlers["candidacy.created"]

    def test_on_decorator_preserves_function(self, handler):
        """Test decorator preserves original function"""

        @handler.on("candidacy.created")
        def my_handler(event):
            """Docstring"""
            return "result"

        # Function should work normally
        event = WebhookEvent({"event": "test"})
        result = my_handler(event)

        assert result == "result"
        assert my_handler.__doc__ == "Docstring"

    def test_register_default_handler(self, handler):
        """Test registering default handler"""
        mock_func = Mock()

        handler.register_default(mock_func)

        assert handler.default_handler == mock_func

    def test_handle_event_with_registered_handler(self, handler, sample_payload):
        """Test handling event calls registered handler"""
        mock_func = Mock()
        handler.register("candidacy.created", mock_func)

        handler.handle(sample_payload)

        # Handler should be called with WebhookEvent
        assert mock_func.called
        event = mock_func.call_args[0][0]
        assert isinstance(event, WebhookEvent)
        assert event.event_type == "candidacy.created"
        assert event.candidacy_id == "cand_456"

    def test_handle_event_with_multiple_handlers(self, handler, sample_payload):
        """Test all registered handlers are called"""
        mock_func1 = Mock()
        mock_func2 = Mock()

        handler.register("candidacy.created", mock_func1)
        handler.register("candidacy.created", mock_func2)

        handler.handle(sample_payload)

        # Both handlers should be called
        assert mock_func1.called
        assert mock_func2.called

    def test_handle_event_with_no_handler_uses_default(self, handler):
        """Test unhandled events use default handler"""
        mock_default = Mock()
        handler.register_default(mock_default)

        payload = {"event": "unknown.event", "event_id": "evt_999"}

        handler.handle(payload)

        # Default handler should be called
        assert mock_default.called

    def test_handle_event_with_no_handler_and_no_default(self, handler, sample_payload):
        """Test unhandled events with no default handler logs warning"""
        # Don't register any handlers

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            handler.handle(sample_payload)

            # Should log warning
            assert mock_logger.warning.called

    def test_handle_event_handler_exception(self, handler, sample_payload):
        """Test exception in handler is caught and logged"""

        def failing_handler(event):
            raise ValueError("Handler error")

        handler.register("candidacy.created", failing_handler)

        # Should not raise, should log error
        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            handler.handle(sample_payload)

            # Should log error
            assert mock_logger.error.called

    def test_handle_event_default_handler_exception(self, handler):
        """Test exception in default handler is caught and logged"""

        def failing_handler(event):
            raise ValueError("Default handler error")

        handler.register_default(failing_handler)

        payload = {"event": "unknown.event"}

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            handler.handle(payload)

            # Should log error
            assert mock_logger.error.called

    def test_handle_raw_bytes(self, handler):
        """Test handling raw bytes payload"""
        mock_func = Mock()
        handler.register("candidacy.created", mock_func)

        payload = b'{"event": "candidacy.created", "event_id": "evt_123"}'

        handler.handle_raw(payload)

        # Handler should be called
        assert mock_func.called

    def test_handle_raw_invalid_json(self, handler):
        """Test handling invalid JSON logs error"""
        payload = b"invalid json"

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            handler.handle_raw(payload)

            # Should log error
            assert mock_logger.error.called

    def test_multiple_event_types(self, handler):
        """Test handling different event types"""
        mock_created = Mock()
        mock_updated = Mock()

        handler.register("candidacy.created", mock_created)
        handler.register("candidacy.updated", mock_updated)

        # Handle created event
        handler.handle({"event": "candidacy.created", "event_id": "evt_1"})
        assert mock_created.called
        assert not mock_updated.called

        mock_created.reset_mock()

        # Handle updated event
        handler.handle({"event": "candidacy.updated", "event_id": "evt_2"})
        assert not mock_created.called
        assert mock_updated.called


class TestAsyncWebhookHandler:
    """Test AsyncWebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Create async handler instance"""
        return AsyncWebhookHandler()

    @pytest.fixture
    def sample_payload(self):
        """Sample webhook payload"""
        return {
            "event": "candidacy.created",
            "event_id": "evt_123",
            "data": {"candidacy_id": "cand_456"},
        }

    def test_initialization(self):
        """Test async handler initialization"""
        handler = AsyncWebhookHandler()

        assert handler.handlers == {}
        assert handler.default_handler is None

    def test_register_handler(self, handler):
        """Test registering async handler"""

        async def async_func(event):
            pass

        handler.register("candidacy.created", async_func)

        assert "candidacy.created" in handler.handlers
        assert async_func in handler.handlers["candidacy.created"]

    def test_on_decorator(self, handler):
        """Test @handler.on decorator for async"""

        @handler.on("candidacy.created")
        async def my_async_handler(event):
            pass

        assert "candidacy.created" in handler.handlers
        assert my_async_handler in handler.handlers["candidacy.created"]

    def test_register_default_handler(self, handler):
        """Test registering default async handler"""

        async def async_default(event):
            pass

        handler.register_default(async_default)

        assert handler.default_handler == async_default

    @pytest.mark.asyncio
    async def test_handle_event_with_registered_handler(self, handler, sample_payload):
        """Test async handling calls registered handler"""
        called = []

        async def async_func(event):
            called.append(event)

        handler.register("candidacy.created", async_func)

        await handler.handle(sample_payload)

        # Handler should be called
        assert len(called) == 1
        assert isinstance(called[0], WebhookEvent)
        assert called[0].event_type == "candidacy.created"

    @pytest.mark.asyncio
    async def test_handle_event_with_multiple_handlers(self, handler, sample_payload):
        """Test all async handlers are called"""
        called1 = []
        called2 = []

        async def async_func1(event):
            called1.append(event)

        async def async_func2(event):
            called2.append(event)

        handler.register("candidacy.created", async_func1)
        handler.register("candidacy.created", async_func2)

        await handler.handle(sample_payload)

        # Both handlers should be called
        assert len(called1) == 1
        assert len(called2) == 1

    @pytest.mark.asyncio
    async def test_handle_event_with_default_handler(self, handler):
        """Test async default handler is called for unknown events"""
        called = []

        async def async_default(event):
            called.append(event)

        handler.register_default(async_default)

        payload = {"event": "unknown.event", "event_id": "evt_999"}

        await handler.handle(payload)

        # Default handler should be called
        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_handle_event_handler_exception(self, handler, sample_payload):
        """Test async handler exception is caught"""

        async def failing_handler(event):
            raise ValueError("Async handler error")

        handler.register("candidacy.created", failing_handler)

        # Should not raise, should log error
        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            await handler.handle(sample_payload)

            # Should log error
            assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_handle_event_default_handler_exception(self, handler):
        """Test async default handler exception is caught"""

        async def failing_handler(event):
            raise ValueError("Default handler error")

        handler.register_default(failing_handler)

        payload = {"event": "unknown.event"}

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            await handler.handle(payload)

            # Should log error
            assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_handle_raw_bytes(self, handler):
        """Test async handling of raw bytes"""
        called = []

        async def async_func(event):
            called.append(event)

        handler.register("candidacy.created", async_func)

        payload = b'{"event": "candidacy.created", "event_id": "evt_123"}'

        await handler.handle_raw(payload)

        # Handler should be called
        assert len(called) == 1

    @pytest.mark.asyncio
    async def test_handle_raw_invalid_json(self, handler):
        """Test async handling of invalid JSON logs error"""
        payload = b"invalid json"

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            await handler.handle_raw(payload)

            # Should log error
            assert mock_logger.error.called


class TestCommonHandlers:
    """Test common event handlers"""

    def test_log_event_handler(self):
        """Test log_event_handler logs event"""
        event = WebhookEvent(
            {"event": "candidacy.created", "data": {"candidacy_id": "cand_123"}}
        )

        with patch("src.core.herp.webhooks.handlers.logger") as mock_logger:
            log_event_handler(event)

            # Should log info
            assert mock_logger.info.called
            call_args = str(mock_logger.info.call_args)
            assert "candidacy.created" in call_args

    def test_print_event_handler(self, capsys):
        """Test print_event_handler prints event"""
        event = WebhookEvent(
            {"event": "candidacy.created", "data": {"candidacy_id": "cand_123"}}
        )

        print_event_handler(event)

        # Capture stdout
        captured = capsys.readouterr()

        assert "candidacy.created" in captured.out
        assert "cand_123" in captured.out


class TestWebhookHandlerEdgeCases:
    """Test edge cases for webhook handlers"""

    def test_handler_receives_correct_event_data(self):
        """Test handler receives all event data"""
        handler = WebhookHandler()
        received_events = []

        def capture_handler(event):
            received_events.append(
                {
                    "type": event.event_type,
                    "id": event.event_id,
                    "timestamp": event.timestamp,
                    "candidacy_id": event.candidacy_id,
                }
            )

        handler.register("candidacy.created", capture_handler)

        payload = {
            "event": "candidacy.created",
            "event_id": "evt_123",
            "timestamp": "2026-01-28T10:00:00Z",
            "data": {"candidacy_id": "cand_456", "name": "John Doe"},
        }

        handler.handle(payload)

        assert len(received_events) == 1
        assert received_events[0]["type"] == "candidacy.created"
        assert received_events[0]["id"] == "evt_123"
        assert received_events[0]["timestamp"] == "2026-01-28T10:00:00Z"
        assert received_events[0]["candidacy_id"] == "cand_456"

    def test_handler_order_preserved(self):
        """Test handlers are called in registration order"""
        handler = WebhookHandler()
        call_order = []

        def handler1(event):
            call_order.append(1)

        def handler2(event):
            call_order.append(2)

        def handler3(event):
            call_order.append(3)

        handler.register("test.event", handler1)
        handler.register("test.event", handler2)
        handler.register("test.event", handler3)

        handler.handle({"event": "test.event"})

        assert call_order == [1, 2, 3]

    def test_empty_payload(self):
        """Test handling empty payload"""
        handler = WebhookHandler()
        mock_default = Mock()
        handler.register_default(mock_default)

        handler.handle({})

        # Should call default handler with event that has None type
        assert mock_default.called
        event = mock_default.call_args[0][0]
        assert event.event_type is None

    def test_unicode_in_event_data(self):
        """Test handling unicode characters in event data"""
        handler = WebhookHandler()
        received = []

        def capture(event):
            received.append(event.data)

        handler.register("test.event", capture)

        payload = {"event": "test.event", "data": {"name": "José García ✓"}}

        handler.handle(payload)

        assert len(received) == 1
        assert received[0]["name"] == "José García ✓"
