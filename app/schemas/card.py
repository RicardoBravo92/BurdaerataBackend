from pydantic import BaseModel, Field, ConfigDict


class QuestionCardBase(BaseModel):
    text: str
    blank_count: int = Field(ge=1)


class QuestionCardCreate(QuestionCardBase):
    id: str


class QuestionCardRead(QuestionCardBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class QuestionCardListItem(BaseModel):
    id: str
    blank_count: int

    model_config = ConfigDict(from_attributes=True)


class AnswerCardBase(BaseModel):
    text: str


class AnswerCardCreate(AnswerCardBase):
    id: str


class AnswerCardRead(AnswerCardBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class AnswerCardListItem(BaseModel):
    id: str

    model_config = ConfigDict(from_attributes=True)