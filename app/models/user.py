
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True, max_length=255)
    full_name: str = Field(default="Player")
    first_name: str = Field(default="")
    last_name: str = Field(default="")
    email: str | None = Field(default=None, unique=True, index=True, max_length=320)
    avatar_url: str | None = Field(default=None, max_length=2048)
