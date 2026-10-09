from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoundAnswerBase(BaseModel):
    round_id: str
    user_id: str
    cards_used: list[str]
    final_text: str
    is_winner: bool = False


class RoundAnswerCreate(RoundAnswerBase):
    pass


class RoundAnswerRead(RoundAnswerBase):
    id: str
    created_at: datetime
    user_full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)