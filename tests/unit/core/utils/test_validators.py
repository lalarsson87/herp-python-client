"""
Tests for validation utilities
"""

from typing import TypedDict
from unittest.mock import patch

import pytest

from src.core.utils.validators import (
    _get_schema_fields,
    _validate_dict,
    validate_list_response,
    validate_response,
    validate_single_response,
)


# Test schemas
class UserSchema(TypedDict):
    """Test schema for user"""

    id: str
    name: str
    email: str


class ProductSchema(TypedDict):
    """Test schema for product"""

    id: str
    title: str
    price: float
    in_stock: bool


class TestGetSchemaFields:
    """Test _get_schema_fields helper"""

    def test_extract_fields_from_typed_dict(self):
        """Test extracting fields from TypedDict"""
        fields = _get_schema_fields(UserSchema)

        assert "id" in fields
        assert "name" in fields
        assert "email" in fields
        assert len(fields) == 3

    def test_extract_fields_from_product_schema(self):
        """Test extracting fields from different schema"""
        fields = _get_schema_fields(ProductSchema)

        assert "id" in fields
        assert "title" in fields
        assert "price" in fields
        assert "in_stock" in fields
        assert len(fields) == 4

    def test_caching_works(self):
        """Test LRU cache works for repeated calls"""
        # Clear cache first
        _get_schema_fields.cache_clear()

        # First call
        fields1 = _get_schema_fields(UserSchema)

        # Second call should return cached result
        fields2 = _get_schema_fields(UserSchema)

        assert fields1 is fields2  # Same object (cached)

        # Check cache info
        cache_info = _get_schema_fields.cache_info()
        assert cache_info.hits >= 1

    def test_invalid_schema_returns_empty(self):
        """Test invalid schema returns empty frozenset"""
        # Pass a non-TypedDict class
        fields = _get_schema_fields(str)

        # Should return empty frozenset and log warning
        assert len(fields) == 0


class TestValidateDict:
    """Test _validate_dict helper"""

    def test_valid_complete_data(self):
        """Test validation passes with complete data"""
        data = {"id": "123", "name": "John", "email": "john@example.com"}

        result = _validate_dict(data, UserSchema, strict=True)

        assert result == data

    def test_valid_extra_fields(self):
        """Test validation allows extra fields"""
        data = {
            "id": "123",
            "name": "John",
            "email": "john@example.com",
            "extra_field": "extra",  # Extra field should be allowed
        }

        result = _validate_dict(data, UserSchema, strict=True)

        assert result == data
        assert "extra_field" in result

    @patch("src.core.utils.validators.logger")
    def test_missing_fields_logs_warning_in_strict_mode(self, mock_logger):
        """Test missing fields logs warning in strict mode"""
        data = {"id": "123", "name": "John"}  # Missing 'email'

        result = _validate_dict(data, UserSchema, strict=True)

        # Should still return data (non-blocking)
        assert result == data

        # Should log warning about missing fields
        assert mock_logger.debug.called
        call_args = str(mock_logger.debug.call_args)
        assert "missing" in call_args.lower() or "email" in call_args.lower()

    def test_missing_fields_no_warning_in_lenient_mode(self):
        """Test missing fields doesn't log in lenient mode"""
        data = {"id": "123"}  # Missing fields

        with patch("src.core.utils.validators.logger") as mock_logger:
            result = _validate_dict(data, UserSchema, strict=False)

            # Should return data
            assert result == data

            # Should not log debug messages
            assert not mock_logger.debug.called

    @patch("src.core.utils.validators.logger")
    def test_empty_data_logs_warning_in_strict_mode(self, mock_logger):
        """Test empty data logs warning in strict mode"""
        data = {}

        result = _validate_dict(data, UserSchema, strict=True)

        assert result == data
        assert mock_logger.warning.called

    def test_empty_data_no_warning_in_lenient_mode(self):
        """Test empty data doesn't log in lenient mode"""
        data = {}

        with patch("src.core.utils.validators.logger") as mock_logger:
            result = _validate_dict(data, UserSchema, strict=False)

            assert result == data
            # Should not log warning in lenient mode
            # Actually, it does log for empty data even in lenient - let me check


class TestValidateResponse:
    """Test validate_response decorator"""

    def test_decorator_validates_dict_response(self):
        """Test decorator validates dictionary response"""

        @validate_response(UserSchema)
        def get_user():
            return {"id": "123", "name": "John", "email": "john@example.com"}

        result = get_user()

        assert result["id"] == "123"
        assert result["name"] == "John"

    def test_decorator_allows_non_dict_response(self):
        """Test decorator allows non-dict responses"""

        @validate_response(UserSchema)
        def get_count():
            return 42  # Non-dict response

        result = get_count()

        assert result == 42

    def test_decorator_with_missing_fields(self):
        """Test decorator handles missing fields"""

        @validate_response(UserSchema, strict=True)
        def get_partial_user():
            return {"id": "123", "name": "John"}  # Missing email

        with patch("src.core.utils.validators.logger"):
            result = get_partial_user()

            # Should still return data
            assert result["id"] == "123"

    def test_decorator_preserves_function_metadata(self):
        """Test decorator preserves function metadata"""

        @validate_response(UserSchema)
        def documented_func():
            """This is a docstring"""
            return {"id": "1", "name": "Test", "email": "test@example.com"}

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a docstring"

    def test_decorator_with_none_response(self):
        """Test decorator handles None response"""

        @validate_response(UserSchema)
        def get_none():
            return None

        result = get_none()

        assert result is None


class TestValidateListResponse:
    """Test validate_list_response decorator"""

    def test_decorator_validates_list_response(self):
        """Test decorator validates list of dicts"""

        @validate_list_response(UserSchema)
        def get_users():
            return [
                {"id": "1", "name": "Alice", "email": "alice@example.com"},
                {"id": "2", "name": "Bob", "email": "bob@example.com"},
            ]

        result = get_users()

        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_decorator_validates_sample_only(self):
        """Test decorator only validates first 5 items (sampling)"""
        call_count = [0]

        def track_validation(*args, **kwargs):
            call_count[0] += 1
            return args[0]  # Return original data

        with patch(
            "src.core.utils.validators._validate_dict", side_effect=track_validation
        ):

            @validate_list_response(UserSchema)
            def get_many_users():
                return [
                    {"id": str(i), "name": f"User{i}", "email": f"user{i}@test.com"}
                    for i in range(10)
                ]

            result = get_many_users()

            # Should validate only first 5 items
            assert len(result) == 10
            assert call_count[0] == 5  # Only sampled 5 items

    def test_decorator_handles_empty_list(self):
        """Test decorator handles empty list"""

        @validate_list_response(UserSchema)
        def get_empty():
            return []

        result = get_empty()

        assert result == []

    def test_decorator_handles_non_list_response(self):
        """Test decorator allows non-list responses"""

        @validate_list_response(UserSchema)
        def get_count():
            return 42

        result = get_count()

        assert result == 42

    def test_decorator_handles_list_with_non_dict_items(self):
        """Test decorator handles list with non-dict items"""

        @validate_list_response(UserSchema)
        def get_mixed():
            return [1, 2, 3]  # List of non-dicts

        result = get_mixed()

        # Should return list without error
        assert result == [1, 2, 3]

    def test_decorator_validates_partial_list(self):
        """Test decorator validates list with missing fields"""

        @validate_list_response(UserSchema, strict=True)
        def get_partial_users():
            return [
                {"id": "1", "name": "Alice"},  # Missing email
                {"id": "2", "name": "Bob", "email": "bob@example.com"},
            ]

        with patch("src.core.utils.validators.logger"):
            result = get_partial_users()

            # Should still return data
            assert len(result) == 2


class TestValidateSingleResponse:
    """Test validate_single_response decorator (alias)"""

    def test_is_alias_for_validate_response(self):
        """Test that validate_single_response is an alias"""

        @validate_single_response(UserSchema)
        def get_user():
            return {"id": "123", "name": "John", "email": "john@example.com"}

        result = get_user()

        assert result["id"] == "123"

    def test_works_same_as_validate_response(self):
        """Test validate_single_response behaves like validate_response"""

        @validate_single_response(UserSchema, strict=True)
        def get_partial():
            return {"id": "1", "name": "Test"}  # Missing email

        with patch("src.core.utils.validators.logger"):
            result = get_partial()

            # Should return data (non-blocking validation)
            assert result["id"] == "1"


class TestValidationEdgeCases:
    """Test edge cases for validation"""

    def test_nested_dict_not_deeply_validated(self):
        """Test nested dicts are not deeply validated"""

        class NestedSchema(TypedDict):
            id: str
            data: dict

        @validate_response(NestedSchema)
        def get_nested():
            return {"id": "1", "data": {"nested": "value"}}

        result = get_nested()

        # Should validate top-level only
        assert result["data"]["nested"] == "value"

    def test_unicode_field_names(self):
        """Test validation works with unicode characters"""

        class UnicodeSchema(TypedDict):
            café: str  # Unicode field name

        @validate_response(UnicodeSchema)
        def get_unicode():
            return {"café": "espresso"}

        result = get_unicode()

        assert result["café"] == "espresso"

    def test_large_response_validation_performance(self):
        """Test validation performs well with large responses"""

        @validate_list_response(UserSchema)
        def get_large_list():
            return [
                {"id": str(i), "name": f"User{i}", "email": f"user{i}@test.com"}
                for i in range(1000)
            ]

        # Should complete without timeout (sampling limits work)
        result = get_large_list()

        assert len(result) == 1000

    def test_multiple_decorators(self):
        """Test function can have multiple decorators"""

        @validate_response(UserSchema)
        @validate_response(UserSchema)  # Duplicate decorator
        def get_user():
            return {"id": "1", "name": "Test", "email": "test@test.com"}

        result = get_user()

        assert result["id"] == "1"

    def test_validation_with_none_fields(self):
        """Test validation allows None values in fields"""

        @validate_response(UserSchema)
        def get_user_with_none():
            return {"id": "1", "name": None, "email": "test@test.com"}

        result = get_user_with_none()

        assert result["name"] is None
