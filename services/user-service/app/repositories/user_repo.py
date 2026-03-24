"""Repository for ``UserProfile`` persistence (synchronous SQLAlchemy session)."""

from __future__ import annotations

from uuid import UUID

from app.schemas.user import UserUpdate
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.user import UserProfile


class UserProfileRepository:
    """Create, read, and delete operations for user profiles."""

    @staticmethod
    def create(db: Session, user_profile_data: UserProfile) -> UserProfile:
        """Persist a new profile from a validated Pydantic model and return the stored row."""
        user_profile = UserProfile(**user_profile_data.model_dump())
        db.add(user_profile)
        db.commit()
        db.refresh(user_profile)
        return user_profile

    @staticmethod
    def get(db: Session, user_id: UUID) -> UserProfile | None:
        """Return the profile for ``user_id``, or ``None`` if missing."""
        return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    @staticmethod
    def get_all(db: Session) -> list[UserProfile]:
        """Return all user profiles."""
        return db.query(UserProfile).all()

    @staticmethod
    def delete(db: Session, user_id: UUID) -> UserProfile | None:
        """Delete the profile for ``user_id`` if it exists; return the removed row or ``None``."""
        user = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
        return user
    
    @staticmethod
    def update(db: Session, user_id: UUID, data: UserUpdate) -> UserProfile | None:
        """Update the profile for ``user_id`` if it exists; return the updated row or ``None``."""
        existing_user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if existing_user_profile is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(existing_user_profile, key, value)
        db.commit()
        db.refresh(existing_user_profile)
        return existing_user_profile
        
