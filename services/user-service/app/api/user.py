"""REST routes for user profile create, read, update, delete, and list."""

from __future__ import annotations

import logging
from uuid import UUID

from app.dependencies.user_dep import get_db
from app.schemas.user import UserCreate, UserCreatedResponse, UserUpdate
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger("app.user_service")

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserCreatedResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Persist a new user profile and return its representation."""
    created = await UserService.create_user(db, user)
    log.info(
        "user_profile_created",
        extra={"event": "user_profile_created", "user_id": created.user_id},
    )
    return created


@router.get("/{user_id}", response_model=UserCreatedResponse)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Return one user profile by id, or 404 if it does not exist."""
    row = await UserService.get_user(db, user_id)
    if not row:
        log.info(
            "user_profile_not_found",
            extra={"event": "user_profile_not_found", "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")
    log.info(
        "user_profile_retrieved",
        extra={"event": "user_profile_retrieved", "user_id": user_id},
    )
    return row


@router.get("/", response_model=list[UserCreatedResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    """Return all user profiles."""
    rows = await UserService.get_all_users(db)
    log.info(
        "user_profiles_listed",
        extra={"event": "user_profiles_listed", "count": len(rows)},
    )
    return rows


@router.delete("/{user_id}")
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a user profile by id."""
    row = await UserService.delete_user(db, user_id)
    if not row:
        log.info(
            "user_profile_delete_miss",
            extra={"event": "user_profile_delete_miss", "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")
    log.info(
        "user_profile_deleted",
        extra={"event": "user_profile_deleted", "user_id": user_id},
    )
    return {"message": "User deleted successfully"}


@router.patch("/{user_id}", response_model=UserCreatedResponse)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Apply partial updates to a user profile."""
    updated = await UserService.update_user(db, user_id, user)
    if not updated:
        log.info(
            "user_profile_update_miss",
            extra={"event": "user_profile_update_miss", "user_id": user_id},
        )
        raise HTTPException(status_code=404, detail="User not found")
    log.info(
        "user_profile_updated",
        extra={"event": "user_profile_updated", "user_id": user_id},
    )
    return updated
