from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, HttpUrl

class UserCreate(BaseModel):
    user_id: Optional[UUID]
    email: Optional[EmailStr]=None
    display_name: Optional[str]=None
    avatar_url: Optional[HttpUrl]=None
    bio: Optional[str]=None
    last_seen: Optional[datetime]=None
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr]=None
    display_name: Optional[str]=None
    avatar_url: Optional[HttpUrl]=None
    bio: Optional[str]=None
    last_seen: Optional[datetime]=None

class UserCreatedResponse(BaseModel):
    user_id: Optional[UUID]
    email: Optional[EmailStr]=None
    display_name: Optional[str]=None
    avatar_url: Optional[HttpUrl]=None
    bio: Optional[str]=None
    last_seen: Optional[datetime]=None
