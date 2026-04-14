from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    full_name: str
    avatar_url: str