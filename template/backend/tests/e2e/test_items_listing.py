"""GET /items: filters (name__ilike, search), ordering (order_by) and pagination."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from tests.e2e.helpers import assert_error, create_item

if TYPE_CHECKING:
    from collections.abc import Callable

    import httpx

    from tests.e2e.helpers import RegisteredUser


def _names(response: httpx.Response) -> list[str]:
    assert response.status_code == 200, response.text
    return [item["name"] for item in response.json()["items"]]


@pytest.fixture
def fruit(auth_client: httpx.Client) -> httpx.Client:
    """A user with five items, created in this order."""
    for name, description in [
        ("Mango", "sweet tropical fruit"),
        ("Apple", "crunchy fruit"),
        ("Banana", "TROPICAL and yellow"),
        ("Cherry", None),
        ("Durian", "smells strong"),
    ]:
        create_item(auth_client, name=name, description=description)
    return auth_client


def test_default_order_is_oldest_first(fruit: httpx.Client) -> None:
    assert _names(fruit.get("/items")) == [
        "Mango",
        "Apple",
        "Banana",
        "Cherry",
        "Durian",
    ]


@pytest.mark.parametrize(
    ("order_by", "expected"),
    [
        ("name", ["Apple", "Banana", "Cherry", "Durian", "Mango"]),
        ("-name", ["Mango", "Durian", "Cherry", "Banana", "Apple"]),
        ("-created_at", ["Durian", "Cherry", "Banana", "Apple", "Mango"]),
    ],
)
def test_order_by_sorts_the_list(
    fruit: httpx.Client, order_by: str, expected: list[str]
) -> None:
    # Regression: order_by was read from the request body and ignored.
    assert _names(fruit.get("/items", params={"order_by": order_by})) == expected


def test_order_by_accepts_several_fields(auth_client: httpx.Client) -> None:
    for name, description in [("B", "same"), ("A", "same"), ("C", "first")]:
        create_item(auth_client, name=name, description=description)

    response = auth_client.get("/items", params={"order_by": "description,-name"})

    assert _names(response) == ["C", "B", "A"]


@pytest.mark.parametrize(
    "order_by",
    [
        "not_a_column",
        # Model attributes that are not columns (a 500 before, not a 422).
        "metadata",
        "-__table__",
        "registry",
        # The same field twice is ambiguous.
        "name,-name",
    ],
)
def test_order_by_rejects_invalid_values(
    auth_client: httpx.Client, order_by: str
) -> None:
    response = auth_client.get("/items", params={"order_by": order_by})

    body = assert_error(response, 422, "validation_error")
    assert body["detail"][0]["loc"][-1] == "order_by"


@pytest.mark.parametrize("pattern", ["%an%", "%AN%"])
def test_name_ilike_matches_case_insensitively(
    fruit: httpx.Client, pattern: str
) -> None:
    response = fruit.get("/items", params={"name__ilike": pattern})

    assert _names(response) == ["Mango", "Banana", "Durian"]
    assert response.json()["total"] == 3


def test_name_ilike_without_wildcards_still_matches_substrings(
    fruit: httpx.Client,
) -> None:
    assert _names(fruit.get("/items", params={"name__ilike": "err"})) == ["Cherry"]


def test_search_matches_name_or_description_case_insensitively(
    fruit: httpx.Client,
) -> None:
    assert _names(fruit.get("/items", params={"search": "tropical"})) == [
        "Mango",
        "Banana",
    ]
    assert _names(fruit.get("/items", params={"search": "DURIAN"})) == ["Durian"]
    assert _names(fruit.get("/items", params={"search": "no-such-thing"})) == []


def test_filters_combine_with_ordering_and_pagination(fruit: httpx.Client) -> None:
    response = fruit.get(
        "/items",
        params={"search": "fruit", "order_by": "-name", "size": 1, "page": 2},
    )

    assert _names(response) == ["Apple"]
    page = response.json()
    assert (page["total"], page["pages"], page["page"], page["size"]) == (2, 2, 2, 1)


def test_filters_never_return_another_users_items(
    fruit: httpx.Client, register_user: Callable[..., RegisteredUser]
) -> None:
    stranger = register_user()
    create_item(stranger.client, name="Stranger mango", description="tropical")

    assert _names(fruit.get("/items", params={"search": "Stranger"})) == []
    assert _names(stranger.client.get("/items", params={"search": "tropical"})) == [
        "Stranger mango"
    ]


def test_pagination_splits_the_list_into_pages(fruit: httpx.Client) -> None:
    pages = [
        fruit.get("/items", params={"size": 2, "page": page}).json()
        for page in (1, 2, 3)
    ]

    assert [[i["name"] for i in p["items"]] for p in pages] == [
        ["Mango", "Apple"],
        ["Banana", "Cherry"],
        ["Durian"],
    ]
    assert {(p["total"], p["pages"], p["size"]) for p in pages} == {(5, 3, 2)}
    assert [p["page"] for p in pages] == [1, 2, 3]


def test_page_after_the_last_one_is_empty(fruit: httpx.Client) -> None:
    page = fruit.get("/items", params={"size": 2, "page": 4}).json()

    assert page["items"] == []
    assert page["total"] == 5


def test_default_page_size_is_50(auth_client: httpx.Client) -> None:
    page = auth_client.get("/items").json()

    assert page == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"size": 101}, "size"),
        ({"size": 0}, "size"),
        ({"page": 0}, "page"),
        ({"page": "first"}, "page"),
    ],
)
def test_pagination_rejects_invalid_values(
    auth_client: httpx.Client, params: dict[str, Any], field: str
) -> None:
    response = auth_client.get("/items", params=params)

    body = assert_error(response, 422, "validation_error")
    assert body["detail"][0]["loc"] == ["query", field]
