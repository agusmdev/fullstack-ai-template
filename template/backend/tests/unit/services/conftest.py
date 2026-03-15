"""Service layer test fixtures with mocked repositories."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


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
def mock_item_repository():
    """Create a mock item repository."""
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
def sample_user_id():
    """Generate a sample user UUID."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def sample_user_model(sample_user_id):
    """Create a mock User model instance."""
    from argon2 import PasswordHasher

    ph = PasswordHasher()
    user = MagicMock()
    user.id = sample_user_id
    user.email = "test@example.com"
    user.display_name = "Test User"
    user.is_active = True
    user.password = ph.hash("correct_password")
    user.email_verified_at = None
    user.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    user.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    # Mock check_password method
    def check_password(password):
        from argon2.exceptions import VerifyMismatchError

        if password == "correct_password":
            return True
        raise VerifyMismatchError()

    user.check_password = check_password
    return user


@pytest.fixture
def sample_item_id():
    """Generate a sample item UUID."""
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def sample_item_model(sample_item_id):
    """Create a mock Item model instance."""
    item = MagicMock()
    item.id = sample_item_id
    item.name = "Test Item"
    item.description = "A test item description"
    item.quantity = 10
    item.sku = "TEST-SKU-001"
    item.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    item.updated_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    return item
