"""Tests for core logging helper functions."""

import uuid
from unittest.mock import patch

import pytest

from app.core.logging.context import WideEventContext
from app.core.logging.helpers import (
    log_action,
    log_custom,
    log_entities,
    log_entity,
    log_user,
)


@pytest.fixture
def wide_event_ctx():
    return WideEventContext(request_id="test-req-id")


class TestLogEntity:
    def test_adds_entity_with_string_id(self, wide_event_ctx):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            with patch("app.core.logging.helpers.add_entity_to_context") as mock_add:
                log_entity("item", "abc-123")
                mock_add.assert_called_once_with("item", "abc-123")

    def test_adds_entity_with_uuid(self, wide_event_ctx):
        uid = uuid.uuid4()
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            with patch("app.core.logging.helpers.add_entity_to_context") as mock_add:
                log_entity("user", uid)
                mock_add.assert_called_once_with("user", uid)


class TestLogEntities:
    def test_adds_multiple_entities(self, wide_event_ctx):
        ids = ["id-1", "id-2", "id-3"]
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            with patch("app.core.logging.helpers.add_entity_to_context") as mock_add:
                log_entities("item", ids)
                assert mock_add.call_count == 3

    def test_empty_list_no_calls(self, wide_event_ctx):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            with patch("app.core.logging.helpers.add_entity_to_context") as mock_add:
                log_entities("item", [])
                mock_add.assert_not_called()


class TestLogAction:
    def test_sets_action(self, wide_event_ctx):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            log_action("create")
            assert wide_event_ctx.action == "create"

    def test_no_ctx_does_not_raise(self):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=None):
            log_action("create")  # should not raise


class TestLogCustom:
    def test_updates_custom_dict(self, wide_event_ctx):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            log_custom(key1="val1", key2=42)
            assert wide_event_ctx.custom["key1"] == "val1"
            assert wide_event_ctx.custom["key2"] == 42

    def test_no_ctx_does_not_raise(self):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=None):
            log_custom(key="val")  # should not raise


class TestLogUser:
    def test_sets_user_id_and_email(self, wide_event_ctx):
        uid = uuid.uuid4()
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            log_user(uid, "user@example.com")
            assert wide_event_ctx.user_id == str(uid)
            assert wide_event_ctx.email == "user@example.com"

    def test_sets_user_id_without_email(self, wide_event_ctx):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=wide_event_ctx):
            log_user("user-123")
            assert wide_event_ctx.user_id == "user-123"
            assert wide_event_ctx.email is None

    def test_no_ctx_does_not_raise(self):
        with patch("app.core.logging.helpers.get_wide_event_context", return_value=None):
            log_user("user-id")  # should not raise
