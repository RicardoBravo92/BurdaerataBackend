from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ProfileBase(BaseModel):
    full_name: str = Field(max_length=255)
    first_name: str = Field(default="", max_length=255)
    last_name: str = Field(default="", max_length=255)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = Field(default=None, max_length=2048)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=255)
    last_name: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = Field(default=None, max_length=2048)


class ProfileRead(ProfileBase):
    id: str

    model_config = ConfigDict(from_attributes=True)