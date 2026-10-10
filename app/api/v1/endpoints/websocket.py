from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header
from clerk_backend_api.security import (
    TokenVerificationError,
    VerifyTokenOptions,
    verify_token_async,
)

from app.core.ws_manager import ws_manager
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.repositories.game_repository import game_repository
import html

router = APIRouter()

MAX_CHAT_MESSAGE_LENGTH = 500


def _authorized_parties() -> list[str]:
    return settings.authorized_parties


async def _authenticate_token(token: str) -> str | None:
    """Verify the Clerk session token and return the user id, or None if invalid."""
    if not settings.clerk_secret_key:
        return None

    try:
        payload = await verify_token_async(
            token,
            VerifyTokenOptions(
                secret_key=settings.clerk_secret_key,
                authorized_parties=_authorized_parties() or None,
            ),
        )
    except TokenVerificationError:
        return None

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        return None
    return user_id


@router.websocket("/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    authorization: str | None = Header(None),
):
    """
    WebSocket endpoint with token authentication via Authorization header.
    
    Client should connect with: 
    ws://host/api/v1/ws/{game_id}
    Headers: Authorization: Bearer <clerk_jwt>
    """
    if not authorization or not authorization.startswith("Bearer "):
        await websocket.close(code=4001, reason="Missing or invalid Authorization header")
        return

    token = authorization[7:]  # Remove "Bearer " prefix
    user_id = await _authenticate_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Only players who belong to the game may open a socket for it.
    async with AsyncSessionLocal() as session:
        if not await game_repository.get_player_row(session, game_id, user_id):
            await websocket.close(code=4003, reason="Not a player in this game")
            return

    connected = await ws_manager.connect(websocket, game_id, user_id)
    if not connected:
        return

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")

            # Handle pong response to heartbeat ping
            if event == "pong":
                continue

            if event == "send_chat_message":
                text = data.get("data", {}).get("text", "")
                if not isinstance(text, str):
                    continue

                # Sanitize: escape HTML to prevent XSS if frontend renders dangerously
                text = html.escape(text.strip()[:MAX_CHAT_MESSAGE_LENGTH])
                if not text:
                    continue

                async with AsyncSessionLocal() as session:
                    new_msg = ChatMessage(game_id=game_id, user_id=user_id, text=text)
                    session.add(new_msg)

                    user = await session.get(User, user_id)
                    full_name = user.full_name if user else "Unknown player"

                    await session.commit()
                    await session.refresh(new_msg)

                    await ws_manager.broadcast_to_game(
                        game_id,
                        "new_chat_message",
                        {
                            "id": new_msg.id,
                            "text": new_msg.text,
                            "user": {"id": user_id, "full_name": full_name},
                        },
                    )
            else:
                await websocket.send_json({"event": "ack", "data": data})
    except WebSocketDisconnect:
        ws_manager.disconnect(game_id, user_id)