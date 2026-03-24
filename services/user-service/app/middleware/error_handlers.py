"""
Map selected exceptions to JSON HTTP responses (FastAPI **exception handlers**,
not ASGI middleware — see ``app.server`` for request-id middleware).

**What gets handled where**

- **This module** — Only types you register here. Starlette picks the **most
  specific** matching handler (MRO), so a broad ``Exception`` handler does not
  replace FastAPI’s built-ins for more specific types.
- **FastAPI / Starlette defaults** (no code needed here) — ``HTTPException``,
  ``RequestValidationError`` (422 body validation), ``WebSocketRequestValidationError``,
  etc.
- **Still not “everything”** — Errors raised as ``BaseException`` subclasses other
  than ``Exception`` (e.g. ``KeyboardInterrupt``, ``asyncio.CancelledError`` on
  3.8+) are not routed through these HTTP handlers by design.

For request-scoped behavior (e.g. ``X-Request-ID``), use
``RequestIdASGIMiddleware`` in ``app.server``.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.integrity_errors import http_status_and_detail

log = logging.getLogger("app.user_service")


async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    status_code, detail = http_status_and_detail(exc)
    log.warning(
        "database_integrity_error",
        extra={
            "event": "database_integrity_error",
            "status_code": status_code,
        },
    )
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Last resort for HTTP: JSON 500, full traceback in logs only."""
    log.exception(
        "unhandled_exception",
        extra={
            "event": "unhandled_exception",
            "status_code": 500,
            "exc_type": type(exc).__name__,
        },
    )
    settings = get_settings()
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register app-specific handlers; specific types before the ``Exception`` fallback."""
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
