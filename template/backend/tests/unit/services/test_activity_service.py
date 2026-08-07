"""Tests for ActivityService (team-scoped reads + internal write).

Covers:
  - ``record`` persists an entry (no auth — callers pre-authorize).
  - List scoped by issue_id returns the feed; cross-team issue → 404 (no leak).
  - get_by_id enforces the issue's team membership.
  - Team membership enforced on list (404 for non-member team_id).
"""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.activity import models as activity_models
from app.modules.activity.service import ActivityService
from app.repositories.exceptions import NotFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_user_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def sample_team_id():
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def other_team_id():
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def issue_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def activity_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def issue_obj(issue_id, sample_team_id):
    return SimpleNamespace(id=issue_id, team_id=sample_team_id)


@pytest.fixture
def actor_brief(sample_user_id):
    return SimpleNamespace(id=sample_user_id, display_name="Ada", email="ada@x.com")


@pytest.fixture
def activity_obj(activity_id, issue_id, sample_user_id, actor_brief):
    return SimpleNamespace(
        id=activity_id,
        issue_id=issue_id,
        actor_id=sample_user_id,
        type=activity_models.STATUS_CHANGE,
        payload={"from": "Backlog", "to": "In Progress"},
        actor=actor_brief,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def service(mock_activity_repository, mock_issue_repository, mock_team_service):
    return ActivityService(
        repo=mock_activity_repository,
        team_service=mock_team_service,
        issue_repo=mock_issue_repository,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestActivityModel:
    def test_table_registered(self):
        from app.database.base import Base

        assert "activity" in Base.metadata.tables

    def test_model_fields(self):
        from app.modules.activity.models import Activity

        cols = {c.name for c in Activity.__table__.columns}
        assert {"id", "issue_id", "actor_id", "type", "payload"} <= cols

    def test_type_constants(self):
        assert activity_models.STATUS_CHANGE == "status_change"
        assert activity_models.ASSIGNEE_CHANGE == "assignee_change"
        assert activity_models.PRIORITY_CHANGE == "priority_change"
        assert activity_models.TITLE_RENAME == "title_rename"
        assert activity_models.LABEL_ADDED == "label_added"
        assert activity_models.LABEL_REMOVED == "label_removed"


# ---------------------------------------------------------------------------
# record (internal write)
# ---------------------------------------------------------------------------


class TestRecord:
    @pytest.mark.asyncio
    async def test_record_persists_entry(
        self, service, mock_activity_repository, issue_id, sample_user_id
    ):
        """record() persists an entry with the given fields (VAL-ACTIVITY-001)."""
        payload = {"from": "Backlog", "to": "In Progress"}
        await service.record(
            issue_id=issue_id,
            actor_id=sample_user_id,
            activity_type=activity_models.STATUS_CHANGE,
            payload=payload,
        )

        mock_activity_repository.create.assert_awaited_once()
        args, kwargs = mock_activity_repository.create.await_args
        # The entry is passed as the positional ``entity`` dict.
        assert kwargs == {}
        assert args[0] == {
            "issue_id": issue_id,
            "actor_id": sample_user_id,
            "type": activity_models.STATUS_CHANGE,
            "payload": payload,
        }

    @pytest.mark.asyncio
    async def test_record_no_team_access_check(
        self, service, mock_team_service, mock_activity_repository, issue_id,
        sample_user_id,
    ):
        """record() performs no authorization — the caller pre-authorizes."""
        await service.record(
            issue_id=issue_id,
            actor_id=sample_user_id,
            activity_type=activity_models.TITLE_RENAME,
            payload={"from": "Old", "to": "New"},
        )
        mock_team_service.require_team_access.assert_not_awaited()
        mock_activity_repository.create.assert_awaited_once()


# ---------------------------------------------------------------------------
# List (team-scoped)
# ---------------------------------------------------------------------------


class TestList:
    @pytest.mark.asyncio
    async def test_list_scoped_to_issue_returns_feed(
        self, service, mock_team_service, mock_issue_repository,
        mock_activity_repository, issue_obj, activity_obj,
        issue_id, sample_user_id, sample_team_id,
    ):
        """Listing by issue_id returns the activity feed (VAL-ACTIVITY-008)."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_issue_repository.get.return_value = issue_obj
        mock_activity_repository.get_all_paginated.return_value = SimpleNamespace(
            items=[activity_obj], total=1, page=1, size=50, pages=1
        )

        result = await service.get_all_paginated(
            Params(), user_id=sample_user_id, issue_id=issue_id
        )
        assert result.total == 1
        mock_issue_repository.get.assert_awaited_with(issue_id, raise_error=False)

    @pytest.mark.asyncio
    async def test_list_cross_team_issue_404(
        self, service, mock_team_service, issue_id, sample_user_id, other_team_id,
    ):
        """Listing a foreign-team issue's activity raises 404 (no leak)."""
        mock_team_service.get_team_ids_for_user.return_value = [other_team_id]
        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, issue_id=issue_id
            )

    @pytest.mark.asyncio
    async def test_list_team_id_404_for_non_member(
        self, service, mock_team_service, sample_user_id, other_team_id,
        sample_team_id,
    ):
        """Filtering by a non-member team_id raises 404."""
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, team_id=other_team_id
            )


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_activity_for_member(
        self, service, mock_team_service, mock_activity_repository,
        mock_issue_repository, activity_obj, issue_obj, activity_id,
        sample_user_id, sample_team_id,
    ):
        mock_team_service.get_team_ids_for_user.return_value = [sample_team_id]
        mock_activity_repository.get.return_value = activity_obj
        mock_issue_repository.get.return_value = issue_obj

        result = await service.get_by_id(activity_id, user_id=sample_user_id)
        assert result == activity_obj

    @pytest.mark.asyncio
    async def test_404_for_cross_team_activity(
        self, service, mock_team_service, mock_activity_repository,
        mock_issue_repository, activity_obj, issue_obj, activity_id,
        sample_user_id, other_team_id,
    ):
        mock_team_service.get_team_ids_for_user.return_value = [other_team_id]
        mock_activity_repository.get.return_value = activity_obj
        mock_issue_repository.get.return_value = issue_obj

        with pytest.raises(NotFoundError):
            await service.get_by_id(activity_id, user_id=sample_user_id)
