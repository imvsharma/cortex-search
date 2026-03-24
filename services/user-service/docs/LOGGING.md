# Integrating `logging_config` in any module

This service uses a single root logging setup in `app/core/logging_config.py`: **console** (human-readable, UTC, optional color) and an optional **JSON lines file** for aggregation. HTTP requests get a **`request_id`** on every line automatically.

You do **not** import formatters or handlers in normal application code—only `configure_logging` at process entry, and the standard library `logging` module everywhere else.

---

## 1. One-time setup (already wired)

Call `configure_logging` early in the process, before much other logging:

- **`app/main.py`** — before `uvicorn.run`
- **`app/server.py`** — at the start of the FastAPI **lifespan** (so reload/worker processes re-apply after Uvicorn resets loggers)

Settings come from `app.core.config` / environment:

| Setting | Env / source | Role |
|--------|----------------|------|
| Log level | `LOG_LEVEL` (default `INFO`) | Root and Uvicorn loggers |
| JSON file | `LOG_JSON_FILE` (default `logs/user-service.jsonl`; empty disables file sink) | One JSON object per line |

If you add a new entrypoint (CLI script, worker), call:

```python
from app.core.config import get_settings
from app.core.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level, json_log_path=settings.log_json_file)
```

Handlers attach to the **root** logger only once per process; repeated calls refresh level and re-route Uvicorn loggers.

---

## 2. Using logging in any file

Use the standard library logger pattern. Pick a **stable logger name** (hierarchical, usually under `app.`):

```python
import logging

log = logging.getLogger("app.user_service")
# or, for a submodule:
log = logging.getLogger("app.repositories.user_repo")
```

Then log as usual:

```python
log.debug("verbose detail")
log.info("something happened")
log.warning("recoverable issue")
log.error("operation failed")
log.exception("failed with traceback")  # same as error(..., exc_info=True)
```

**Parameterized messages** (preferred—avoids string formatting if the level is disabled):

```python
log.info("Loaded %d rows for tenant=%s", count, tenant_id)
```

---

## 3. Structured fields (`extra=`) for JSON and console

Only keys listed in `_STRUCTURED_KEYS` inside `logging_config.py` are copied into **JSON** output and appended on the **console** line. Anything else is ignored by the custom formatters (by design: avoids leaking arbitrary `LogRecord` attributes).

Current allow-list:

`event`, `environment`, `project`, `method`, `path`, `status_code`, `duration_ms`, `user_id`, `count`, `dependency`, `outcome`, `startup_report`

**Convention:** set `event` to a stable machine-friendly name; use the **message** for a short human-readable phrase (they can match).

```python
log.info(
    "user_profile_created",
    extra={
        "event": "user_profile_created",
        "user_id": str(user_id),
    },
)
```

On the console, `event` is **not** duplicated in the `key=value` suffix (it would repeat the message when they are the same). Other allow-listed keys still appear.

**To add a new field** (e.g. `tenant_id`): edit `_STRUCTURED_KEYS` in `app/core/logging_config.py` and use that key consistently in `extra`.

---

## 4. Request correlation (`request_id`)

For HTTP traffic, `RequestIdASGIMiddleware` in `app/server.py` sets `request_id` from the `X-Request-ID` header or generates a UUID. The `RequestIdFilter` attaches it to every log record.

Inside request handling code you do **nothing special**—use `log.info(...)` and the line will show the current `request_id`.

For **non-HTTP** code (startup, background tasks) the request id is typically `-` unless you set the context yourself:

```python
from app.core.logging_config import request_id_ctx

token = request_id_ctx.set("job-123")
try:
    log.info("batch_step", extra={"event": "batch_step"})
finally:
    request_id_ctx.reset(token)
```

---

## 5. Untrusted strings in logs (log injection)

For values that come from users or headers, avoid raw newlines in log messages. Use the helper:

```python
from app.core.logging_config import _sanitize_log_fragment

safe = _sanitize_log_fragment(raw_string, max_len=128)
log.info("Received header value=%s", safe)
```

---

## 6. Checklist for a new module

1. `import logging`
2. `log = logging.getLogger("app.<area>.<module>")`
3. Use `log.info` / `log.warning` / `log.error` / `log.exception`
4. For operational signals, add `extra={"event": "...", ...}` with **only** allow-listed keys
5. Do not log secrets, tokens, passwords, or full connection strings

---

## 7. Reference: imports by use case

| Need | Import from `app.core.logging_config` |
|------|----------------------------------------|
| App / worker startup | `configure_logging` |
| Correlate logs in non-HTTP code | `request_id_ctx` |
| Sanitize untrusted fragments | `_sanitize_log_fragment` |
| Tests or custom handlers (rare) | `JsonFormatter`, `ConsoleFormatter`, `RequestIdFilter` |

Normal feature code only needs `logging.getLogger(...)` plus optional `configure_logging` in its entrypoint if it is a standalone process.
