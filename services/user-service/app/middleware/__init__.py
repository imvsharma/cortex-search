"""HTTP concerns: ASGI middleware and FastAPI exception registration."""

from .error_handlers import register_exception_handlers

__all__ = ["register_exception_handlers"]
