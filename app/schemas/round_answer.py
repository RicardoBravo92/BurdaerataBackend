from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    user_full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
