"""Route-level tests for the Teams router.

These hit the mounted teams_router through FastAPI's TestClient (real HTTP,
dependency injection, response serialization) instead of importing the handler
functions and invoking them directly. The service and auth dependencies are
overridden so no database is touched.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.teams.dependencies import get_team_service
from app.modules.teams.routers import teams_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def team_obj(team_id, user_id):
    return SimpleNamespace(
        id=team_id,
        name="Test Team",
        key="TEST",
        issue_sequence=5,
    )


@pytest.fixture
def team_service(team_obj, team_id):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=team_obj)
    svc.create = AsyncMock(return_value=team_obj)
    svc.update = AsyncMock(return_value=team_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[team_obj], total=1, page=1, size=50, pages=1
        )
    )
    svc.get_role_map_for_user = AsyncMock(return_value={team_id: "admin"})
    return svc


@pytest.fixture
def client(user_id, team_service):
    app = FastAPI()
    app.include_router(teams_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_team_service] = lambda: team_service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestListTeams:
    def test_returns_paginated_teams(self, client, team_service):
        response = client.get("/teams")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "Test Team"
        assert body["items"][0]["key"] == "TEST"
        team_service.get_all_paginated.assert_awaited_once()

    def test_enriches_items_with_my_role(self, client, team_service, team_id):
        """Each list item carries the requesting user's role (VAL-CROSS-025)."""
        response = client.get("/teams")

        assert response.status_code == 200
        assert response.json()["items"][0]["my_role"] == "admin"
        team_service.get_role_map_for_user.assert_awaited_once()

    def test_propagates_user_id_to_service(self, client, team_service, user_id):
        client.get("/teams")

        _args, kwargs = team_service.get_all_paginated.await_args
        assert kwargs["user_id"] == user_id


class TestGetTeam:
    def test_returns_team_by_id(self, client, team_id):
        response = client.get(f"/teams/{team_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(team_id)
        assert response.json()["issue_sequence"] == 5

    def test_not_found_returns_404(self, client, team_service, team_id):
        team_service.get_by_id.side_effect = NotFoundError(
            detail=f"Team '{team_id}' not found"
        )

        response = client.get(f"/teams/{team_id}")

        assert response.status_code == 404

    def test_owns_user_id_from_auth(self, client, team_service, user_id, team_id):
        client.get(f"/teams/{team_id}")

        _args, kwargs = team_service.get_by_id.await_args
        assert kwargs["user_id"] == user_id


class TestCreateTeam:
    def test_creates_and_returns_201(self, client, team_service, user_id, team_id):
        response = client.post("/teams", json={"name": "New Team", "key": "NEW"})

        assert response.status_code == 201
        assert response.json()["id"] == str(team_id)
        _args, kwargs = team_service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_empty_name(self, client):
        response = client.post("/teams", json={"name": "", "key": "NEW"})

        assert response.status_code == 422

    def test_rejects_short_key(self, client):
        response = client.post("/teams", json={"name": "Team", "key": "X"})

        assert response.status_code == 422


class TestUpdateTeam:
    def test_updates_and_returns_team(self, client, team_service, team_id):
        response = client.patch(
            f"/teams/{team_id}", json={"name": "Updated", "key": "UPD"}
        )

        assert response.status_code == 200
        team_service.update.assert_awaited_once()


class TestDeleteTeam:
    def test_returns_204(self, client, team_service, team_id, user_id):
        response = client.delete(f"/teams/{team_id}")

        assert response.status_code == 204
        team_service.delete.assert_awaited_once_with(team_id, user_id=user_id)
