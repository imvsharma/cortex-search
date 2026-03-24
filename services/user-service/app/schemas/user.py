from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    """Payload to create a profile; omit optional fields or send null to store NULL."""

    user_id: UUID = Field(default_factory=uuid4)
    email: EmailStr | None = None
    display_name: str | None = None
    avatar_url: HttpUrl | None = None
    bio: str | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    display_name: str | None = None
    avatar_url: HttpUrl | None = None
    bio: str | None = None
    last_seen: datetime | None = None


class UserCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: EmailStr | None = None
    display_name: str | None = None
    avatar_url: HttpUrl | None = None
    bio: str | None = None
    last_seen: datetime | None = None
