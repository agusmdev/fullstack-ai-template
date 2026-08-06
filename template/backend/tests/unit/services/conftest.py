"""Service layer test fixtures with mocked repositories."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.user.models import User


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.create_many = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_session_repository():
    """Create a mock session repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.delete_session = AsyncMock()
    repo.delete_all_for_user = AsyncMock()
    return repo


@pytest.fixture
def mock_password_reset_repository():
    """Create a mock password reset token repository."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_valid_token = AsyncMock()
    repo.mark_as_used = AsyncMock()
    repo.invalidate_user_tokens = AsyncMock()
    return repo


@pytest.fixture
def mock_email_verification_repository():
    """Create a mock email verification token repository."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_valid_token = AsyncMock()
    repo.mark_as_used = AsyncMock()
    repo.invalidate_user_tokens = AsyncMock()
    return repo


@pytest.fixture
def mock_team_repository():
    """Create a mock team repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.create_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_team_membership_repository():
    """Create a mock team membership repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_workflow_state_repository():
    """Create a mock workflow state repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.create_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_label_repository():
    """Create a mock label repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.create_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_project_repository():
    """Create a mock project repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.create_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    return repo


@pytest.fixture
def mock_issue_repository():
    """Create a mock issue repository."""
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_field = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_all_paginated = AsyncMock()
    repo.create = AsyncMock()
    repo.create_many = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.upsert = AsyncMock()
    repo.allocate_identifier = AsyncMock(return_value="ENG-1")
    repo.add_label = AsyncMock(return_value=None)
    repo.remove_label = AsyncMock(return_value=None)
    repo.attach_labels = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_team_service():
    """Create a mock TeamService for scoping in domain services."""
    svc = MagicMock()
    svc.get_team_ids_for_user = AsyncMock(return_value=[])
    svc.require_team_access = AsyncMock()
    svc.get_membership = AsyncMock()
    return svc


@pytest.fixture
def sample_user_id():
    """Generate a sample user UUID."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_user_model(sample_user_id):
    """Create a real User instance with an argon2-hashed password.

    Uses the production ``User.check_password`` (argon2 verification) rather than a
    stubbed string comparison, so any code path that verifies credentials exercises
    the real hashing logic and would catch a regression in that method.
    """
    from argon2 import PasswordHasher

    ph = PasswordHasher()
    return User(
        id=sample_user_id,
        email="test@example.com",
        display_name="Test User",
        is_active=True,
        password=ph.hash("correct_password"),
        email_verified_at=None,
        created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
