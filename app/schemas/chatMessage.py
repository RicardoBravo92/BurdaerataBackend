from pydantic import BaseModel, Field

class ChatMessageCreate(BaseModel):
    game_id: str = Field(...)
    user_id: str = Field(...)
    text: str = Field(..., max_length=1000)

class ChatMessageResponse(ChatMessageCreate):
    id: str
    created_at: str

    class Config:
        from_attributes = True
