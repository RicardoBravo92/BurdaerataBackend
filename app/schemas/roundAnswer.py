from pydantic import BaseModel


class RoundAnswerCreate(BaseModel):
    round_id: int
    user_id: int
    cards_used: list[str]
    final_text: str
    is_winner: bool


class RoundAnswerUpdate(BaseModel):
    round_id: int
    user_id: int
    cards_used: list[str]
    final_text: str
    is_winner: bool


class RoundAnswerResponse(BaseModel):
    id: int
    round_id: int
    user_id: int
    cards_used: list[str]
    final_text: str
    is_winner: bool
