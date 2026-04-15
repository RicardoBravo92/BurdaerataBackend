from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from clerk_backend_api.jwt import verify_token
from app.core.config import get_settings
from app.core.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(...),
):
    settings = get_settings()
    try:
        payload = verify_token(token, settings.CLERK_SECRET_KEY)
        user_id: str = payload["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_manager.connect(websocket, game_id, user_id)
    await ws_manager.send_to_game(game_id, "player_joined", {"user_id": user_id})

    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"event": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, user_id)
        await ws_manager.send_to_game(game_id, "player_left", {"user_id": user_id})
