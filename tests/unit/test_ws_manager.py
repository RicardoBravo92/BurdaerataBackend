from app.core.ws_manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, fail_send=False):
        self.accepted = False
        self.sent = []
        self.fail_send = fail_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.fail_send:
            raise RuntimeError("connection closed")
        self.sent.append(message)


class TestConnectionManager:
    async def test_connect_adds_websocket(self):
        manager = ConnectionManager()
        ws = FakeWebSocket()

        await manager.connect(ws, "game-1", "user-1")

        assert ws.accepted is True
        assert manager.get_connected_users("game-1") == ["user-1"]

    async def test_connect_multiple_users(self):
        manager = ConnectionManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()

        await manager.connect(ws1, "game-1", "user-1")
        await manager.connect(ws2, "game-1", "user-2")

        assert set(manager.get_connected_users("game-1")) == {"user-1", "user-2"}

    async def test_disconnect_removes_user(self):
        manager = ConnectionManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        await manager.connect(ws1, "game-1", "user-1")
        await manager.connect(ws2, "game-1", "user-2")

        manager.disconnect("game-1", "user-1")

        assert manager.get_connected_users("game-1") == ["user-2"]

    async def test_disconnect_last_user_removes_game(self):
        manager = ConnectionManager()
        ws = FakeWebSocket()
        await manager.connect(ws, "game-1", "user-1")

        manager.disconnect("game-1", "user-1")

        assert "game-1" not in manager._connections
        assert manager.get_connected_users("game-1") == []

    async def test_disconnect_unknown_game_is_noop(self):
        manager = ConnectionManager()
        manager.disconnect("ghost-game", "user-1")
        assert manager.get_connected_users("ghost-game") == []

    async def test_send_to_game_no_connections(self):
        manager = ConnectionManager()
        await manager.send_to_game("ghost-game", "event", {"x": 1})
        # no error raised

    async def test_send_to_game_delivers_all(self):
        manager = ConnectionManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        await manager.connect(ws1, "game-1", "user-1")
        await manager.connect(ws2, "game-1", "user-2")

        await manager.send_to_game("game-1", "event", {"x": 1})

        assert ws1.sent == [{"event": "event", "data": {"x": 1}}]
        assert ws2.sent == [{"event": "event", "data": {"x": 1}}]

    async def test_send_to_game_drops_failed_connections(self):
        manager = ConnectionManager()
        ws_ok = FakeWebSocket()
        ws_bad = FakeWebSocket(fail_send=True)
        await manager.connect(ws_ok, "game-1", "user-1")
        await manager.connect(ws_bad, "game-1", "user-2")

        await manager.send_to_game("game-1", "event", {"x": 1})

        assert ws_ok.sent == [{"event": "event", "data": {"x": 1}}]
        assert manager.get_connected_users("game-1") == ["user-1"]

    async def test_broadcast_to_game_delegates(self):
        manager = ConnectionManager()
        ws = FakeWebSocket()
        await manager.connect(ws, "game-1", "user-1")

        await manager.broadcast_to_game("game-1", "event", {"x": 1})

        assert ws.sent == [{"event": "event", "data": {"x": 1}}]