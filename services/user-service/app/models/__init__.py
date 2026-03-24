"""SQLAlchemy ORM models; import here so Alembic autogenerate registers metadata."""

from app.models.user import UserProfile

__all__ = ["UserProfile"]
