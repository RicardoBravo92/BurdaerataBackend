from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .user import User

class Round(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int
    judge_user_id: int
    question_card_id: int
    round_number: int
    status: str
    winning_answer_id: int
    judge: User = Relationship(back_populates="rounds")
