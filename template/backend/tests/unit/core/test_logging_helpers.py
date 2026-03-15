"""Tests for logging helper functions."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.core.logging.context import (
    WideEventContext,
    clear_wide_event_context,
    set_wide_event_context,
)
from app.core.logging.helpers import (
    log_action,
    log_custom,
    log_entities,
    log_entity,
    log_user,
)


@pytest.fixture(autouse=True)
def clear_context():
    """Clear context before and after each test."""
    clear_wide_event_context()
    yield
    clear_wide_event_context()


@pytest.fixture
def ctx():
    """Set up a WideEventContext for tests."""
    context = WideEventContext(request_id="req-test")
    set_wide_event_context(context)
    return context


class TestLogEntity:
    """Tests for log_entity helper."""

    def test_adds_entity_to_context(self, ctx):
        log_entity("item", "item-123")
        assert ctx.entity_type == "item"
        assert ctx.entity_id == "item-123"

    def test_accepts_uuid(self, ctx):
        entity_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        log_entity("user", entity_id)
        assert ctx.entity_id == str(entity_id)

    def test_does_nothing_without_context(self):
        # Should not raise when no context is set
        log_entity("item", "id-123")


class TestLogEntities:
    """Tests for log_entities helper."""

    def test_adds_multiple_entities(self, ctx):
        log_entities("item", ["id-001", "id-002"])
        assert ctx.entity_type == "item"
        assert "id-001" in ctx.entity_ids or ctx.entity_id == "id-001"

    def test_empty_list_does_nothing_harmful(self, ctx):
        log_entities("item", [])
        # Should not change entity state meaningfully
        assert ctx.entity_type is None or ctx.entity_ids == []


class TestLogAction:
    """Tests for log_action helper."""

    def test_sets_action_in_context(self, ctx):
        log_action("create")
        assert ctx.action == "create"

    def test_overwrites_previous_action(self, ctx):
        log_action("create")
        log_action("update")
        assert ctx.action == "update"

    def test_does_nothing_without_context(self):
        # Should not raise when no context is set
        log_action("create")


class TestLogCustom:
    """Tests for log_custom helper."""

    def test_adds_custom_fields(self, ctx):
        log_custom(order_total=99.99, items_count=3)
        assert ctx.custom["order_total"] == 99.99
        assert ctx.custom["items_count"] == 3

    def test_merges_with_existing_custom(self, ctx):
        ctx.custom["existing"] = "value"
        log_custom(new_field="new_value")
        assert ctx.custom["existing"] == "value"
        assert ctx.custom["new_field"] == "new_value"

    def test_does_nothing_without_context(self):
        # Should not raise when no context is set
        log_custom(key="value")


class TestLogUser:
    """Tests for log_user helper."""

    def test_sets_user_id(self, ctx):
        log_user("user-123")
        assert ctx.user_id == "user-123"

    def test_sets_email_when_provided(self, ctx):
        log_user("user-123", "user@example.com")
        assert ctx.user_id == "user-123"
        assert ctx.email == "user@example.com"

    def test_accepts_uuid_user_id(self, ctx):
        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        log_user(user_id, "user@example.com")
        assert ctx.user_id == str(user_id)

    def test_does_not_set_email_when_none(self, ctx):
        log_user("user-123")
        assert ctx.email is None

    def test_does_nothing_without_context(self):
        # Should not raise when no context is set
        log_user("user-123")
