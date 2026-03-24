"""Repository for ``UserProfile`` persistence (synchronous SQLAlchemy AsyncSession)."""

from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserUpdate
from app.models.user import UserProfile


class UserProfileRepository:
    """Create, read, and delete operations for user profiles."""

    @staticmethod
    async def create(db: AsyncSession, user_profile_data: UserCreate) -> UserProfile:
        """Persist a new profile from a validated Pydantic model and return the stored row."""
        payload = user_profile_data.model_dump(mode="json", exclude_none=True)
        user_profile = UserProfile(**payload)
        db.add(user_profile)
        await db.commit()
        await db.refresh(user_profile)
        return user_profile

    @staticmethod
    async def get(db: AsyncSession, user_id: UUID) -> UserProfile | None:
        """Return the profile for ``user_id``, or ``None`` if missing."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession) -> list[UserProfile]:
        """Return all user profiles."""
        result = await db.execute(select(UserProfile))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, user_id: UUID) -> UserProfile | None:
        """Delete the profile for ``user_id`` if it exists; return the removed row or ``None``."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        await db.delete(user)
        await db.commit()
        return user

    @staticmethod
    async def update(db: AsyncSession, user_id: UUID, user_profile_data: UserUpdate) -> UserProfile | None:
        """Update the profile for ``user_id`` if it exists; return the updated row or ``None``."""
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        existing_user_profile = result.scalar_one_or_none()
        if existing_user_profile is None:
            return None
        for key, value in user_profile_data.model_dump(
            mode="json",
            exclude_unset=True,
        ).items():
            setattr(existing_user_profile, key, value)
        await db.commit()
        await db.refresh(existing_user_profile)
        return existing_user_profile

