# Filters and pagination (backend)

List endpoints use `fastapi-filter` (2.0.1) for filtering and sorting and
`fastapi-pagination` (0.14.2) for pages. Reference: `ItemFilter` in
`backend/app/modules/items/filters.py` and `list_items` in
`backend/app/modules/items/routers.py`. Tests: `backend/tests/e2e/test_items_listing.py`.

## The filter class

```python
from app.core.filters import ModelFilter
from app.modules.items.models import Item


class ItemFilter(ModelFilter):
    order_by: list[str] = ["created_at"]
    name__ilike: str | None = None
    search: str | None = None

    class Constants(ModelFilter.Constants):
        model = Item
        search_model_fields = ["name", "description"]
```

`ItemFilter` declares only these three params:

| Param | Meaning |
|---|---|
| `order_by` | comma-separated fields; `-field` = descending. Default `created_at`. Unknown field or the same field twice = 422 `validation_error`. |
| `name__ilike` | name, case-insensitive pattern. Send the `%` wildcards yourself: `%lamp%`. |
| `search` | `ILIKE '%term%'` on every field in `search_model_fields` (name OR description). |

A param works only if it is declared on the filter class.

## Operators for new filters

Declare `<field>__<op>: <type> | None = None`:

| `op` | Example query | SQL |
|---|---|---|
| (none) | `?status=active` | `= 'active'` |
| `neq` | `?status__neq=deleted` | `!= 'deleted'` |
| `gt` / `gte` / `lt` / `lte` | `?quantity__gte=10` | `>= 10` |
| `like` / `ilike` | `?name__ilike=%lamp%` | `ILIKE '%lamp%'` |
| `in` / `not_in` | `?status__in=a,b` (type `list[str] \| None`) | `IN ('a', 'b')` |
| `isnull` | `?description__isnull=true` | `IS NULL` |
| `not` | `?status__not=deleted` | `IS NOT 'deleted'` |

- There is **no `__eq`**. Equality uses the bare field name.
- `like` / `ilike`: pass `%` explicitly. Auto-wrapping a value without `%` is
  deprecated in fastapi-filter and only works with a warning.
- Frontend: escape user text before you put it in a pattern (see
  `escapeLikePattern` in `frontend/src/lib/api-endpoints.ts`).
- Cross-table filters: there is no join-filter helper in this project. Build
  the join in the service with `QueryOptions(base_query=select(...).join(...))`.

## In the router

```python
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params

async def list_items(
    pagination: Params = Depends(),
    item_filter: ItemFilter = FilterDepends(ItemFilter),
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> Page[ItemResponse]:
```

Always `FilterDepends(...)`. Plain `Depends()` reads list fields such as
`order_by` from the request body, and the query param is ignored.

## Pagination

`Params` from `fastapi_pagination`:

| Param | Default | Limit |
|---|---|---|
| `page` | 1 | >= 1 |
| `size` | 50 | 1..100 (more = 422) |

Response (`Page[T]`):

```json
{ "items": [...], "total": 100, "page": 1, "size": 50, "pages": 2 }
```

## How the query runs

1. The service builds an optional base query, e.g.
   `QueryOptions(base_query=select(Item).where(Item.user_id == user_id))`.
2. `SQLAlchemyRepository._build_filtered_query` applies `entity_filter.filter(query)`
   and then `entity_filter.sort(query)`.
3. `get_all_paginated(pagination_params, entity_filter, options)` returns
   `Page[T]`; `get_all(entity_filter, options)` returns `list[T]` (no pages).

Always scope user-owned lists in the service (base query), never in the filter.

## Tests

Every declared filter param, `order_by` (asc, desc, invalid), and paging
(`page`, `size`, `total`, `pages`) needs an e2e test. Copy
`tests/e2e/test_items_listing.py`. See [e2e-testing.md](e2e-testing.md).
