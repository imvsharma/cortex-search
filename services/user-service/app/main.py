import logging
import os

import uvicorn

from .core.config import get_settings
from .core.logging_config import configure_logging
from .server import app  # noqa: F401 — exposed for `uvicorn app.main:app`

_boot_log = logging.getLogger("app.user_service")


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_log_path=settings.log_json_file)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    _boot_log.info(
        "Booting User Service (HTTP will start after dependency checks in lifespan)",
        extra={
            "event": "service_boot",
            "environment": str(settings.environment),
            "project": settings.project_name,
        },
    )
    _boot_log.info(
        "Uvicorn binding to http://%s:%s (reload=%s)",
        host,
        port,
        reload,
        extra={"event": "uvicorn_bind", "outcome": "pending"},
    )
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run()
