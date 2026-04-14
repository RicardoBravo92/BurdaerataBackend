from pydantic import BaseModel

class QuestionCardCreate(BaseModel):
    text: str
    blank_count: int

class QuestionCardUpdate(BaseModel):
    text: str
    blank_count: int

class QuestionCardResponse(BaseModel):
    id: int
    text: str
    blank_count: int

