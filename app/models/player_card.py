from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class PlayerCard(SQLModel, table=True):
    __tablename__ = "player_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", max_length=255)
    game_id: Optional[str] = Field(default=None, foreign_key="games.id", max_length=36)
    cards: list[Any] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
