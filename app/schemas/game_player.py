from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    user_full_name: str | None = None
    user_avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PlayerCardsRead(BaseModel):
    game_id: str
    user_id: str
    cards: list[str]


class LeaveGameResponse(BaseModel):
    success: bool