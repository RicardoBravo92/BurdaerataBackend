from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class GamePlayer(SQLModel, table=True):
    __tablename__ = "game_players"

    id: str = Field(primary_key=True, max_length=36)
    game_id: str = Field(
        foreign_key="games.id", max_length=36, index=True, ondelete="CASCADE"
    )
    user_id: str = Field(
        foreign_key="users.id", max_length=255, index=True, ondelete="CASCADE"
    )
    score: int = Field(default=0)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
