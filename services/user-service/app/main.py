import os

import uvicorn

from .core.config import get_settings
from .core.logging_config import configure_logging
from .server import app


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level, json_log_path=settings.log_json_file)

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run()
