# Logging (backend)

Wide events (canonical log lines): **one structured log line per request**,
emitted when the request ends, with all the context the request collected.
Code: `backend/app/core/logging/`. Tests: `backend/tests/e2e/test_logging.py`.

## Request flow

```
CORSMiddleware (outermost)
  -> WideEventMiddleware   creates request_id + WideEventContext, times the request
       -> auth dependency  log_user(user.id, user.email)
       -> router           log_action("create"), log_entity("item", id)
       -> service          BaseService logs entity_type/entity_id on reads and writes
  <- WideEventMiddleware   emits "request_completed" with every field
```

- `WideEventMiddleware` (`app/core/logging/middleware.py`) is the only app
  middleware. It also turns an unhandled exception into a JSON 500
  `{detail, error_code: "internal_server_error"}` (inside CORS, so the browser
  can read it) and logs it with the traceback.
- Middleware placement: a new cross-cutting HTTP middleware goes in
  `app/middlewares/` (create the package when you need it). A middleware that
  belongs to one feature stays in that feature's package, like
  `app/core/logging/middleware.py`. Register it in `create_app()` in
  `app/main.py`; `add_middleware` is LIFO (last added = outermost).

## Helpers (in handlers)

```python
from app.core.logging import log_action, log_custom, log_entities, log_entity, log_user
```

| Helper | Sets | Example |
|---|---|---|
| `log_action(name)` | `action` | `log_action("create")` |
| `log_entity(type, id)` | `entity_type`, `entity_id` | `log_entity("item", item.id)` |
| `log_entities(type, ids)` | `entity_type`, `entity_ids` | `log_entities("item", [a.id, b.id])` |
| `log_custom(**kwargs)` | `custom` (sanitized) | `log_custom(provider="google")` |
| `log_user(id, email)` | `user_id`, `email` | done by the auth dependency; do not call it in routers |

- Every router handler calls `log_action(...)` first.
- `entity_type` is the lowercase table name (`"item"`). `BaseService` already
  logs it for `get_by_id`, `get_by_field`, `create`, `create_many`, `upsert`,
  `update`, `delete`. Use the same name in `log_entity`.
- The helpers do nothing outside a request.
- `log_custom` values must be JSON-serializable.

## Other logs

For a log line that is not part of the wide event, use loguru directly:

```python
from loguru import logger

logger.warning("No entities to create")
```

No `print`, no `logging.getLogger`. Stdlib logs (uvicorn, SQLAlchemy, httpx)
are intercepted into loguru.

## Wide event fields

Always: `request_id` (new UUID per request), `method`, `path`, `status_code`,
`duration_ms`, `client_ip`, plus `service`, `environment` and, when set,
`version`, `commit_hash`, `instance_id`.

When set: `trace_id` (`X-Trace-Id` header, else `X-Request-ID`), `user_id`,
`email`, `path_template` (e.g. `/items/{item_id}`, only when it differs from
`path`), `query_string`, `entity_type`, `entity_id` / `entity_ids`, `action`,
`custom`, `error`, `error_type`, `error_message`.

`client_ip`: first `X-Forwarded-For` address, else `X-Real-IP`, else the peer.

Level: `ERROR` for 5xx or an error, `WARNING` for 4xx, else `INFO`.

## Sensitive data

- `custom` is passed through `sanitize_dict`: any key that contains
  `password`, `token`, `secret`, `api_key`, `authorization`, `auth`,
  `credential`, `cookie`, `session_id`, ... (`SENSITIVE_KEYS` in
  `app/core/logging/sanitizer.py`) becomes `[REDACTED]`, at any depth.
- `query_string` and uvicorn access lines redact the values of the same keys,
  plus the whole-word params `code` and `session`.
- Tracebacks never show variable values (`diagnose=False`), and SQL errors
  never show bound parameters (`hide_parameters=True`).
- Sentry (on when `ENVIRONMENT` is not `local`) never gets frame locals or
  PII. Its scrubber matches EXACT key names only, so a new secret field name
  (e.g. `new_api_key`) must be added to `SENSITIVE_KEYS` or to
  `_SENTRY_DENYLIST` in `app/main.py`.
- Never pass a secret as a value under a harmless key name.

## Settings (`app/core/config.py`, `LoggingSettings`)

| Var | Default | Notes |
|---|---|---|
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT` | `console` | `console` (colored, stderr) or `json` (stdout) |
| `VERSION`, `COMMIT_HASH`, `INSTANCE_ID` | unset | added to every log line when set |

## Testing logs

The backend e2e suite runs the server with `LOG_FORMAT=json` and parses its
output. Use the `server_log` fixture:

```python
def test_update_is_logged(auth_client: httpx.Client, server_log: ServerLogView) -> None:
    item = create_item(auth_client)
    response = auth_client.patch(f"/items/{item['id']}", json={"name": "New"})

    event = server_log.wide_event_for(response)
    assert (event["action"], event["entity_type"]) == ("update", "item")
    assert event["entity_id"] == item["id"]
```

See [e2e-testing.md](e2e-testing.md).
