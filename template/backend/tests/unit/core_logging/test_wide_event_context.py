"""Tests for WideEventContext and related functions."""

import uuid

import pytest

from app.core.logging.context import (
    WideEventContext,
    add_entity_to_context,
    clear_wide_event_context,
    get_wide_event_context,
    set_wide_event_context,
)


@pytest.fixture(autouse=True)
def clean_context():
    clear_wide_event_context()
    yield
    clear_wide_event_context()


class TestWideEventContextCreation:
    def test_minimal_creation(self):
        ctx = WideEventContext(request_id="req-123")
        assert ctx.request_id == "req-123"
        assert ctx.user_id is None
        assert ctx.action is None
        assert ctx.custom == {}
        assert ctx.entity_ids == []

    def test_to_dict_required_fields(self):
        ctx = WideEventContext(request_id="req-1", method="GET", path="/api/test")
        data = ctx.to_dict()
        assert data["request_id"] == "req-1"
        assert data["method"] == "GET"
        assert data["path"] == "/api/test"
        assert "timestamp" in data

    def test_to_dict_omits_none_fields(self):
        ctx = WideEventContext(request_id="req-1")
        data = ctx.to_dict()
        assert "user_id" not in data
        assert "email" not in data
        assert "trace_id" not in data

    def test_to_dict_includes_optional_when_set(self):
        ctx = WideEventContext(request_id="req-1", user_id="u-1", email="test@example.com")
        data = ctx.to_dict()
        assert data["user_id"] == "u-1"
        assert data["email"] == "test@example.com"


class TestWideEventContextSetError:
    def test_set_error(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.set_error("ValueError", "invalid input")
        assert ctx.error is True
        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "invalid input"

    def test_to_dict_includes_error(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.set_error("RuntimeError", "something broke")
        data = ctx.to_dict()
        assert data["error"] is True
        assert data["error_type"] == "RuntimeError"
        assert data["error_message"] == "something broke"


class TestWideEventContextFinalize:
    def test_finalize_sets_status_and_duration(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.finalize(status_code=200, duration_ms=42.5)
        assert ctx.status_code == 200
        assert ctx.duration_ms == 42.5

    def test_to_dict_rounds_duration(self):
        ctx = WideEventContext(request_id="req-1")
        ctx.finalize(200, 12.3456789)
        data = ctx.to_dict()
        assert data["duration_ms"] == 12.35


class TestContextVarFunctions:
    def test_get_returns_none_when_not_set(self):
        assert get_wide_event_context() is None

    def test_set_and_get(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)
        assert get_wide_event_context() is ctx

    def test_clear_removes_context(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)
        clear_wide_event_context()
        assert get_wide_event_context() is None


class TestAddEntityToContext:
    def test_first_entity_sets_entity_id(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)
        add_entity_to_context("item", "item-1")
        assert ctx.entity_id == "item-1"
        assert ctx.entity_type == "item"

    def test_second_entity_moves_to_list(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)
        add_entity_to_context("item", "item-1")
        add_entity_to_context("item", "item-2")
        assert ctx.entity_id is None
        assert "item-1" in ctx.entity_ids
        assert "item-2" in ctx.entity_ids

    def test_uuid_entity_id_converted_to_string(self):
        ctx = WideEventContext(request_id="req-1")
        set_wide_event_context(ctx)
        uid = uuid.uuid4()
        add_entity_to_context("user", uid)
        assert ctx.entity_id == str(uid)

    def test_no_context_does_not_raise(self):
        add_entity_to_context("item", "id-1")  # no context set, should not raise
