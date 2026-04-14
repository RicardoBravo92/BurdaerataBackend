from pydantic import BaseModel

class RoundCreate(BaseModel):
    game_id: int
    judge_user_id: int
    question_card_id: int
    round_number: int
    status: str
    winning_answer_id: int

class RoundUpdate(BaseModel):
    game_id: int
    judge_user_id: int
    question_card_id: int
    round_number: int
    status: str
    winning_answer_id: int

class RoundResponse(BaseModel):
    id: int
    game_id: int
    judge_user_id: int
    question_card_id: int
    round_number: int
    status: str
    winning_answer_id: int

