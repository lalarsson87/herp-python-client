"""
Tests for Error Context
"""

from unittest.mock import Mock

import pytest

from src.core.errors.context import (
    ErrorContext,
    OperationContext,
    create_api_error_context,
)


class TestErrorContext:
    """Test ErrorContext dataclass"""

    def test_initialization_minimal(self):
        """Test error context with minimal fields"""
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
        )

        assert context.operation == "get_candidacy"
        assert context.resource_type == "candidacy"
        assert context.resource_id is None
        assert context.params is None
        assert context.user_id is None
        assert context.metadata == {}

    def test_initialization_full(self):
        """Test error context with all fields"""
        params = {"fields": ["id", "name"], "limit": 10}
        metadata = {"source": "api", "version": "v1"}

        context = ErrorContext(
            operation="list_candidacies",
            resource_type="candidacy",
            resource_id="cand_123",
            params=params,
            user_id="user_456",
            metadata=metadata,
        )

        assert context.operation == "list_candidacies"
        assert context.resource_type == "candidacy"
        assert context.resource_id == "cand_123"
        assert context.params == params
        assert context.user_id == "user_456"
        assert context.metadata == metadata

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields"""
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
        )

        result = context.to_dict()

        assert result == {
            "operation": "get_candidacy",
            "resource_type": "candidacy",
        }

    def test_to_dict_with_resource_id(self):
        """Test to_dict includes resource_id when set"""
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
            resource_id="cand_123",
        )

        result = context.to_dict()

        assert result["resource_id"] == "cand_123"

    def test_to_dict_with_params(self):
        """Test to_dict includes params when set"""
        params = {"fields": ["id", "name"], "limit": 10}
        context = ErrorContext(
            operation="list_candidacies",
            resource_type="candidacy",
            params=params,
        )

        result = context.to_dict()

        assert result["params"] == params

    def test_to_dict_with_user_id(self):
        """Test to_dict includes user_id when set"""
        context = ErrorContext(
            operation="create_candidacy",
            resource_type="candidacy",
            user_id="user_456",
        )

        result = context.to_dict()

        assert result["user_id"] == "user_456"

    def test_to_dict_with_metadata(self):
        """Test to_dict includes metadata when set"""
        metadata = {"source": "api", "version": "v1"}
        context = ErrorContext(
            operation="update_candidacy",
            resource_type="candidacy",
            metadata=metadata,
        )

        result = context.to_dict()

        assert result["metadata"] == metadata

    def test_to_dict_complete(self):
        """Test to_dict with all fields"""
        params = {"status": "active"}
        metadata = {"source": "webhook"}

        context = ErrorContext(
            operation="filter_candidacies",
            resource_type="candidacy",
            resource_id="cand_789",
            params=params,
            user_id="user_123",
            metadata=metadata,
        )

        result = context.to_dict()

        assert result == {
            "operation": "filter_candidacies",
            "resource_type": "candidacy",
            "resource_id": "cand_789",
            "params": params,
            "user_id": "user_123",
            "metadata": metadata,
        }

    def test_str_minimal(self):
        """Test string representation with minimal fields"""
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
        )

        result = str(context)

        assert result == "get_candidacy(candidacy)"

    def test_str_with_resource_id(self):
        """Test string representation with resource_id"""
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
            resource_id="cand_123",
        )

        result = str(context)

        assert result == "get_candidacy(candidacy id=cand_123)"

    def test_str_with_params(self):
        """Test string representation with params"""
        params = {"limit": 10, "offset": 20, "status": "active"}
        context = ErrorContext(
            operation="list_candidacies",
            resource_type="candidacy",
            params=params,
        )

        result = str(context)

        # Should include first 3 params
        assert "list_candidacies(candidacy" in result
        assert "params=" in result
        assert "limit=10" in result

    def test_str_with_resource_id_and_params(self):
        """Test string representation with resource_id and params"""
        params = {"fields": ["id", "name"]}
        context = ErrorContext(
            operation="get_candidacy",
            resource_type="candidacy",
            resource_id="cand_123",
            params=params,
        )

        result = str(context)

        assert "get_candidacy(candidacy" in result
        assert "id=cand_123" in result
        assert "params=" in result


class TestOperationContext:
    """Test OperationContext context manager"""

    def test_initialization(self):
        """Test operation context initialization"""
        logger = Mock()
        ctx = OperationContext(
            operation="get_candidacy",
            resource_type="candidacy",
            resource_id="cand_123",
            logger=logger,
        )

        assert ctx.context.operation == "get_candidacy"
        assert ctx.context.resource_type == "candidacy"
        assert ctx.context.resource_id == "cand_123"
        assert ctx.logger == logger

    def test_context_manager_success(self):
        """Test context manager with successful operation"""
        logger = Mock()

        with OperationContext(
            operation="get_candidacy",
            resource_type="candidacy",
            logger=logger,
        ) as ctx:
            # Simulate successful operation
            result_id = "cand_123"
            ctx.set_result(result_id)

        # Logger should not be called on success
        logger.error.assert_not_called()

        # Context should have resource_id
        assert ctx.context.resource_id == "cand_123"

    def test_context_manager_with_exception(self):
        """Test context manager logs error on exception"""
        logger = Mock()

        with pytest.raises(ValueError):
            with OperationContext(
                operation="get_candidacy",
                resource_type="candidacy",
                resource_id="cand_123",
                logger=logger,
            ):
                raise ValueError("Test error")

        # Logger should be called with error details
        logger.error.assert_called_once()
        call_args = logger.error.call_args

        # Verify error message
        assert "Operation failed: get_candidacy" in call_args[0][0]

        # Verify extra context
        extra = call_args[1]["extra"]
        assert "context" in extra
        assert extra["context"]["operation"] == "get_candidacy"
        assert extra["context"]["resource_type"] == "candidacy"
        assert extra["error_type"] == "ValueError"
        assert extra["error"] == "Test error"

        # Verify exc_info is True
        assert call_args[1]["exc_info"] is True

    def test_context_manager_without_logger(self):
        """Test context manager without logger doesn't crash"""
        # Should not raise exception even without logger
        with pytest.raises(ValueError):
            with OperationContext(
                operation="get_candidacy",
                resource_type="candidacy",
            ):
                raise ValueError("Test error")

    def test_set_result(self):
        """Test set_result updates resource_id"""
        ctx = OperationContext(
            operation="create_candidacy",
            resource_type="candidacy",
        )

        assert ctx.context.resource_id is None

        ctx.set_result("cand_new_123")

        assert ctx.context.resource_id == "cand_new_123"

    def test_add_metadata(self):
        """Test add_metadata adds to context"""
        ctx = OperationContext(
            operation="update_candidacy",
            resource_type="candidacy",
        )

        assert ctx.context.metadata == {}

        ctx.add_metadata("source", "api")
        ctx.add_metadata("version", "v1")

        assert ctx.context.metadata == {"source": "api", "version": "v1"}

    def test_context_manager_logs_with_params(self):
        """Test context manager includes params in error log"""
        logger = Mock()
        params = {"fields": ["id", "name"], "limit": 10}

        with pytest.raises(RuntimeError):
            with OperationContext(
                operation="list_candidacies",
                resource_type="candidacy",
                params=params,
                logger=logger,
            ):
                raise RuntimeError("API error")

        # Verify params in context
        extra = logger.error.call_args[1]["extra"]
        assert extra["context"]["params"] == params

    def test_context_manager_logs_with_user_id(self):
        """Test context manager includes user_id in error log"""
        logger = Mock()

        with pytest.raises(Exception):
            with OperationContext(
                operation="delete_candidacy",
                resource_type="candidacy",
                user_id="user_456",
                logger=logger,
            ):
                raise Exception("Deletion failed")

        # Verify user_id in context
        extra = logger.error.call_args[1]["extra"]
        assert extra["context"]["user_id"] == "user_456"

    def test_context_manager_with_metadata(self):
        """Test context manager with metadata in error log"""
        logger = Mock()

        with pytest.raises(Exception):
            with OperationContext(
                operation="process_candidacy",
                resource_type="candidacy",
                logger=logger,
            ) as ctx:
                ctx.add_metadata("retry_count", 3)
                ctx.add_metadata("elapsed_time", 1.5)
                raise Exception("Processing failed")

        # Verify metadata in context
        extra = logger.error.call_args[1]["extra"]
        assert extra["context"]["metadata"]["retry_count"] == 3
        assert extra["context"]["metadata"]["elapsed_time"] == 1.5


class TestCreateApiErrorContext:
    """Test create_api_error_context factory function"""

    def test_create_minimal(self):
        """Test creating context with minimal args"""
        context = create_api_error_context("get", "candidacy")

        assert context.operation == "get_candidacy"
        assert context.resource_type == "candidacy"
        assert context.resource_id is None
        assert context.params is None
        assert context.user_id is None

    def test_create_with_resource_id(self):
        """Test creating context with resource_id"""
        context = create_api_error_context(
            "get",
            "candidacy",
            resource_id="cand_123",
        )

        assert context.operation == "get_candidacy"
        assert context.resource_id == "cand_123"

    def test_create_with_params(self):
        """Test creating context with params"""
        params = {"limit": 10, "offset": 20}
        context = create_api_error_context(
            "list",
            "candidacy",
            params=params,
        )

        assert context.operation == "list_candidacy"
        assert context.params == params

    def test_create_with_user_id(self):
        """Test creating context with user_id"""
        context = create_api_error_context(
            "create",
            "candidacy",
            user_id="user_456",
        )

        assert context.operation == "create_candidacy"
        assert context.user_id == "user_456"

    def test_create_with_metadata(self):
        """Test creating context with metadata"""
        metadata = {"source": "webhook", "event_id": "evt_123"}
        context = create_api_error_context(
            "update",
            "candidacy",
            metadata=metadata,
        )

        assert context.operation == "update_candidacy"
        assert context.metadata == metadata

    def test_create_complete(self):
        """Test creating context with all args"""
        params = {"status": "active"}
        metadata = {"retry": True}

        context = create_api_error_context(
            "update",
            "contact",
            resource_id="contact_789",
            params=params,
            user_id="user_123",
            metadata=metadata,
        )

        assert context.operation == "update_contact"
        assert context.resource_type == "contact"
        assert context.resource_id == "contact_789"
        assert context.params == params
        assert context.user_id == "user_123"
        assert context.metadata == metadata

    def test_create_different_operations(self):
        """Test creating context for different operations"""
        get_ctx = create_api_error_context("get", "requisition")
        list_ctx = create_api_error_context("list", "user")
        create_ctx = create_api_error_context("create", "contact")
        update_ctx = create_api_error_context("update", "evaluation")
        delete_ctx = create_api_error_context("delete", "file")

        assert get_ctx.operation == "get_requisition"
        assert list_ctx.operation == "list_user"
        assert create_ctx.operation == "create_contact"
        assert update_ctx.operation == "update_evaluation"
        assert delete_ctx.operation == "delete_file"


class TestErrorContextIntegration:
    """Integration tests for error context"""

    def test_context_in_logging_workflow(self):
        """Test complete workflow with logging"""
        logger = Mock()

        try:
            with OperationContext(
                operation="create_candidacy",
                resource_type="candidacy",
                params={"name": "John Doe", "email": "john@example.com"},
                user_id="user_789",
                logger=logger,
            ) as ctx:
                # Simulate API call
                ctx.add_metadata("attempt", 1)
                ctx.add_metadata("endpoint", "/v1/candidacies")

                # Simulate failure
                raise ValueError("Validation failed: email already exists")

        except ValueError:
            pass

        # Verify complete logging
        assert logger.error.called
        call_args = logger.error.call_args

        # Check message
        assert "Operation failed: create_candidacy" in call_args[0][0]

        # Check context
        extra = call_args[1]["extra"]
        context = extra["context"]
        assert context["operation"] == "create_candidacy"
        assert context["resource_type"] == "candidacy"
        assert context["params"]["name"] == "John Doe"
        assert context["user_id"] == "user_789"
        assert context["metadata"]["attempt"] == 1
        assert context["metadata"]["endpoint"] == "/v1/candidacies"

        # Check error details
        assert extra["error_type"] == "ValueError"
        assert "email already exists" in extra["error"]

    def test_context_with_successful_operation(self):
        """Test context with successful operation doesn't log"""
        logger = Mock()

        with OperationContext(
            operation="get_candidacy",
            resource_type="candidacy",
            resource_id="cand_123",
            logger=logger,
        ) as ctx:
            # Simulate successful operation
            result = {"id": "cand_123", "name": "Jane Doe"}
            ctx.add_metadata("response_time_ms", 150)

        # No error should be logged
        logger.error.assert_not_called()

        # Metadata should still be captured
        assert ctx.context.metadata["response_time_ms"] == 150

    def test_factory_function_integration(self):
        """Test factory function in complete workflow"""
        params = {"limit": 50, "offset": 0}
        context = create_api_error_context(
            "list",
            "candidacy",
            params=params,
            user_id="user_456",
            metadata={"cache": "miss"},
        )

        # Verify context can be serialized for logging
        context_dict = context.to_dict()

        assert context_dict["operation"] == "list_candidacy"
        assert context_dict["resource_type"] == "candidacy"
        assert context_dict["params"] == params
        assert context_dict["user_id"] == "user_456"
        assert context_dict["metadata"]["cache"] == "miss"

        # Verify string representation
        context_str = str(context)
        assert "list_candidacy" in context_str
        assert "candidacy" in context_str
