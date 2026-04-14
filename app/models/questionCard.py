from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

class QuestionCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    blank_count: int
