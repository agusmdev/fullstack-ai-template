"""Tests for wide event logging context."""

import uuid

from app.core.logging.context import (
    WideEventContext,
    add_entity_to_context,
    clear_wide_event_context,
    get_wide_event_context,
    set_wide_event_context,
)


class TestWideEventContext:
    """Tests for WideEventContext dataclass."""

    def test_default_values(self):
        ctx = WideEventContext(request_id="req-123")
        assert ctx.request_id == "req-123"
        assert ctx.method == ""
        assert ctx.path == ""
        assert ctx.status_code == 0
        assert ctx.duration_ms == 0.0
        assert ctx.error is False
        assert ctx.entity_ids == []
        assert ctx.custom == {}

    def test_set_error(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.set_error("ValueError", "Something went wrong")
        assert ctx.error is True
        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "Something went wrong"

    def test_finalize(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.finalize(200, 45.3)
        assert ctx.status_code == 200
        assert ctx.duration_ms == 45.3

    def test_to_dict_minimal(self):
        ctx = WideEventContext(request_id="req-abc")
        ctx.method = "GET"
        ctx.path = "/items"
        ctx.finalize(200, 10.5)

        data = ctx.to_dict()
        assert data["request_id"] == "req-abc"
        assert data["method"] == "GET"
        assert data["path"] == "/items"
        assert data["status_code"] == 200
        assert data["duration_ms"] == 10.5
        assert "timestamp" in data

    def test_to_dict_omits_none_fields(self):
        ctx = WideEventContext(request_id="req-1")
        data = ctx.to_dict()
        assert "user_id" not in data
        assert "email" not in data
        assert "trace_id" not in data
        assert "action" not in data

    def test_to_dict_includes_optional_when_set(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.user_id = "user-123"
        ctx.email = "user@example.com"
        ctx.trace_id = "trace-abc"
        ctx.action = "create"

        data = ctx.to_dict()
        assert data["user_id"] == "user-123"
        assert data["email"] == "user@example.com"
        assert data["trace_id"] == "trace-abc"
        assert data["action"] == "create"

    def test_to_dict_includes_error_when_set(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.set_error("RuntimeError", "crash")
        ctx.finalize(500, 5.0)

        data = ctx.to_dict()
        assert data["error"] is True
        assert data["error_type"] == "RuntimeError"
        assert data["error_message"] == "crash"

    def test_to_dict_rounds_duration(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.finalize(200, 45.6789)
        data = ctx.to_dict()
        assert data["duration_ms"] == 45.68

    def test_to_dict_includes_entity_type_and_id(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.entity_type = "item"
        ctx.entity_id = "ent-123"

        data = ctx.to_dict()
        assert data["entity_type"] == "item"
        assert data["entity_id"] == "ent-123"

    def test_to_dict_includes_entity_ids(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.entity_ids = ["id1", "id2"]

        data = ctx.to_dict()
        assert data["entity_ids"] == ["id1", "id2"]


class TestContextVar:
    """Tests for context variable get/set/clear functions."""

    def setup_method(self):
        clear_wide_event_context()

    def teardown_method(self):
        clear_wide_event_context()

    def test_get_returns_none_initially(self):
        assert get_wide_event_context() is None

    def test_set_and_get(self):
        ctx = WideEventContext(request_id="req-set")
        set_wide_event_context(ctx)
        result = get_wide_event_context()
        assert result is ctx

    def test_clear_sets_to_none(self):
        ctx = WideEventContext(request_id="req-clear")
        set_wide_event_context(ctx)
        clear_wide_event_context()
        assert get_wide_event_context() is None

    def test_get_returns_none_when_not_set_second_check(self):
        clear_wide_event_context()
        assert get_wide_event_context() is None


class TestAddEntityToContext:
    """Tests for add_entity_to_context function."""

    def setup_method(self):
        clear_wide_event_context()

    def teardown_method(self):
        clear_wide_event_context()

    def test_does_nothing_when_no_context(self):
        # Should not raise
        add_entity_to_context("item", "id-123")

    def test_adds_first_entity(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)

        add_entity_to_context("item", "id-001")

        assert ctx.entity_type == "item"
        assert ctx.entity_id == "id-001"
        assert ctx.entity_ids == []

    def test_adds_second_entity_moves_to_list(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)

        add_entity_to_context("item", "id-001")
        add_entity_to_context("item", "id-002")

        assert ctx.entity_type == "item"
        assert ctx.entity_id is None
        assert "id-001" in ctx.entity_ids
        assert "id-002" in ctx.entity_ids

    def test_accepts_uuid_entity_id(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)

        entity_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        add_entity_to_context("user", entity_id)

        assert ctx.entity_id == str(entity_id)

    def test_avoids_duplicate_entity_ids(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)

        add_entity_to_context("item", "id-001")
        add_entity_to_context("item", "id-002")
        add_entity_to_context("item", "id-002")  # duplicate

        assert ctx.entity_ids.count("id-002") == 1
