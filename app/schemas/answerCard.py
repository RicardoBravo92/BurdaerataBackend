from pydantic import BaseModel

class AnswerCardCreate(BaseModel):
    text: str

class AnswerCardUpdate(BaseModel):
    text: str

class AnswerCardResponse(BaseModel):
    id: int
    text: str
