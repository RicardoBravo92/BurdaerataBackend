from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GameBase(BaseModel):
    code: str = Field(min_length=4, max_length=16)
    status: str = Field(pattern="^(waiting|playing|finished)$")
    max_players: int = Field(ge=2, le=20)
    score_to_win: int = Field(ge=1)
    public: bool = True


class GameCreate(GameBase):
    host_player_id: str


class GameUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(waiting|playing|finished)$")
    max_players: int | None = Field(default=None, ge=2, le=20)
    score_to_win: int | None = Field(default=None, ge=1)
    public: bool | None = None


class GameRead(GameBase):
    id: str
    host_player_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GameListResponse(BaseModel):
    total: int
    items: list[GameRead]


# Request bodies for game endpoints
class CreateGameRequest(BaseModel):
    max_players: int = Field(default=8, ge=2, le=20)
    score_to_win: int = Field(default=7, ge=1)


class JoinGameRequest(BaseModel):
    code: str


class StartGameRequest(BaseModel):
    pass  # No body needed, just path params


class StartNextRoundRequest(BaseModel):
    pass
