from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class Round(SQLModel, table=True):
    __tablename__ = "rounds"

    id: str = Field(primary_key=True, max_length=36)
    game_id: str = Field(
        foreign_key="games.id", max_length=36, index=True, ondelete="CASCADE"
    )
    round_number: int
    question_card_id: str = Field(max_length=64)
    judge_user_id: str = Field(
        foreign_key="users.id", max_length=255, ondelete="CASCADE"
    )
    status: str = Field(default="submitting", max_length=32)
    winning_answer_id: Optional[str] = Field(default=None, max_length=36)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
