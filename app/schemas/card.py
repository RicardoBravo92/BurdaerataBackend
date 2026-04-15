from pydantic import BaseModel


class QuestionCard(BaseModel):
    id: str
    text: str
    blank_count: int


class AnswerCard(BaseModel):
    id: str
    text: str


class QuestionCardListItem(BaseModel):
    id: str
    blank_count: int


class AnswerCardListItem(BaseModel):
    id: str
