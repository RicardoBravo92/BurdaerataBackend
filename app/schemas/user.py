from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    full_name: str = Field(default="Player", max_length=255)
    first_name: str = Field(default="", max_length=255)
    last_name: str = Field(default="", max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=2048)


class UserCreate(UserBase):
    id: str


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=2048)


class UserRead(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
