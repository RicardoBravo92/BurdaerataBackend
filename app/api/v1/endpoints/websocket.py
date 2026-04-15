import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.ws_manager import ws_manager

router = APIRouter()


@router.websocket("/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    token: str = Query(...),
):
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id: str = payload["sub"]
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_manager.connect(websocket, game_id, user_id)
 
    try:
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"event": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, user_id)
