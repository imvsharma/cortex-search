"""Structured logging setup, request correlation, and log-injection-safe formatting."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

_logging_configured = False


def _utc_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _sanitize_log_fragment(value: str, max_len: int = 2048) -> str:
    """Strip CR/LF to reduce log injection; cap length (codeguard logging)."""
    cleaned = value.replace("\r", " ").replace("\n", " ")
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned


class RequestIdFilter(logging.Filter):
    """Attach request_id from context to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        rid = request_id_ctx.get("")
        record.request_id = rid if rid else "-"
        return True


# Explicit allow-list for `extra={...}` fields in JSON and console (no LogRecord internals).
_STRUCTURED_KEYS = frozenset(
    {
        "event",
        "environment",
        "project",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "user_id",
        "count",
        "dependency",
        "outcome",
    }
)

# Console: show allow-listed extras except `event` (duplicates the message when msg == event).
_CONSOLE_STRUCTURED_KEYS = sorted(_STRUCTURED_KEYS - {"event"})


class JsonFormatter(logging.Formatter):
    """One JSON object per line for centralized log pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": _utc_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for key in _STRUCTURED_KEYS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


# ANSI SGR (console only; JSON file logs stay plain).
_LEVEL_COLOR: dict[int, str] = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;31m",  # bold red
}
_RESET = "\033[0m"


def _console_color_enabled(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("FORCE_COLOR", "").strip():
        return True
    return stream.isatty()


class ConsoleFormatter(logging.Formatter):
    """Human-readable lines for terminal (UTC timestamps, colored level when TTY)."""

    converter = time.gmtime

    def __init__(self, stream: TextIO | None = None) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")
        self._stream = stream if stream is not None else sys.stdout

    def format(self, record: logging.LogRecord) -> str:
        ts = f"{self.formatTime(record, self.datefmt)}Z"
        if _console_color_enabled(self._stream):
            prefix = _LEVEL_COLOR.get(record.levelno, "")
            level = f"{prefix}{record.levelname:8s}{_RESET}"
        else:
            level = f"{record.levelname:8s}"
        rid = getattr(record, "request_id", "-")
        extras: list[str] = []
        for key in _CONSOLE_STRUCTURED_KEYS:
            if hasattr(record, key):
                val = getattr(record, key)
                if val is not None and val != "":
                    extras.append(f"{key}={val}")
        extra_suffix = f" | {' '.join(extras)}" if extras else ""
        line = f"{ts} | {level} | {rid} | {record.name} | {record.getMessage()}{extra_suffix}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


def _route_uvicorn_loggers_to_root(level: int) -> None:
    """Send Uvicorn's own records through the root logger (same text + JSON file sinks)."""
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
        uv_logger.setLevel(level)


def configure_logging(level: str = "INFO", *, json_log_path: str | None = None) -> None:
    """
    Attach console (text) and optional file (JSON) handlers to the root logger.

    Handler setup runs once per process; every call refreshes root level and re-attaches
    Uvicorn loggers to root (Uvicorn applies its own logging config at startup).
    """
    global _logging_configured
    root = logging.getLogger()
    root.setLevel(level.upper())
    level_no = getattr(logging, level.upper(), logging.INFO)

    if not _logging_configured:
        _logging_configured = True

        req_filter = RequestIdFilter()

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(ConsoleFormatter(stream=console.stream))
        console.addFilter(req_filter)
        root.addHandler(console)

        if json_log_path:
            path = Path(json_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(JsonFormatter())
            file_handler.addFilter(req_filter)
            root.addHandler(file_handler)

    _route_uvicorn_loggers_to_root(level_no)


__all__ = [
    "ConsoleFormatter",
    "JsonFormatter",
    "RequestIdFilter",
    "configure_logging",
    "_route_uvicorn_loggers_to_root",
    "request_id_ctx",
    "_sanitize_log_fragment",
]
