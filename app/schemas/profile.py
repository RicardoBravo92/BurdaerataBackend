from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProfileBase(BaseModel):
    full_name: str = Field(max_length=255)
    first_name: str = Field(default="", max_length=255)
    last_name: str = Field(default="", max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=2048)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=255)
    last_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = Field(default=None, max_length=2048)


class ProfileRead(ProfileBase):
    id: str

    model_config = ConfigDict(from_attributes=True)
