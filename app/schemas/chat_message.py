from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ChatMessageBase(BaseModel):
    game_id: str
    user_id: str
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageRead(ChatMessageBase):
    id: str
    created_at: datetime
    user_full_name: str
    user_avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessageListResponse(BaseModel):
    messages: list[ChatMessageRead]