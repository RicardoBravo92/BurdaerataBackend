import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.ws_manager import ws_manager
from app.core.database import AsyncSessionLocal
from app.models.chat_message import ChatMessage
from app.models.user import User

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
            event = data.get("event")
            
            if event == "send_chat_message":
                text = data.get("data", {}).get("text", "")
                if text:
                    async with AsyncSessionLocal() as session:
                        new_msg = ChatMessage(game_id=game_id, user_id=user_id, text=text)
                        session.add(new_msg)
                        
                        user = await session.get(User, user_id)
                        full_name = user.full_name if user else "Unknown player"
                        
                        await session.commit()
                        await session.refresh(new_msg)

                        await ws_manager.broadcast_to_game(game_id, "new_chat_message", {
                            "id": new_msg.id,
                            "text": new_msg.text,
                            "user": {
                                "id": user_id,
                                "full_name": full_name
                            }
                        })
            else:
                await websocket.send_json({"event": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, user_id)
