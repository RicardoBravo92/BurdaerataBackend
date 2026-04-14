from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class RoundAnswer(SQLModel, table=True):
    __tablename__ = "round_answers"

    id: str = Field(primary_key=True, max_length=36)
    round_id: str = Field(foreign_key="rounds.id", max_length=36, index=True)
    user_id: str = Field(foreign_key="users.id", max_length=255)
    cards_used: list[Any] = Field(default_factory=list, sa_column=Column(JSON))
    final_text: Optional[str] = Field(default=None, max_length=2048)
    is_winner: bool = Field(default=False)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
