"""Items CRUD and ownership: a user only ever sees and changes their own items.

This file is the reference example for a feature module's e2e tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest

from tests.e2e.helpers import assert_error, create_item

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser
    from tests.e2e.stack import Database

ITEM_FIELDS = {"id", "user_id", "name", "description", "created_at", "updated_at"}


def _set_sku(db: Database, item_id: str, sku: str) -> None:
    # The items API has no sku field yet; only the by-SKU lookup exists.
    assert db.execute("UPDATE item SET sku = %s WHERE id = %s", (sku, item_id))


def test_create_returns_the_item_with_owner_and_timestamps(
    register_user: Callable[..., RegisteredUser],
) -> None:
    user = register_user()

    response = user.client.post(
        "/items", json={"name": "Lamp", "description": "Desk lamp"}
    )

    assert response.status_code == 201
    item = response.json()
    assert set(item) == ITEM_FIELDS
    assert item["name"] == "Lamp"
    assert item["description"] == "Desk lamp"
    assert item["user_id"] == user.id
    uuid.UUID(item["id"])
    assert datetime.fromisoformat(item["created_at"]).tzinfo is not None
    assert user.client.get(f"/items/{item['id']}").json() == item


def test_create_without_description_stores_null(auth_client: httpx.Client) -> None:
    item = create_item(auth_client, name="Plain")

    assert item["description"] is None
    assert auth_client.get(f"/items/{item['id']}").json()["description"] is None


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "name"),
        ({"name": ""}, "name"),
        ({"name": "x" * 256}, "name"),
        ({"name": "ok", "description": "x" * 5001}, "description"),
    ],
)
def test_create_validates_the_payload(
    auth_client: httpx.Client, payload: dict[str, Any], field: str
) -> None:
    response = auth_client.post("/items", json=payload)

    body = assert_error(response, 422, "validation_error")
    assert [issue["loc"] for issue in body["detail"]] == [["body", field]]
    assert auth_client.get("/items").json()["total"] == 0


def test_create_accepts_the_maximum_lengths(auth_client: httpx.Client) -> None:
    item = create_item(auth_client, name="n" * 255, description="d" * 5000)

    assert len(item["name"]) == 255
    assert len(item["description"]) == 5000


def test_update_changes_only_the_sent_fields(auth_client: httpx.Client) -> None:
    item = create_item(auth_client, name="Old name", description="Keep me")

    response = auth_client.patch(f"/items/{item['id']}", json={"name": "New name"})

    assert response.status_code == 200
    updated = auth_client.get(f"/items/{item['id']}").json()
    assert updated["name"] == "New name"
    assert updated["description"] == "Keep me"
    assert updated["created_at"] == item["created_at"]
    assert datetime.fromisoformat(updated["updated_at"]) > datetime.fromisoformat(
        item["updated_at"]
    )
    assert response.json() == updated


def test_update_with_null_description_clears_it(auth_client: httpx.Client) -> None:
    item = create_item(auth_client, name="Item", description="Remove me")

    response = auth_client.patch(f"/items/{item['id']}", json={"description": None})

    assert response.status_code == 200
    assert auth_client.get(f"/items/{item['id']}").json()["description"] is None


def test_update_with_an_empty_body_changes_nothing(auth_client: httpx.Client) -> None:
    item = create_item(auth_client, name="Same", description="Same")

    response = auth_client.patch(f"/items/{item['id']}", json={})

    assert response.status_code == 200
    stored = auth_client.get(f"/items/{item['id']}").json()
    assert (stored["name"], stored["description"]) == ("Same", "Same")


@pytest.mark.parametrize(
    "payload",
    [
        # Regression: explicit null on the NOT NULL name column was a 500.
        {"name": None},
        {"name": ""},
        {"description": "x" * 5001},
    ],
)
def test_update_rejects_invalid_values(
    auth_client: httpx.Client, payload: dict[str, Any]
) -> None:
    item = create_item(auth_client, name="Valid", description="Valid")

    response = auth_client.patch(f"/items/{item['id']}", json=payload)

    assert_error(response, 422, "validation_error")
    stored = auth_client.get(f"/items/{item['id']}").json()
    assert (stored["name"], stored["description"]) == ("Valid", "Valid")


def test_delete_removes_the_item(auth_client: httpx.Client) -> None:
    item = create_item(auth_client)
    kept = create_item(auth_client, name="Kept")

    response = auth_client.delete(f"/items/{item['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert_error(auth_client.get(f"/items/{item['id']}"), 404, "not_found")
    assert [i["id"] for i in auth_client.get("/items").json()["items"]] == [kept["id"]]


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_missing_item_is_404(auth_client: httpx.Client, method: str) -> None:
    missing = str(uuid.uuid4())
    body = {"name": "x"} if method == "PATCH" else None

    response = auth_client.request(method, f"/items/{missing}", json=body)

    assert_error(response, 404, "not_found", f"Item {missing} not found")


def test_item_id_must_be_a_uuid(auth_client: httpx.Client) -> None:
    body = assert_error(auth_client.get("/items/not-a-uuid"), 422, "validation_error")

    assert body["detail"][0]["loc"] == ["path", "item_id"]


def test_get_by_sku_returns_the_item(auth_client: httpx.Client, db: Database) -> None:
    item = create_item(auth_client, name="Has a SKU")
    _set_sku(db, item["id"], "SKU-001")

    response = auth_client.get("/items/by-sku/SKU-001")

    assert response.status_code == 200
    assert response.json() == auth_client.get(f"/items/{item['id']}").json()


def test_get_by_unknown_sku_is_404(auth_client: httpx.Client) -> None:
    response = auth_client.get("/items/by-sku/NOPE-1")

    assert_error(response, 404, "not_found", "Item with SKU 'NOPE-1' not found")


# --- Ownership -------------------------------------------------------------------


@pytest.fixture
def owner_and_stranger(
    register_user: Callable[..., RegisteredUser],
) -> tuple[RegisteredUser, RegisteredUser]:
    """Two users; only the first one owns items."""
    return register_user(), register_user()


def test_users_list_only_their_own_items(
    owner_and_stranger: tuple[RegisteredUser, RegisteredUser],
) -> None:
    owner, stranger = owner_and_stranger
    mine = create_item(owner.client, name="Mine")
    theirs = create_item(stranger.client, name="Theirs")

    owner_list = owner.client.get("/items").json()
    stranger_list = stranger.client.get("/items").json()

    assert [i["id"] for i in owner_list["items"]] == [mine["id"]]
    assert owner_list["total"] == 1
    assert [i["id"] for i in stranger_list["items"]] == [theirs["id"]]


@pytest.mark.parametrize(
    ("method", "body"),
    [("GET", None), ("PATCH", {"name": "Hijacked"}), ("DELETE", None)],
)
def test_another_users_item_looks_missing(
    owner_and_stranger: tuple[RegisteredUser, RegisteredUser],
    method: str,
    body: dict[str, Any] | None,
) -> None:
    owner, stranger = owner_and_stranger
    item = create_item(owner.client, name="Private")

    response = stranger.client.request(method, f"/items/{item['id']}", json=body)

    # The same 404 as for a missing item: nothing reveals that the item exists.
    assert_error(response, 404, "not_found", f"Item {item['id']} not found")
    assert owner.client.get(f"/items/{item['id']}").json() == item


def test_another_users_sku_looks_missing(
    owner_and_stranger: tuple[RegisteredUser, RegisteredUser], db: Database
) -> None:
    owner, stranger = owner_and_stranger
    item = create_item(owner.client, name="Private")
    _set_sku(db, item["id"], "SKU-PRIVATE")

    response = stranger.client.get("/items/by-sku/SKU-PRIVATE")

    # The same 404 as for an unknown SKU, without the owner's item id.
    assert_error(response, 404, "not_found", "Item with SKU 'SKU-PRIVATE' not found")
    assert item["id"] not in response.text
    assert owner.client.get("/items/by-sku/SKU-PRIVATE").status_code == 200


def test_create_ignores_user_id_in_the_payload(
    owner_and_stranger: tuple[RegisteredUser, RegisteredUser],
) -> None:
    owner, stranger = owner_and_stranger

    response = stranger.client.post(
        "/items", json={"name": "Planted", "user_id": owner.id}
    )

    # The owner is always the caller; nobody can create items for another user.
    assert response.status_code == 201
    assert response.json()["user_id"] == stranger.id
    assert owner.client.get("/items").json()["total"] == 0
    assert stranger.client.get("/items").json()["total"] == 1


def test_update_cannot_move_an_item_to_another_user(
    owner_and_stranger: tuple[RegisteredUser, RegisteredUser],
) -> None:
    owner, stranger = owner_and_stranger
    item = create_item(owner.client, name="Mine")

    response = owner.client.patch(
        f"/items/{item['id']}", json={"name": "Still mine", "user_id": stranger.id}
    )

    assert response.status_code == 200
    stored = owner.client.get(f"/items/{item['id']}").json()
    assert (stored["user_id"], stored["name"]) == (owner.id, "Still mine")
    assert stranger.client.get("/items").json()["total"] == 0
    assert_error(stranger.client.get(f"/items/{item['id']}"), 404, "not_found")
