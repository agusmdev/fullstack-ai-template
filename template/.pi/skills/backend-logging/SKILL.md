---
name: backend-logging
description: Wide event logging system reference. Covers WideEventMiddleware, canonical log lines, structured context helpers (log_action, log_entity, log_custom, log_user), and sensitive data sanitization. Use when adding logging to new features or debugging request flow.
---

# Backend Logging System

## Overview

The backend uses a **wide event / canonical log lines** pattern. Each HTTP request produces exactly one structured log entry at completion, enriched with context accumulated during handling.

**Location:** `app/core/logging/`

## Architecture

```
Request → WideEventMiddleware → RequestContextMiddleware → Route Handler
                                                              ↓
                                                     log_action("create")
                                                     log_entity("item", id)
                                                     log_custom(key=value)
                                                              ↓
WideEventMiddleware ← emits one log line with all accumulated context
```

## Quick Usage in Handlers

Import helpers from `app/core/logging`:

```python
from app.core.logging import log_action, log_entity, log_entities, log_custom

@router.post("")
async def create_item(item: ItemCreate, service: ItemService = Depends(get_item_service)):
    log_action("create")                    # Set the business action
    result = await service.create(item)
    log_entity("item", result.id)           # Tag the entity type + ID
    return result

@router.get("")
async def list_items(service: ItemService = Depends(get_item_service)):
    log_action("list")
    results = await service.get_all()
    log_entities("item", [r.id for r in results])  # Multiple entity IDs
    return results
```

### Available Helpers

| Helper | Purpose | Example |
|--------|---------|---------|
| `log_action(name)` | Name the business operation | `log_action("create")` |
| `log_entity(type, id)` | Tag single entity | `log_entity("item", item.id)` |
| `log_entities(type, ids)` | Tag multiple entities | `log_entities("item", [id1, id2])` |
| `log_custom(**kwargs)` | Add arbitrary context | `log_custom(import_count=42)` |
| `log_user(id, email)` | Tag the user (auto-set by auth) | `log_user(user.id, user.email)` |

All helpers safely no-op if called outside a request context.

## What Gets Auto-Logged

The `WideEventMiddleware` automatically captures per request:

| Field | Source |
|-------|--------|
| `method` | HTTP method (GET, POST, etc.) |
| `path` | URL path |
| `route` | Route template (e.g., `/items/{item_id}`) |
| `status_code` | Response status |
| `duration_ms` | Request duration in milliseconds |
| `client_ip` | From `X-Forwarded-For`, `X-Real-IP`, or direct connection |
| `query_string` | URL query parameters |
| `request_id` | UUID from `RequestContextMiddleware` |
| `trace_id` | From `X-Trace-ID` header (for distributed tracing) |
| `error_type` | Exception class name (if error) |
| `error_message` | Exception message (if error) |
| `user_id` | Set by auth middleware via `log_user()` |
| `user_email` | Set by auth middleware via `log_user()` |

## Log Format

Controlled by `LOG_FORMAT` setting:
- `"console"` (default, local dev) — human-readable colored output via loguru
- `"json"` (production) — structured JSON for log aggregation

## WideEventContext

The dataclass (`app/core/logging/context.py`) that accumulates request context:

```python
@dataclass
class WideEventContext:
    request_id: str | None
    trace_id: str | None
    user_id: str | None
    user_email: str | None
    method: str | None
    path: str | None
    route: str | None
    entity_type: str | None
    entity_id: str | None      # Single or comma-separated list
    action: str | None
    custom: dict[str, Any]     # From log_custom()
    error_type: str | None
    error_message: str | None
    duration_ms: float | None
    status_code: int | None
    client_ip: str | None
    query_string: str | None
```

## Sensitive Data Sanitization

The sanitizer (`app/core/logging/sanitizer.py`) automatically redacts fields matching:

`password`, `token`, `secret`, `api_key`, `apikey`, `authorization`, `credit_card`, `ssn`, `social_security`

Any dict value with a matching key is replaced with `[REDACTED]`. Applied recursively to nested dicts.

## Configuration

In `app/core/config.py` (`LoggingSettings`):

```python
LOG_LEVEL: str = "INFO"        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT: str = "console"    # "console" or "json"
VERSION: str | None = None     # App version (bound to all logs)
COMMIT_HASH: str | None = None # Git commit (bound to all logs)
INSTANCE_ID: str | None = None # Server instance (bound to all logs)
```

## Middleware Stack Order

In `app/main.py`, middleware is added in this order (outermost first):

1. `WideEventMiddleware` — creates context, emits log
2. `RequestContextMiddleware` — generates `request_id`
3. `CORSMiddleware` — handles CORS headers
