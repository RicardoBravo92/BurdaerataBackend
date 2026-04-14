from pydantic import BaseModel

class GamePlayerCreate(BaseModel):
    game_id: int
    user_id: int
    score: int
    is_host: bool
    is_ready: bool
    avatar_url: str

class GamePlayerUpdate(BaseModel):
    game_id: int
    user_id: int
    score: int
    is_host: bool
    is_ready: bool
    avatar_url: str

class GamePlayerResponse(BaseModel):
    id: int
    game_id: int
    user_id: int
    score: int
    is_host: bool
    is_ready: bool
    avatar_url: str
