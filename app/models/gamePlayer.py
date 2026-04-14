from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .user import User

class GamePlayer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int
    user_id: int
    score: int
    is_host: bool
    is_ready: bool
    user: User = Relationship(back_populates="game_players")
    profile: User = Relationship(back_populates="game_players")
    avatar_url: str