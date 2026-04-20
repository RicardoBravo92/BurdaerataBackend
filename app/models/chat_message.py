import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, Column, DateTime


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=255
    )
    game_id: str = Field(
        foreign_key="games.id", index=True, max_length=255, ondelete="CASCADE"
    )
    user_id: str = Field(
        foreign_key="users.id", index=True, max_length=255, ondelete="CASCADE"
    )
    text: str = Field(max_length=1000)
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
