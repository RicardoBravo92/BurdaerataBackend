from fastapi import APIRouter

from app.api.v1.endpoints.game import router as game_router

api_router = APIRouter()
api_router.include_router(game_router, prefix="/games", tags=["games"])
