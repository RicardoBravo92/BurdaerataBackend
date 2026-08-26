from fastapi import APIRouter

from app.api.v1.endpoints.game import router as game_router
from app.api.v1.endpoints.websocket import router as ws_router
from app.api.v1.endpoints.cards import router as cards_router
from app.api.v1.endpoints.email import router as email_router

api_router = APIRouter()
api_router.include_router(game_router, prefix="/games", tags=["games"])
api_router.include_router(cards_router, prefix="/cards", tags=["cards"])
api_router.include_router(ws_router, prefix="/ws", tags=["websocket"])
api_router.include_router(email_router, prefix="/email", tags=["email"])
