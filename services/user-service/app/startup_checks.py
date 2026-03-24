"""Verify external dependencies before the application serves traffic."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import get_settings
from app.db.session import engine

log = logging.getLogger("app.user_service")

# Keys in `startup_report` (stable for operators and log queries)
STEP_ENVIRONMENT = "environment"
STEP_DATABASE = "database"


async def _ping_database(conn_engine: AsyncEngine) -> None:
    async with conn_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


def _log_startup_summary(report: dict[str, Any], *, outcome: str) -> None:
    """Single summary line: all step keys and results, plus overall outcome."""
    log.info(
        "startup_checks_summary",
        extra={
            "event": "startup_checks_summary",
            "startup_report": dict(report),
            "outcome": outcome,
        },
    )


async def run_startup_dependency_checks() -> None:
    """
    Run startup steps in order; each step records a result in ``startup_report``.

    Emits a final log with ``startup_report`` mapping step name -> ``ok`` | ``failed`` and
    ``outcome`` ``ok`` | ``failed``. Raises on the first failed step so Uvicorn does not serve.
    """
    report: dict[str, Any] = {}

    log.info(
        "startup_dependency_checks_begin",
        extra={"event": "startup_dependency_checks_begin"},
    )

    # Step 1: environment — settings load and validate (``.env`` / env vars via Pydantic)
    log.info(
        "Verifying environment and settings",
        extra={
            "event": "startup_step",
            "dependency": STEP_ENVIRONMENT,
            "outcome": "pending",
        },
    )
    try:
        get_settings()
        report[STEP_ENVIRONMENT] = "ok"
    except Exception:
        report[STEP_ENVIRONMENT] = "failed"
        log.exception(
            "Environment/settings check failed; aborting startup",
            extra={
                "event": "startup_step",
                "dependency": STEP_ENVIRONMENT,
                "outcome": "failed",
            },
        )
        _log_startup_summary(report, outcome="failed")
        raise

    log.info(
        "Environment and settings OK",
        extra={
            "event": "startup_step",
            "dependency": STEP_ENVIRONMENT,
            "outcome": "ok",
        },
    )

    # Step 2: database connectivity
    log.info(
        "Verifying database (SELECT 1)",
        extra={
            "event": "startup_step",
            "dependency": STEP_DATABASE,
            "outcome": "pending",
        },
    )
    try:
        await _ping_database(engine)
        report[STEP_DATABASE] = "ok"
    except Exception:
        report[STEP_DATABASE] = "failed"
        log.exception(
            "Database connectivity check failed; aborting startup",
            extra={
                "event": "startup_step",
                "dependency": STEP_DATABASE,
                "outcome": "failed",
            },
        )
        _log_startup_summary(report, outcome="failed")
        raise

    log.info(
        "Database connectivity OK",
        extra={
            "event": "startup_step",
            "dependency": STEP_DATABASE,
            "outcome": "ok",
        },
    )

    _log_startup_summary(report, outcome="ok")
