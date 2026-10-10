import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    # Connection limits to prevent DoS
    MAX_CONNECTIONS_PER_USER = 3
    MAX_CONNECTIONS_PER_GAME = 50
    MAX_TOTAL_CONNECTIONS = 500

    # Heartbeat settings
    PING_INTERVAL = 30      # seconds between pings
    PONG_TIMEOUT = 60       # seconds to wait for pong before closing

    def __init__(self):
        self._connections: dict[str, dict[str, WebSocket]] = {}
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

    def _count_user_connections(self, user_id: str) -> int:
        """Count total connections for a user across all games."""
        count = 0
        for game_connections in self._connections.values():
            if user_id in game_connections:
                count += 1
        return count

    def _count_game_connections(self, game_id: str) -> int:
        """Count total connections for a game."""
        if game_id not in self._connections:
            return 0
        return len(self._connections[game_id])

    def _count_total_connections(self) -> int:
        """Count total connections across all games."""
        return sum(len(c) for c in self._connections.values())

    async def connect(self, websocket: WebSocket, game_id: str, user_id: str) -> bool:
        """
        Accept connection if within limits.
        Returns True if connected, False if rejected (connection closed).
        """
        # Check total connection limit
        if self._count_total_connections() >= self.MAX_TOTAL_CONNECTIONS:
            await websocket.close(code=4008, reason="Server at capacity")
            return False

        # Check per-user limit
        if self._count_user_connections(user_id) >= self.MAX_CONNECTIONS_PER_USER:
            await websocket.close(code=4008, reason="Too many connections for user")
            return False

        # Check per-game limit
        if self._count_game_connections(game_id) >= self.MAX_CONNECTIONS_PER_GAME:
            await websocket.close(code=4008, reason="Game at capacity")
            return False

        await websocket.accept()
        if game_id not in self._connections:
            self._connections[game_id] = {}
        self._connections[game_id][user_id] = websocket

        # Start heartbeat for this connection
        self._start_heartbeat(game_id, user_id, websocket)
        return True

    def _start_heartbeat(self, game_id: str, user_id: str, websocket: WebSocket) -> None:
        """Start a background task to send periodic pings."""
        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(self.PING_INTERVAL)
                    # Check if connection still exists
                    if (game_id not in self._connections or 
                        user_id not in self._connections[game_id] or
                        self._connections[game_id][user_id] != websocket):
                        break
                    
                    try:
                        # Send ping and wait for pong
                        pong_waiter = asyncio.create_task(websocket.receive())
                        
                        await websocket.send_json({"event": "ping"})
                        
                        # Wait for pong with timeout
                        try:
                            await asyncio.wait_for(pong_waiter, timeout=self.PONG_TIMEOUT)
                        except TimeoutError:
                            # No pong received - close connection
                            await websocket.close(code=4009, reason="Heartbeat timeout")
                            break
                            
                    except (asyncio.CancelledError, ConnectionError, RuntimeError) as e:
                        # Connection error - will be handled by disconnect
                        logger.debug("WebSocket ping error: %s", e)
                        break
            except asyncio.CancelledError:
                pass
            except (ConnectionError, RuntimeError) as e:
                logger.debug("Heartbeat task error: %s", e)

        task = asyncio.create_task(heartbeat())
        self._heartbeat_tasks[f"{game_id}:{user_id}"] = task

    def _stop_heartbeat(self, game_id: str, user_id: str) -> None:
        """Stop the heartbeat task for a connection."""
        key = f"{game_id}:{user_id}"
        if key in self._heartbeat_tasks:
            self._heartbeat_tasks[key].cancel()
            del self._heartbeat_tasks[key]

    def disconnect(self, game_id: str, user_id: str) -> None:
        self._stop_heartbeat(game_id, user_id)
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
            except (RuntimeError, ConnectionError) as e:
                logger.debug("Failed to send to user %s: %s", user_id, e)
                disconnected.append(user_id)
        for uid in disconnected:
            self.disconnect(game_id, uid)

    async def broadcast_to_game(self, game_id: str, event: str, data: Any) -> None:
        await self.send_to_game(game_id, event, data)

    def get_connected_users(self, game_id: str) -> list[str]:
        if game_id not in self._connections:
            return []
        return list(self._connections[game_id].keys())

    def get_stats(self) -> dict[str, int]:
        """Get connection statistics for monitoring."""
        return {
            "total_connections": self._count_total_connections(),
            "total_games": len(self._connections),
            "games": {
                game_id: len(users)
                for game_id, users in self._connections.items()
            },
        }


ws_manager = ConnectionManager()