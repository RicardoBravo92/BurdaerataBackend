from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str
    full_name: str

class UserUpdate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: str
    full_name: str