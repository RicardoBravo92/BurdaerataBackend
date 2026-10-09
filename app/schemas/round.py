from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoundBase(BaseModel):
    round_number: int = Field(ge=1)
    question_card_id: str
    judge_user_id: str
    status: str = Field(pattern="^(submitting|judging|finished)$")
    winning_answer_id: Optional[str] = None


class RoundCreate(RoundBase):
    game_id: str


class RoundUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(submitting|judging|finished)$")
    winning_answer_id: Optional[str] = None


class RoundRead(RoundBase):
    id: str
    game_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Request bodies
class CreateRoundAnswerRequest(BaseModel):
    cards_used: list[str] = Field(min_length=1)


class SelectWinnerRequest(BaseModel):
    winning_answer_id: str