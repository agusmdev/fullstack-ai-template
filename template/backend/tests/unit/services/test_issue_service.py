"""Tests for IssueService (team-scoped, auto-identifier, labels sub-resource).

Covers:
  - Team scoping on list (user teams only, 404 for non-member team_id).
  - Auto-identifier generation (allocate_identifier called on create).
  - Default status resolution (falls back to team's first workflow state).
  - Creator_id set to authenticated user.
  - Label attach on create + add/remove label sub-resource.
  - Ownership enforcement (member role required for writes).
  - NotFoundError for cross-team issue access.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi_pagination import Params

from app.modules.issues.models import Issue
from app.modules.issues.schemas import IssueCreate, IssueUpdate
from app.modules.issues.service import IssueService
from app.modules.teams.models import TeamRole
from app.repositories.exceptions import ForbiddenError, NotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
def status_id():
    return uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
def label_id():
    return uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
def issue_id():
    return uuid.UUID("66666666-6666-6666-6666-666666666666")


@pytest.fixture
def workflow_state_obj(status_id, sample_team_id):
    return SimpleNamespace(
        id=status_id,
        team_id=sample_team_id,
        name="Backlog",
        type="backlog",
        position=0.0,
        color="#bec2c8",
    )


@pytest.fixture
def label_obj(label_id, sample_team_id):
    return SimpleNamespace(
        id=label_id,
        team_id=sample_team_id,
        name="Bug",
        color="#f00",
    )


@pytest.fixture
def membership_obj(sample_user_id, sample_team_id):
    return SimpleNamespace(
        id=uuid.UUID("77777777-0000-0000-0000-000000000000"),
        user_id=sample_user_id,
        team_id=sample_team_id,
        role=TeamRole.member,
    )


@pytest.fixture
def issue_obj(issue_id, sample_team_id, status_id, sample_user_id):
    return SimpleNamespace(
        id=issue_id,
        team_id=sample_team_id,
        identifier="ENG-1",
        title="Test issue",
        description=None,
        status_id=status_id,
        priority=4,
        assignee_id=None,
        creator_id=sample_user_id,
        project_id=None,
        cycle_id=None,
        parent_id=None,
        sort_order=0.0,
        estimate=None,
        due_date=None,
        labels=[],
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def service(
    mock_issue_repository,
    mock_team_service,
    mock_workflow_state_repository,
    mock_label_repository,
    workflow_state_obj,
    label_obj,
    membership_obj,
):
    # Default same-team lookups so the cross-team validation helpers pass for
    # tests that don't exercise the rejection paths. Individual tests override
    # these to assert the foreign-team/non-member rejection.
    mock_workflow_state_repository.get = AsyncMock(return_value=workflow_state_obj)
    mock_label_repository.get = AsyncMock(return_value=label_obj)
    mock_team_service.get_membership = AsyncMock(return_value=membership_obj)
    return IssueService(
        repo=mock_issue_repository,
        team_service=mock_team_service,
        workflow_state_repo=mock_workflow_state_repository,
        label_repo=mock_label_repository,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestIssueModel:
    def test_issue_table_registered(self):
        from app.database.base import Base

        assert "issue" in Base.metadata.tables

    def test_issue_model_fields(self):
        cols = {c.name for c in Issue.__table__.columns}
        assert {
            "id",
            "team_id",
            "identifier",
            "title",
            "description",
            "status_id",
            "priority",
            "assignee_id",
            "creator_id",
            "project_id",
            "cycle_id",
            "parent_id",
            "sort_order",
            "estimate",
            "due_date",
            "created_at",
            "updated_at",
        } <= cols

    def test_issue_label_fk_now_wired(self):
        """After m1-issue-backend, issue_label.issue_id has a FK to issue.id."""
        from app.modules.labels.models import issue_label

        fk_targets = {
            fk.target_fullname
            for c in issue_label.columns
            for fk in c.foreign_keys
        }
        assert "issue.id" in fk_targets
        assert "label.id" in fk_targets


# ---------------------------------------------------------------------------
# get_all_paginated
# ---------------------------------------------------------------------------

class TestGetAllPaginated:
    async def test_scopes_to_user_teams(
        self,
        service,
        mock_issue_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[issue_obj], total=1, page=1, size=50, pages=1
            )
        )

        result = await service.get_all_paginated(Params(), user_id=sample_user_id)

        assert result.total == 1

    async def test_team_id_filter_404_for_non_member(
        self,
        service,
        mock_team_service,
        sample_user_id,
        other_team_id,
        sample_team_id,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )

        with pytest.raises(NotFoundError):
            await service.get_all_paginated(
                Params(), user_id=sample_user_id, team_id=other_team_id
            )

    async def test_label_id_filter_applied(
        self,
        service,
        mock_issue_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        label_id,
        issue_obj,
    ):
        """label_id should be passed through and results returned."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[issue_obj], total=1, page=1, size=50, pages=1
            )
        )

        result = await service.get_all_paginated(
            Params(), user_id=sample_user_id, label_id=label_id
        )

        assert result.total == 1
        # Verify the repo was called (label filter is in the query, not a separate call)
        mock_issue_repository.get_all_paginated.assert_awaited_once()

    async def test_unassigned_filter_accepted(
        self,
        service,
        mock_issue_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        issue_obj,
    ):
        """``unassigned`` is accepted and results returned (VAL-ISSUES-021)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get_all_paginated = AsyncMock(
            return_value=SimpleNamespace(
                items=[issue_obj], total=1, page=1, size=50, pages=1
            )
        )

        result = await service.get_all_paginated(
            Params(), user_id=sample_user_id, unassigned=True
        )

        assert result.total == 1
        # The unassigned filter is built into the base_query passed to the repo
        # as the third positional argument (QueryOptions).
        args, _kwargs = mock_issue_repository.get_all_paginated.await_args
        opts = args[2]
        assert opts is not None
        assert opts.base_query is not None


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    async def test_returns_issue_for_member(
        self,
        service,
        mock_issue_repository,
        mock_team_service,
        sample_user_id,
        sample_team_id,
        issue_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        result = await service.get_by_id(issue_id, user_id=sample_user_id)

        assert result == issue_obj

    async def test_404_for_other_team_issue(
        self,
        service,
        mock_issue_repository,
        mock_team_service,
        sample_user_id,
        other_team_id,
        issue_id,
        issue_obj,
    ):
        issue_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        with pytest.raises(NotFoundError):
            await service.get_by_id(issue_id, user_id=sample_user_id)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    async def test_requires_member_role(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        workflow_state_obj,
        sample_user_id,
        sample_team_id,
        issue_obj,
    ):
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(team_id=sample_team_id, title="Test issue"),
            user_id=sample_user_id,
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_auto_generates_identifier(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        workflow_state_obj,
        sample_user_id,
        sample_team_id,
        issue_obj,
    ):
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-42"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(team_id=sample_team_id, title="Test"),
            user_id=sample_user_id,
        )

        mock_issue_repository.allocate_identifier.assert_awaited_once_with(
            sample_team_id
        )

    async def test_defaults_status_to_first_workflow_state(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        workflow_state_obj,
        sample_user_id,
        sample_team_id,
        issue_obj,
        status_id,
    ):
        """When status_id is None, it defaults to the team's first workflow state."""
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(team_id=sample_team_id, title="Test"),
            user_id=sample_user_id,
        )

        # Verify create was called with the resolved status_id
        _args, kwargs = mock_issue_repository.create.call_args
        assert kwargs["status_id"] == status_id

    async def test_uses_provided_status_id(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        sample_user_id,
        sample_team_id,
        issue_obj,
        status_id,
    ):
        """When status_id is provided, the default resolution is skipped."""
        custom_status = uuid.UUID("77777777-7777-7777-7777-777777777777")
        mock_workflow_state_repository.get_all = AsyncMock(return_value=[])
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(
                team_id=sample_team_id, title="Test", status_id=custom_status
            ),
            user_id=sample_user_id,
        )

        # Default resolution should NOT have been called
        mock_workflow_state_repository.get_all.assert_not_awaited()
        _args, kwargs = mock_issue_repository.create.call_args
        assert kwargs["status_id"] == custom_status

    async def test_sets_creator_id(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        workflow_state_obj,
        sample_user_id,
        sample_team_id,
        issue_obj,
    ):
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(team_id=sample_team_id, title="Test"),
            user_id=sample_user_id,
        )

        _args, kwargs = mock_issue_repository.create.call_args
        assert kwargs["creator_id"] == sample_user_id

    async def test_no_team_id_raises(
        self,
        service,
        sample_user_id,
    ):
        """Creating without a team_id should raise NotFoundError."""
        from app.modules.issues.schemas import IssueCreate as IC

        # We can't create a valid IssueCreate without team_id, so test the path
        # where team_id is explicitly None on a mock entity
        from unittest.mock import MagicMock

        mock_entity = MagicMock()
        mock_entity.team_id = None

        with pytest.raises(NotFoundError):
            await service.create(mock_entity, user_id=sample_user_id)

    async def test_attaches_labels_on_create(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_workflow_state_repository,
        workflow_state_obj,
        sample_user_id,
        sample_team_id,
        label_id,
        issue_obj,
    ):
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        await service.create(
            IssueCreate(
                team_id=sample_team_id, title="Test", label_ids=[label_id]
            ),
            user_id=sample_user_id,
        )

        mock_issue_repository.attach_labels.assert_awaited_once_with(
            issue_obj.id, [label_id]
        )


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    async def test_update_member_enforced(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_issue_repository.update = AsyncMock(return_value=issue_obj)

        await service.update(
            issue_id, IssueUpdate(title="Updated"), user_id=sample_user_id
        )

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_update_404_for_non_member(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        other_team_id,
        issue_id,
        issue_obj,
    ):
        issue_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        with pytest.raises(NotFoundError):
            await service.update(
                issue_id, IssueUpdate(title="X"), user_id=sample_user_id
            )


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    async def test_delete_member_enforced(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_issue_repository.delete = AsyncMock(return_value=None)

        await service.delete(issue_id, user_id=sample_user_id)

        mock_issue_repository.delete.assert_awaited_once_with(issue_id)


# ---------------------------------------------------------------------------
# Labels sub-resource
# ---------------------------------------------------------------------------

class TestLabelsSubResource:
    async def test_add_label(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        result = await service.add_label(
            issue_id, label_id, user_id=sample_user_id
        )

        mock_issue_repository.add_label.assert_awaited_once_with(
            issue_obj.id, label_id
        )
        assert result == issue_obj

    async def test_remove_label(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        result = await service.remove_label(
            issue_id, label_id, user_id=sample_user_id
        )

        mock_issue_repository.remove_label.assert_awaited_once_with(
            issue_obj.id, label_id
        )
        assert result == issue_obj

    async def test_add_label_404_for_non_member(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        other_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        issue_obj.team_id = other_team_id
        mock_team_service.get_team_ids_for_user = AsyncMock(return_value=[])
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        with pytest.raises(NotFoundError):
            await service.add_label(
                issue_id, label_id, user_id=sample_user_id
            )


# ---------------------------------------------------------------------------
# Label role gate — guests cannot add/remove labels (VAL-CROSS-025)
# ---------------------------------------------------------------------------

class TestLabelRoleGate:
    async def test_add_label_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        """A guest-role user is forbidden from adding a label (403, not 200)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.add_label(issue_id, label_id, user_id=sample_user_id)

        # The write must never reach the repository.
        mock_issue_repository.add_label.assert_not_awaited()

    async def test_remove_label_403_for_guest(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        """A guest-role user is forbidden from removing a label (403, not 200)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_team_service.require_team_access = AsyncMock(
            side_effect=ForbiddenError(detail="guest cannot write")
        )

        with pytest.raises(ForbiddenError):
            await service.remove_label(issue_id, label_id, user_id=sample_user_id)

        mock_issue_repository.remove_label.assert_not_awaited()

    async def test_add_label_member_role_enforced(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        """add_label calls require_team_access with min_role=member."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        await service.add_label(issue_id, label_id, user_id=sample_user_id)

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_remove_label_member_role_enforced(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        """remove_label calls require_team_access with min_role=member."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)

        await service.remove_label(issue_id, label_id, user_id=sample_user_id)

        mock_team_service.require_team_access.assert_awaited_once_with(
            sample_user_id, sample_team_id, min_role=TeamRole.member
        )

    async def test_add_label_cross_team_label_rejected(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        mock_label_repository,
        sample_user_id,
        sample_team_id,
        other_team_id,
        issue_id,
        label_id,
        issue_obj,
    ):
        """A label from another team cannot be attached (404, no leak)."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_label_repository.get = AsyncMock(
            return_value=SimpleNamespace(
                id=label_id, team_id=other_team_id, name="Foreign", color=None
            )
        )

        with pytest.raises(NotFoundError):
            await service.add_label(issue_id, label_id, user_id=sample_user_id)

        mock_issue_repository.add_label.assert_not_awaited()


# ---------------------------------------------------------------------------
# Cross-team field validation (defense-in-depth) in create/update
# ---------------------------------------------------------------------------

class TestCrossTeamFieldValidation:
    async def test_create_rejects_cross_team_status(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        other_team_id,
        issue_obj,
    ):
        """A status from another team is rejected on create."""
        foreign_status = uuid.UUID("99999999-1111-1111-1111-111111111111")
        mock_workflow_state_repository.get = AsyncMock(
            return_value=SimpleNamespace(
                id=foreign_status, team_id=other_team_id, name="Other"
            )
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        with pytest.raises(NotFoundError):
            await service.create(
                IssueCreate(
                    team_id=sample_team_id, title="X", status_id=foreign_status
                ),
                user_id=sample_user_id,
            )

        mock_issue_repository.create.assert_not_awaited()

    async def test_create_rejects_non_member_assignee(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_obj,
        workflow_state_obj,
    ):
        """An assignee who is not a team member is rejected on create."""
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_team_service.get_membership = AsyncMock(return_value=None)
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)
        assignee = uuid.UUID("88888888-2222-2222-2222-222222222222")

        with pytest.raises(NotFoundError):
            await service.create(
                IssueCreate(
                    team_id=sample_team_id, title="X", assignee_id=assignee
                ),
                user_id=sample_user_id,
            )

        mock_issue_repository.create.assert_not_awaited()

    async def test_create_rejects_cross_team_label(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        mock_label_repository,
        sample_user_id,
        sample_team_id,
        other_team_id,
        issue_obj,
        workflow_state_obj,
        label_id,
    ):
        """A label from another team is rejected on create (attach_labels)."""
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_label_repository.get = AsyncMock(
            return_value=SimpleNamespace(
                id=label_id, team_id=other_team_id, name="Foreign", color=None
            )
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)

        with pytest.raises(NotFoundError):
            await service.create(
                IssueCreate(
                    team_id=sample_team_id, title="X", label_ids=[label_id]
                ),
                user_id=sample_user_id,
            )

        mock_issue_repository.attach_labels.assert_not_awaited()

    async def test_create_accepts_same_team_assignee(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_obj,
        workflow_state_obj,
    ):
        """A valid team-member assignee is accepted on create."""
        mock_workflow_state_repository.get_all = AsyncMock(
            return_value=[workflow_state_obj]
        )
        mock_issue_repository.allocate_identifier = AsyncMock(
            return_value="ENG-1"
        )
        mock_issue_repository.create = AsyncMock(return_value=issue_obj)
        assignee = uuid.UUID("88888888-3333-3333-3333-333333333333")

        await service.create(
            IssueCreate(
                team_id=sample_team_id, title="X", assignee_id=assignee
            ),
            user_id=sample_user_id,
        )

        mock_team_service.get_membership.assert_awaited_once_with(
            assignee, sample_team_id
        )
        mock_issue_repository.create.assert_awaited_once()

    async def test_update_rejects_cross_team_status(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        other_team_id,
        issue_id,
        issue_obj,
    ):
        """A status from another team is rejected on update."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        foreign_status = uuid.UUID("99999999-4444-4444-4444-444444444444")
        mock_workflow_state_repository.get = AsyncMock(
            return_value=SimpleNamespace(
                id=foreign_status, team_id=other_team_id, name="Other"
            )
        )

        with pytest.raises(NotFoundError):
            await service.update(
                issue_id,
                IssueUpdate(status_id=foreign_status),
                user_id=sample_user_id,
            )

        mock_issue_repository.update.assert_not_awaited()

    async def test_update_rejects_non_member_assignee(
        self,
        service,
        mock_team_service,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        issue_obj,
    ):
        """A non-member assignee is rejected on update."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_team_service.get_membership = AsyncMock(return_value=None)
        assignee = uuid.UUID("88888888-5555-5555-5555-555555555555")

        with pytest.raises(NotFoundError):
            await service.update(
                issue_id,
                IssueUpdate(assignee_id=assignee),
                user_id=sample_user_id,
            )

        mock_issue_repository.update.assert_not_awaited()

    async def test_update_skips_validation_when_status_unset(
        self,
        service,
        mock_team_service,
        mock_workflow_state_repository,
        mock_issue_repository,
        sample_user_id,
        sample_team_id,
        issue_id,
        issue_obj,
    ):
        """Updating only the title does not trigger status/assignee validation."""
        mock_team_service.get_team_ids_for_user = AsyncMock(
            return_value=[sample_team_id]
        )
        mock_issue_repository.get = AsyncMock(return_value=issue_obj)
        mock_issue_repository.update = AsyncMock(return_value=issue_obj)

        await service.update(
            issue_id, IssueUpdate(title="Only title"), user_id=sample_user_id
        )

        # status/assignee validation must not run when those fields are unset.
        mock_workflow_state_repository.get.assert_not_awaited()
        mock_team_service.get_membership.assert_not_awaited()
        mock_issue_repository.update.assert_awaited_once()
