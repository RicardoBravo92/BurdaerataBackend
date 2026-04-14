from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    avatar_url: str
    last_name: str
    full_name: str
    email: str = Field(unique=True, index=True, nullable=False)
    