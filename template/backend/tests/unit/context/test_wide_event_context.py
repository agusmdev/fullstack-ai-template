"""Tests for wide event context module."""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.core.logging.context import (
    WideEventContext,
    add_entity_to_context,
    clear_wide_event_context,
    ensure_wide_event_context,
    get_wide_event_context,
    set_wide_event_context,
)


class TestWideEventContext:
    """Tests for WideEventContext dataclass."""

    def test_default_values(self):
        """Test default values."""
        ctx = WideEventContext(request_id="req-123")

        assert ctx.request_id == "req-123"
        assert ctx.trace_id is None
        assert ctx.user_id is None
        assert ctx.method == ""
        assert ctx.path == ""
        assert ctx.status_code == 0
        assert ctx.error is False
        assert ctx.entity_ids == []
        assert ctx.custom == {}

    def test_set_error(self):
        """Test set_error method."""
        ctx = WideEventContext(request_id="req-123")

        ctx.set_error("ValueError", "Invalid input")

        assert ctx.error is True
        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "Invalid input"

    def test_finalize(self):
        """Test finalize method."""
        ctx = WideEventContext(request_id="req-123")

        ctx.finalize(status_code=200, duration_ms=150.5)

        assert ctx.status_code == 200
        assert ctx.duration_ms == 150.5


class TestWideEventContextToDict:
    """Tests for WideEventContext.to_dict method."""

    def test_basic_to_dict(self):
        """Test to_dict with basic fields."""
        ctx = WideEventContext(request_id="req-123")
        ctx.method = "GET"
        ctx.path = "/api/items"
        ctx.status_code = 200
        ctx.duration_ms = 50.0

        result = ctx.to_dict()

        assert result["request_id"] == "req-123"
        assert result["method"] == "GET"
        assert result["path"] == "/api/items"
        assert result["status_code"] == 200
        assert result["duration_ms"] == 50.0
        assert "timestamp" in result

    def test_to_dict_includes_optional_fields_when_set(self):
        """Test to_dict includes optional fields when set."""
        ctx = WideEventContext(request_id="req-123")
        ctx.user_id = "user-456"
        ctx.trace_id = "trace-789"
        ctx.entity_type = "Item"
        ctx.entity_id = "item-001"

        result = ctx.to_dict()

        assert result["user_id"] == "user-456"
        assert result["trace_id"] == "trace-789"
        assert result["entity_type"] == "Item"
        assert result["entity_id"] == "item-001"

    def test_to_dict_excludes_none_values(self):
        """Test to_dict excludes None values."""
        ctx = WideEventContext(request_id="req-123")

        result = ctx.to_dict()

        assert "user_id" not in result
        assert "trace_id" not in result
        assert "entity_type" not in result

    def test_to_dict_includes_error_context(self):
        """Test to_dict includes error context when set."""
        ctx = WideEventContext(request_id="req-123")
        ctx.set_error("RuntimeError", "Something went wrong")

        result = ctx.to_dict()

        assert result["error"] is True
        assert result["error_type"] == "RuntimeError"
        assert result["error_message"] == "Something went wrong"

    def test_to_dict_rounds_duration(self):
        """Test to_dict rounds duration to 2 decimal places."""
        ctx = WideEventContext(request_id="req-123")
        ctx.duration_ms = 123.456789

        result = ctx.to_dict()

        assert result["duration_ms"] == 123.46

    def test_to_dict_sanitizes_custom(self):
        """Test to_dict sanitizes custom field."""
        ctx = WideEventContext(request_id="req-123")
        ctx.custom = {"password": "secret", "name": "test"}

        result = ctx.to_dict()

        assert result["custom"]["password"] == "[REDACTED]"
        assert result["custom"]["name"] == "test"

    def test_to_dict_includes_entity_ids_when_set(self):
        """Test to_dict includes entity_ids when set."""
        ctx = WideEventContext(request_id="req-123")
        ctx.entity_ids = ["id1", "id2", "id3"]

        result = ctx.to_dict()

        assert result["entity_ids"] == ["id1", "id2", "id3"]

    def test_to_dict_includes_path_template_when_different(self):
        """Test to_dict includes path_template when different from path."""
        ctx = WideEventContext(request_id="req-123")
        ctx.path = "/items/123"
        ctx.path_template = "/items/{item_id}"

        result = ctx.to_dict()

        assert result["path_template"] == "/items/{item_id}"


class TestContextVarFunctions:
    """Tests for context variable management functions."""

    def test_set_and_get_wide_event_context(self):
        """Test setting and getting wide event context."""
        ctx = WideEventContext(request_id="test-req")

        set_wide_event_context(ctx)
        result = get_wide_event_context()

        assert result is ctx
        clear_wide_event_context()

    def test_clear_wide_event_context(self):
        """Test clearing wide event context."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)

        clear_wide_event_context()

        assert get_wide_event_context() is None

    def test_ensure_wide_event_context_returns_none_when_not_set(self):
        """Test ensure returns None when context not set."""
        clear_wide_event_context()

        result = ensure_wide_event_context()

        assert result is None

    def test_ensure_wide_event_context_returns_context_when_set(self):
        """Test ensure returns context when set."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)

        result = ensure_wide_event_context()

        assert result is ctx
        clear_wide_event_context()


class TestAddEntityToContext:
    """Tests for add_entity_to_context function."""

    def test_adds_single_entity(self):
        """Test adding a single entity."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)

        add_entity_to_context("Item", "item-123")

        assert ctx.entity_type == "Item"
        assert ctx.entity_id == "item-123"
        clear_wide_event_context()

    def test_adds_uuid_entity(self):
        """Test adding entity with UUID."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)
        entity_id = uuid.uuid4()

        add_entity_to_context("User", entity_id)

        assert ctx.entity_type == "User"
        assert ctx.entity_id == str(entity_id)
        clear_wide_event_context()

    def test_adds_multiple_entities(self):
        """Test adding multiple entities moves to entity_ids list."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)

        add_entity_to_context("Item", "item-1")
        add_entity_to_context("Item", "item-2")

        assert ctx.entity_type == "Item"
        assert ctx.entity_id is None  # Moved to list
        assert "item-1" in ctx.entity_ids
        assert "item-2" in ctx.entity_ids
        clear_wide_event_context()

    def test_does_nothing_when_no_context(self):
        """Test does nothing when context not set."""
        clear_wide_event_context()

        # Should not raise
        add_entity_to_context("Item", "item-123")

    def test_avoids_duplicate_entity_ids(self):
        """Test doesn't add duplicate entity IDs."""
        ctx = WideEventContext(request_id="test-req")
        set_wide_event_context(ctx)

        add_entity_to_context("Item", "item-1")
        add_entity_to_context("Item", "item-2")
        add_entity_to_context("Item", "item-1")  # Duplicate

        assert ctx.entity_ids.count("item-1") == 1
        clear_wide_event_context()
