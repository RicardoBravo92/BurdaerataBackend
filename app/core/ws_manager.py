from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str) -> None:
        await websocket.accept()
        if game_id not in self._connections:
            self._connections[game_id] = {}
        self._connections[game_id][user_id] = websocket

    def disconnect(self, game_id: str, user_id: str) -> None:
        if game_id in self._connections:
            self._connections[game_id].pop(user_id, None)
            if not self._connections[game_id]:
                del self._connections[game_id]

    async def send_to_game(self, game_id: str, event: str, data: Any) -> None:
        if game_id not in self._connections:
            return
        message = {"event": event, "data": data}
        disconnected = []
        for user_id, ws in self._connections[game_id].items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(user_id)
        for uid in disconnected:
            self.disconnect(game_id, uid)

    async def broadcast_to_game(self, game_id: str, event: str, data: Any) -> None:
        await self.send_to_game(game_id, event, data)

    def get_connected_users(self, game_id: str) -> list[str]:
        if game_id not in self._connections:
            return []
        return list(self._connections[game_id].keys())


ws_manager = ConnectionManager()
