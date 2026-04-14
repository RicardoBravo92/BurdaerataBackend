from typing import List
from pydantic import BaseModel

class PlayerCardsCreate(BaseModel):
    game_id: int
    user_id: int
    cards: List[str]

class PlayerCardsUpdate(BaseModel):
    game_id: int
    user_id: int
    cards: List[str]

class PlayerCardsResponse(BaseModel):
    id: int
    game_id: int
    user_id: int
    cards: List[str]

