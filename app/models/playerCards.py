from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

class PlayerCards(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int
    user_id: int
    cards: List[str]
