"""Route-level tests for the WorkflowStates router.

Hits the mounted router through FastAPI's TestClient with the service and auth
dependencies overridden — no database touched.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.workflows.dependencies import get_workflow_state_service
from app.modules.workflows.models import WorkflowStateType
from app.modules.workflows.routers import workflow_states_router
from app.repositories.exceptions import NotFoundError
from app.user.auth import require_current_user_id


@pytest.fixture
def user_id():
    return uuid.UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def team_id():
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


@pytest.fixture
def state_id():
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def state_obj(state_id, team_id):
    return SimpleNamespace(
        id=state_id,
        team_id=team_id,
        name="In Progress",
        type=WorkflowStateType.started,
        position=2.0,
        color="#f2c94c",
    )


@pytest.fixture
def service(state_obj):
    svc = MagicMock()
    svc.get_by_id = AsyncMock(return_value=state_obj)
    svc.create = AsyncMock(return_value=state_obj)
    svc.update = AsyncMock(return_value=state_obj)
    svc.delete = AsyncMock(return_value=None)
    svc.get_all_paginated = AsyncMock(
        return_value=SimpleNamespace(
            items=[state_obj], total=1, page=1, size=50, pages=1
        )
    )
    return svc


@pytest.fixture
def client(user_id, service):
    app = FastAPI()
    app.include_router(workflow_states_router)
    app.dependency_overrides[require_current_user_id] = lambda: user_id
    app.dependency_overrides[get_workflow_state_service] = lambda: service
    with TestClient(app, base_url="http://test") as c:
        yield c


class TestAuthGuard:
    def test_no_token_rejected(self):
        """Without overriding auth, the router must reject unauthenticated calls.

        A missing Authorization header surfaces 401 Unauthorized (the custom
        ``_Bearer401`` maps FastAPI's default 403 to 401 so clients can react
        with their logout+redirect flow — VAL-CROSS-022).
        """
        app = FastAPI()
        app.include_router(workflow_states_router)
        with TestClient(app, base_url="http://test") as c:
            response = c.get("/workflow-states")
        assert response.status_code == 401


class TestList:
    def test_returns_paginated_states(self, client, service):
        response = client.get("/workflow-states")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "In Progress"
        assert body["items"][0]["type"] == "started"

    def test_passes_team_id_and_user_id(self, client, service, user_id, team_id):
        client.get("/workflow-states", params={"team_id": str(team_id)})

        _args, kwargs = service.get_all_paginated.await_args
        assert kwargs["user_id"] == user_id
        assert kwargs["team_id"] == team_id


class TestGet:
    def test_returns_state_by_id(self, client, state_id):
        response = client.get(f"/workflow-states/{state_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(state_id)

    def test_not_found_returns_404(self, client, service, state_id):
        service.get_by_id.side_effect = NotFoundError(detail="not found")

        response = client.get(f"/workflow-states/{state_id}")

        assert response.status_code == 404


class TestCreate:
    def test_creates_and_returns_201(self, client, service, user_id, team_id):
        response = client.post(
            "/workflow-states",
            json={
                "team_id": str(team_id),
                "name": "Triage",
                "type": "backlog",
                "position": 0.5,
            },
        )

        assert response.status_code == 201
        _args, kwargs = service.create.await_args
        assert kwargs["user_id"] == user_id

    def test_rejects_missing_required_fields(self, client):
        response = client.post("/workflow-states", json={"name": "No team/type"})

        assert response.status_code == 422

    def test_rejects_invalid_type(self, client, team_id):
        response = client.post(
            "/workflow-states",
            json={"team_id": str(team_id), "name": "X", "type": "frobnicated"},
        )

        assert response.status_code == 422


class TestUpdate:
    def test_updates_and_returns_state(self, client, service, state_id):
        response = client.patch(
            f"/workflow-states/{state_id}", json={"name": "Renamed"}
        )

        assert response.status_code == 200
        service.update.assert_awaited_once()


class TestDelete:
    def test_returns_204(self, client, service, state_id, user_id):
        response = client.delete(f"/workflow-states/{state_id}")

        assert response.status_code == 204
        service.delete.assert_awaited_once_with(state_id, user_id=user_id)
