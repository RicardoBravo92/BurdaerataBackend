from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    full_name: str = Field(default="Player", max_length=255)
    first_name: str = Field(default="", max_length=255)
    last_name: str = Field(default="", max_length=255)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = Field(default=None, max_length=2048)


class UserCreate(UserBase):
    id: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = Field(default=None, max_length=2048)


class UserRead(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)