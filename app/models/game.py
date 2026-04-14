from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Game(SQLModel, table=True):
    __tablename__ = "games"

    id: str = Field(primary_key=True, max_length=36)
    code: str = Field(unique=True, index=True, max_length=16)
    host_player_id: str = Field(foreign_key="users.id", max_length=255)
    status: str = Field(default="waiting", max_length=32)
    max_players: int = Field(default=8)
    public: bool = Field(default=True)
    score_to_win: Optional[int] = Field(default=7)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
