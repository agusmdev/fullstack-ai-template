---
name: backend-filters
description: Reference for the backend filter and pagination system. Covers Filter classes, JoinFilter for cross-table queries, search fields, operator transformers, and fastapi_pagination integration. Use when adding or modifying list/search endpoints.
---

# Backend Filters & Pagination

## Overview

The backend uses `fastapi_filter` for query filtering and `fastapi_pagination` for paginated responses. Filters are declared as Pydantic-like classes and injected into routes via `Depends()`.

## Basic Filter

Create a `Filter` class per module in `filters.py`:

```python
from fastapi_filter.contrib.sqlalchemy.filter import Filter
from app.modules.your_entity.models import YourEntity

class YourEntityFilter(Filter):
    search: str | None = None
    name__like: str | None = None
    status__eq: str | None = None
    quantity__gte: int | None = None

    class Constants(Filter.Constants):
        model = YourEntity
        search_model_fields = ["name", "description"]  # For ?search= param
```

## Available Operators

Append to field name with `__` in the filter class:

| Operator | Query Param Example | SQL Equivalent |
|----------|-------------------|----------------|
| `__eq` | `?status__eq=active` | `= 'active'` |
| `__neq` | `?status__neq=deleted` | `!= 'deleted'` |
| `__gt` | `?price__gt=100` | `> 100` |
| `__gte` | `?price__gte=100` | `>= 100` |
| `__lt` | `?price__lt=50` | `< 50` |
| `__lte` | `?price__lte=50` | `<= 50` |
| `__like` | `?name__like=%widget%` | `LIKE '%widget%'` |
| `__ilike` | `?name__ilike=%widget%` | `ILIKE '%widget%'` (case-insensitive) |
| `__in` | `?status__in=active,pending` | `IN ('active', 'pending')` |
| `__not_in` | `?status__not_in=deleted` | `NOT IN ('deleted')` |
| `__isnull` | `?email__isnull=true` | `IS NULL` |

**Note:** `like` and `ilike` auto-wrap with `%` if no `%` is present in the value.

## Search Field

The `search` parameter performs case-insensitive `ILIKE` across all fields listed in `search_model_fields`:

```python
class Constants(Filter.Constants):
    model = YourEntity
    search_model_fields = ["name", "description", "sku"]
```

Query: `?search=widget` → `WHERE name ILIKE '%widget%' OR description ILIKE '%widget%' OR sku ILIKE '%widget%'`

## JoinFilter (Cross-Table Queries)

For filtering across related tables, use `JoinFilter` from `app/core/advanced_filtering.py`:

```python
from app.core.advanced_filtering import JoinFilter

class OrderItemFilter(Filter):
    """Sub-filter for the joined table."""
    name__ilike: str | None = None

    class Constants(Filter.Constants):
        model = Item

class OrderFilter(JoinFilter):
    search: str | None = None
    items: OrderItemFilter | None = None  # Nested filter for joined table

    class Constants(JoinFilter.Constants):
        model = Order
        search_model_fields = ["order_number"]
        joins = {
            "items": {
                "target": Item,      # Join target (optional, inferred from sub-filter)
                "onclause": Order.items,  # Relationship attribute
                "isouter": True,     # LEFT JOIN (optional)
            }
        }
```

Query: `?items.name__ilike=%widget%` → LEFT JOIN items, filter by item name.

## Pagination

Routes use `fastapi_pagination` for paginated responses:

```python
from fastapi_pagination import Page, Params

@router.get("")
async def list_entities(
    pagination: Params = Depends(),      # ?page=1&size=50
    entity_filter: YourEntityFilter = Depends(),  # ?search=...&name__like=...
    service: YourEntityService = Depends(get_your_entity_service),
) -> Page[YourEntityResponse]:
    result = await service.get_all(
        entity_filter=entity_filter,
        pagination_params=pagination,
    )
    return cast("Page[YourEntityResponse]", result)
```

**Pagination params:**
- `?page=1` — page number (1-indexed)
- `?size=50` — items per page (default 50, max controlled by `MAX_ALLOWED_MATCHES` in config)

**Response shape:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 50,
  "pages": 2
}
```

## Unpaginated List

To return all results without pagination, omit `pagination_params`:

```python
result = await service.get_all(entity_filter=entity_filter)
# Returns list[T] instead of Page[T]
```

## Repository Integration

The `SQLAlchemyRepository.get_all()` method handles filter application and pagination internally. The flow:

1. Filter class builds SQLAlchemy WHERE clauses from query params
2. `get_all()` applies filter to base query via `filter.filter(query)`
3. If `pagination_params` provided, wraps with `paginate()` from `fastapi_pagination`
4. Returns either `list[T]` or `Page[T]`
