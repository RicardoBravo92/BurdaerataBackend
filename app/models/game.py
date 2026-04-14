from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
  


class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str
    status: str 
    host_player_id: int
    max_players: int 
    score_to_win: int 
    public: bool 