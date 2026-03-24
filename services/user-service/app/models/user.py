"""SQLAlchemy ORM model for user profile rows in PostgreSQL."""

from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.functions import now as sa_now
from app.db.base import Base


class UserProfile(Base):
    """Public profile for a user: identity, presentation fields, and `last_seen` timestamp."""

    __tablename__ = "user_profile"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
        index = True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str] = mapped_column(String(255), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=sa_now(), onupdate=sa_now())

    def __repr__(self) -> str:
        return (
            f"UserProfile(user_id={self.user_id!r}, "
            f"display_name={self.display_name!r})"
        )
