from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .user import User

class RoundAnswer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int
    user_id: int
    cards_used: List[str]
    final_text: str
    is_winner: bool
    user: User = Relationship(back_populates="round_answers")
