from typing import Any

from sqlmodel import JSON, Field, SQLModel


class PlayerCard(SQLModel, table=True):
    __tablename__ = "player_cards"

    id: int | None = Field(default=None, primary_key=True)
    user_id: str | None = Field(
        default=None, foreign_key="users.id", max_length=255, ondelete="CASCADE"
    )
    game_id: str | None = Field(
        default=None, foreign_key="games.id", max_length=36, ondelete="CASCADE"
    )
    cards: list[Any] = Field(default_factory=list, sa_type=JSON)
