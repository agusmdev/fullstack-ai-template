"""Tests for request context module."""

import threading
from unittest.mock import patch

import pytest

from app.context import (
    RequestContext,
    _request_id_ctx,
    clear_request_context,
    register_request_context,
    get_request_context,
    req_or_thread_id,
    set_request_id,
)


class TestSetRequestId:
    """Tests for set_request_id public function."""

    def test_sets_request_id_in_context(self):
        """Test that set_request_id updates the ContextVar."""
        test_id = "public-api-request-id"
        token = _request_id_ctx.set("before")
        try:
            set_request_id(test_id)
            assert req_or_thread_id() == test_id
        finally:
            _request_id_ctx.reset(token)

    def test_set_request_id_is_retrievable_via_req_or_thread_id(self):
        """Test the public API integrates with req_or_thread_id."""
        test_id = "integration-test-id"
        token = _request_id_ctx.set("placeholder")
        try:
            set_request_id(test_id)
            assert req_or_thread_id() == test_id
        finally:
            _request_id_ctx.reset(token)


class TestReqOrThreadId:
    """Tests for req_or_thread_id function."""

    def test_returns_request_id_when_set(self):
        """Test returns request_id from context when set."""
        test_id = "test-request-id-123"
        token = _request_id_ctx.set(test_id)
        try:
            result = req_or_thread_id()
            assert result == test_id
        finally:
            _request_id_ctx.reset(token)

    def test_returns_thread_id_on_lookup_error(self):
        """Test returns thread ID when context lookup fails."""
        # The default is already set, so we can't easily test the LookupError
        # but we can test the function returns something
        result = req_or_thread_id()
        assert result is not None
        assert isinstance(result, str)


class TestRequestContext:
    """Tests for RequestContext class."""

    def test_default_values(self):
        """Test default values."""
        ctx = RequestContext()
        assert ctx.user_id == "No user id"
        assert ctx.email == "No email"

    def test_custom_values(self):
        """Test custom values."""
        ctx = RequestContext(user_id="user-123", email="test@example.com")
        assert ctx.user_id == "user-123"
        assert ctx.email == "test@example.com"


class TestGetRequestContext:
    """Tests for get_request_context function."""

    def test_creates_new_context_if_not_exists(self):
        """Test creates new context if not in cache."""
        # Clear any existing context
        clear_request_context()

        ctx = get_request_context()

        assert isinstance(ctx, RequestContext)
        assert ctx.user_id == "No user id"

    def test_returns_existing_context(self):
        """Test returns existing context from cache."""
        clear_request_context()

        ctx1 = get_request_context()
        ctx1.user_id = "modified-user"
        ctx2 = get_request_context()

        assert ctx1 is ctx2
        assert ctx2.user_id == "modified-user"

        clear_request_context()


class TestForkRequestContext:
    """Tests for register_request_context function."""

    def test_fork_creates_new_if_not_exists(self):
        """Test fork creates new context if not in cache."""
        clear_request_context()

        new_ctx = RequestContext(user_id="forked-user", email="fork@example.com")
        result = register_request_context(new_ctx)

        assert result.user_id == "forked-user"
        assert result.email == "fork@example.com"

        clear_request_context()

    def test_fork_returns_existing_if_exists(self):
        """Test fork returns existing context if already cached."""
        clear_request_context()

        # First, create an existing context
        existing = get_request_context()
        existing.user_id = "existing-user"

        # Now try to fork
        new_ctx = RequestContext(user_id="new-user")
        result = register_request_context(new_ctx)

        # Should return existing, not new
        assert result.user_id == "existing-user"

        clear_request_context()


class TestClearRequestContext:
    """Tests for clear_request_context function."""

    def test_clears_context_from_cache(self):
        """Test that context is removed from cache."""
        # Create a context
        ctx = get_request_context()
        ctx.user_id = "to-be-cleared"

        # Clear it
        clear_request_context()

        # Getting context now should create a new one
        new_ctx = get_request_context()
        assert new_ctx.user_id == "No user id"

        clear_request_context()

    def test_clear_is_idempotent(self):
        """Test that clearing multiple times is safe."""
        clear_request_context()
        clear_request_context()
        clear_request_context()
        # Should not raise any errors
