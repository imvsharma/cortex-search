"""Verify external dependencies before the application serves traffic."""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import engine

log = logging.getLogger("app.user_service")


async def _ping_database(conn_engine: AsyncEngine) -> None:
    async with conn_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def run_startup_dependency_checks() -> None:
    """
    Run lightweight connectivity checks for each configured dependency.

    Raises on first failure so Uvicorn aborts startup instead of serving with a broken DB.
    """
    log.info(
        "startup_dependency_checks_begin",
        extra={"event": "startup_dependency_checks_begin"},
    )

    log.info(
        "Verifying database (SELECT 1)",
        extra={
            "event": "startup_check",
            "dependency": "database",
            "outcome": "pending",
        },
    )
    try:
        await _ping_database(engine)
    except Exception:
        log.exception(
            "Database connectivity check failed; aborting startup",
            extra={
                "event": "startup_check",
                "dependency": "database",
                "outcome": "failed",
            },
        )
        raise

    log.info(
        "Database connectivity OK",
        extra={
            "event": "startup_check",
            "dependency": "database",
            "outcome": "ok",
        },
    )

    log.info(
        "startup_dependency_checks_complete",
        extra={"event": "startup_dependency_checks_complete"},
    )
