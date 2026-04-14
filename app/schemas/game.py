from pydantic import BaseModel

class GameCreate(BaseModel):
    code: str
    status: str
    host_player_id: int
    max_players: int
    score_to_win: int
    public: bool

class GameUpdate(BaseModel):
    code: str
    status: str
    host_player_id: int
    max_players: int
    score_to_win: int
    public: bool

class GameResponse(BaseModel):
    id: int
    code: str
    status: str
    host_player_id: int
    max_players: int
    score_to_win: int
    public: bool
