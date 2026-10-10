import uuid
from datetime import UTC, datetime

from sqlmodel import Column, DateTime, Field, SQLModel


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
    created_at: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
