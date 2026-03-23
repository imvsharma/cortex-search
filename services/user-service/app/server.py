import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .api import user
from .core.config import Environment, get_settings
from .core.logging_config import (
    configure_logging,
    request_id_ctx,
    _sanitize_log_fragment,
)

log = logging.getLogger("app.user_service")


class RequestIdASGIMiddleware:
    """
    Keep request_id in a ContextVar until the HTTP response is fully handed off on the ASGI
    wire. HTTP middleware resets in `finally` before Uvicorn access logs run, so those lines
    saw request_id as "-".
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id: str | None = None
        for key, value in scope.get("headers") or []:
            if key.lower() == b"x-request-id":
                request_id = value.decode("latin-1").strip()
                break
        if not request_id or len(request_id) > 128:
            request_id = str(uuid.uuid4())
        request_id = _sanitize_log_fragment(request_id, max_len=128)

        token = request_id_ctx.set(request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                out = dict(message)
                hdrs = [
                    (k, v)
                    for k, v in list(out.get("headers") or [])
                    if k.lower() != b"x-request-id"
                ]
                hdrs.append((b"x-request-id", request_id.encode("utf-8")))
                out["headers"] = hdrs
                await send(out)
                return
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, json_log_path=settings.log_json_file)
    environment = settings.environment
    assert isinstance(environment, Environment)
    log.info(
        "service_start",
        extra={
            "event": "service_start",
            "environment": environment.value,
            "project": settings.project_name,
        },
    )
    yield
    log.info("service_stop", extra={"event": "service_stop"})


app = FastAPI(title="User Service", lifespan=lifespan)
app.add_middleware(RequestIdASGIMiddleware)

app.include_router(user.router)
