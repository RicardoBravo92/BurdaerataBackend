from typing import Any, Optional
from sqlmodel import Field, SQLModel, JSON

class RoundAnswer(SQLModel, table=True):
    __tablename__ = "round_answers"

    id: str = Field(primary_key=True, max_length=36)
    round_id: str = Field(
        foreign_key="rounds.id", 
        max_length=36, 
        index=True, 
        ondelete="CASCADE"
    )
    user_id: str = Field(foreign_key="users.id", max_length=255, ondelete="CASCADE")
    cards_used: list[Any] = Field(default_factory=list, sa_type=JSON)
    final_text: Optional[str] = Field(default=None, max_length=2048)
    is_winner: bool = Field(default=False)