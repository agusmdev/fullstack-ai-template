"""Tests for HTTPExceptionMixin base class."""

import pytest

from app.exceptions import HTTPExceptionMixin


class TestHTTPExceptionMixin:
    """Tests for HTTPExceptionMixin initialization and defaults."""

    def test_default_values(self):
        """Test that defaults are applied correctly."""
        exc = HTTPExceptionMixin()
        assert exc.status_code == 500
        assert exc.detail == "Internal Server Error"

    def test_custom_status_code(self):
        """Test overriding status_code."""
        exc = HTTPExceptionMixin(status_code=404)
        assert exc.status_code == 404
        assert exc.detail == "Internal Server Error"

    def test_custom_detail(self):
        """Test overriding detail."""
        exc = HTTPExceptionMixin(detail="Custom error message")
        assert exc.status_code == 500
        assert exc.detail == "Custom error message"

    def test_custom_status_code_and_detail(self):
        """Test overriding both status_code and detail."""
        exc = HTTPExceptionMixin(status_code=400, detail="Bad request details")
        assert exc.status_code == 400
        assert exc.detail == "Bad request details"

    def test_error_code_class_attribute(self):
        """Test error_code class attribute."""
        assert HTTPExceptionMixin.error_code == "internal_server_error"

    def test_inherits_from_http_exception(self):
        """Test that it properly inherits from HTTPException."""
        exc = HTTPExceptionMixin()
        # Should be raiseable
        with pytest.raises(HTTPExceptionMixin) as exc_info:
            raise exc
        assert exc_info.value.status_code == 500


class TestCustomExceptionClass:
    """Tests for custom exceptions that inherit from HTTPExceptionMixin."""

    def test_subclass_with_custom_defaults(self):
        """Test creating a subclass with custom class-level defaults."""

        class CustomError(HTTPExceptionMixin):
            error_code = "custom_error"
            detail = "A custom error occurred"
            status_code = 422

        exc = CustomError()
        assert exc.status_code == 422
        assert exc.detail == "A custom error occurred"
        assert CustomError.error_code == "custom_error"

    def test_subclass_override_at_instantiation(self):
        """Test that instance values override class-level defaults."""

        class CustomError(HTTPExceptionMixin):
            error_code = "custom_error"
            detail = "A custom error occurred"
            status_code = 422

        exc = CustomError(status_code=500, detail="Overridden message")
        assert exc.status_code == 500
        assert exc.detail == "Overridden message"
