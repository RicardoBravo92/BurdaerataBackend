from typing import Any, Optional
from sqlmodel import Field, SQLModel, JSON

class PlayerCard(SQLModel, table=True):
    __tablename__ = "player_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[str] = Field(
        default=None, 
        foreign_key="users.id", 
        max_length=255, 
        ondelete="CASCADE"
    )
    game_id: Optional[str] = Field(
        default=None, 
        foreign_key="games.id", 
        max_length=36, 
        ondelete="CASCADE"
    )
    cards: list[Any] = Field(default_factory=list, sa_type=JSON)