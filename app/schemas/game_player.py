from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GamePlayerBase(BaseModel):
    user_id: str
    score: int = 0


class GamePlayerCreate(GamePlayerBase):
    game_id: str


class GamePlayerRead(GamePlayerBase):
    id: str
    game_id: str
    is_host: bool
    joined_at: datetime
    user_full_name: Optional[str] = None
    user_avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PlayerCardsRead(BaseModel):
    game_id: str
    user_id: str
    cards: list[str]


class LeaveGameResponse(BaseModel):
    success: bool