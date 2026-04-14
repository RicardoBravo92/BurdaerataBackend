from pydantic import BaseModel

class ProfileCreate(BaseModel):
    user_id: int
    full_name: str
    avatar_url: str

class ProfileUpdate(BaseModel):
    user_id: int
    full_name: str
    avatar_url: str

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    avatar_url: str 