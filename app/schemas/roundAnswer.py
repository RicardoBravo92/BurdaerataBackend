from typing import List
from pydantic import BaseModel

class RoundAnswerCreate(BaseModel):
    round_id: int
    user_id: int
    cards_used: List[str]
    final_text: str
    is_winner: bool

class RoundAnswerUpdate(BaseModel):
    round_id: int
    user_id: int
    cards_used: List[str]
    final_text: str
    is_winner: bool

class RoundAnswerResponse(BaseModel):
    id: int
    round_id: int
    user_id: int
    cards_used: List[str]
    final_text: str
    is_winner: bool

