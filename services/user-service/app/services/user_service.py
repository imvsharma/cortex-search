"""Business logic for user profiles; delegates persistence to ``UserProfileRepository``."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserProfile
from app.repositories.user_repo import UserProfileRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Coordinates user profile create, read, update, delete, and list operations."""

    @staticmethod
    async def create_user(db: AsyncSession, user_profile_data: UserCreate) -> UserProfile:
        """Create and persist a new user profile."""
        return await UserProfileRepository.create(db=db, user_profile_data=user_profile_data)

    @staticmethod
    async def get_user(db: AsyncSession, user_id: UUID) -> UserProfile | None:
        """Return a single profile by id, or ``None`` if not found."""
        return await UserProfileRepository.get(db=db, user_id=user_id)

    @staticmethod
    async def get_all_users(db: AsyncSession) -> list[UserProfile]:
        """Return every user profile."""
        return await UserProfileRepository.get_all(db=db)

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: UUID) -> UserProfile | None:
        """Delete a profile by id; return the removed row or ``None`` if it did not exist."""
        return await UserProfileRepository.delete(db=db, user_id=user_id)

    @staticmethod
    async def update_user(
        db: AsyncSession, user_id: UUID, user_profile_data: UserUpdate
    ) -> UserProfile | None:
        """Apply partial updates to a profile; return the updated row or ``None`` if missing."""
        return await UserProfileRepository.update(
            db=db, user_id=user_id, user_profile_data=user_profile_data
        )
