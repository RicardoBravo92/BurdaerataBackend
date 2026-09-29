from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocketDisconnect
from clerk_backend_api.security.types import TokenVerificationErrorReason

from app.api.v1.endpoints import websocket as ws_endpoints
from app.models.user import User


class FakeWebSocket:
    def __init__(self, messages=None):
        self.messages = list(messages or [])
        self.sent = []
        self.closed = []

    async def close(self, code, reason):
        self.closed.append((code, reason))

    async def receive_json(self):
        if self.messages:
            return self.messages.pop(0)
        raise WebSocketDisconnect()

    async def send_json(self, data):
        self.sent.append(data)


class FakeSessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class ChatSession:
    def __init__(self, user=None):
        self.user = user
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None

    async def refresh(self, obj):
        obj.id = "msg-1"

    async def get(self, model, user_id):
        return self.user


class FakeWSManager:
    def __init__(self):
        self.connect = AsyncMock()
        self.broadcast_to_game = AsyncMock()
        self.disconnect = MagicMock()


class TestAuthorizedParties:
    def test_parses(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints, "get_settings", lambda: SimpleNamespace(AUTHORIZED_PARTIES=" https://a.com ")
        )
        assert ws_endpoints._authorized_parties() == ["https://a.com"]

    def test_empty(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints, "get_settings", lambda: SimpleNamespace(AUTHORIZED_PARTIES="  , ")
        )
        assert ws_endpoints._authorized_parties() == []


class TestAuthenticateToken:
    async def test_no_secret(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="", AUTHORIZED_PARTIES=""),
        )
        assert await ws_endpoints._authenticate_token("tok") is None

    async def test_verification_error(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _boom(*args, **kwargs):
            raise ws_endpoints.TokenVerificationError(
                TokenVerificationErrorReason.TOKEN_INVALID
            )

        monkeypatch.setattr(ws_endpoints, "verify_token_async", _boom)
        assert await ws_endpoints._authenticate_token("tok") is None

    async def test_invalid_sub(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _verify(*args, **kwargs):
            return {"sub": 42}

        monkeypatch.setattr(ws_endpoints, "verify_token_async", _verify)
        assert await ws_endpoints._authenticate_token("tok") is None

    async def test_success(self, monkeypatch):
        monkeypatch.setattr(
            ws_endpoints,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _verify(*args, **kwargs):
            return {"sub": "user-1"}

        monkeypatch.setattr(ws_endpoints, "verify_token_async", _verify)
        assert await ws_endpoints._authenticate_token("tok") == "user-1"


class TestWebsocketEndpoint:
    async def test_invalid_token(self, monkeypatch):
        async def _auth(token):
            return None

        monkeypatch.setattr(ws_endpoints, "_authenticate_token", _auth)
        ws_manager = FakeWSManager()
        monkeypatch.setattr(ws_endpoints, "ws_manager", ws_manager)
        ws = FakeWebSocket()

        await ws_endpoints.websocket_endpoint(ws, "game-1", token="tok")

        assert ws.closed == [(4001, "Invalid token")]
        ws_manager.connect.assert_not_awaited()

    async def test_not_a_player(self, monkeypatch):
        async def _auth(token):
            return "user-1"

        monkeypatch.setattr(ws_endpoints, "_authenticate_token", _auth)
        repo = AsyncMock()
        repo.get_player_row.return_value = None
        monkeypatch.setattr(ws_endpoints, "game_repository", repo)
        monkeypatch.setattr(
            ws_endpoints, "AsyncSessionLocal", lambda: FakeSessionCM(ChatSession())
        )
        ws_manager = FakeWSManager()
        monkeypatch.setattr(ws_endpoints, "ws_manager", ws_manager)
        ws = FakeWebSocket()

        await ws_endpoints.websocket_endpoint(ws, "game-1", token="tok")

        assert ws.closed == [(4003, "Not a player in this game")]
        ws_manager.connect.assert_not_awaited()

    async def test_chat_and_ack_flow(self, monkeypatch):
        async def _auth(token):
            return "user-1"

        monkeypatch.setattr(ws_endpoints, "_authenticate_token", _auth)
        repo = AsyncMock()
        repo.get_player_row.return_value = MagicMock()
        monkeypatch.setattr(ws_endpoints, "game_repository", repo)
        monkeypatch.setattr(
            ws_endpoints,
            "AsyncSessionLocal",
            lambda: FakeSessionCM(ChatSession(user=User(id="user-1", full_name="Ana"))),
        )
        ws_manager = FakeWSManager()
        monkeypatch.setattr(ws_endpoints, "ws_manager", ws_manager)

        ws = FakeWebSocket(
            messages=[
                {"event": "send_chat_message", "data": {"text": "  hola mundo  "}},
                {"event": "other_event", "data": {"x": 1}},
            ]
        )

        await ws_endpoints.websocket_endpoint(ws, "game-1", token="tok")

        ws_manager.connect.assert_awaited_once()
        ws_manager.broadcast_to_game.assert_awaited_once()
        game_id, event, payload = ws_manager.broadcast_to_game.await_args.args
        assert game_id == "game-1"
        assert event == "new_chat_message"
        assert payload["text"] == "hola mundo"
        assert payload["user"] == {"id": "user-1", "full_name": "Ana"}
        # the "other" event got an ack echoing the full message
        assert ws.sent == [
            {"event": "ack", "data": {"event": "other_event", "data": {"x": 1}}}
        ]
        ws_manager.disconnect.assert_called_once()

    async def test_unknown_user_name(self, monkeypatch):
        async def _auth(token):
            return "user-1"

        monkeypatch.setattr(ws_endpoints, "_authenticate_token", _auth)
        repo = AsyncMock()
        repo.get_player_row.return_value = MagicMock()
        monkeypatch.setattr(ws_endpoints, "game_repository", repo)
        monkeypatch.setattr(
            ws_endpoints, "AsyncSessionLocal", lambda: FakeSessionCM(ChatSession(user=None))
        )
        ws_manager = FakeWSManager()
        monkeypatch.setattr(ws_endpoints, "ws_manager", ws_manager)

        ws = FakeWebSocket(
            messages=[{"event": "send_chat_message", "data": {"text": "  hola  "}}]
        )

        await ws_endpoints.websocket_endpoint(ws, "game-1", token="tok")

        _, event, payload = ws_manager.broadcast_to_game.await_args.args
        assert event == "new_chat_message"
        assert payload["user"] == {"id": "user-1", "full_name": "Unknown player"}

    async def test_invalid_text_ignored(self, monkeypatch):
        async def _auth(token):
            return "user-1"

        monkeypatch.setattr(ws_endpoints, "_authenticate_token", _auth)
        repo = AsyncMock()
        repo.get_player_row.return_value = MagicMock()
        monkeypatch.setattr(ws_endpoints, "game_repository", repo)
        monkeypatch.setattr(
            ws_endpoints, "AsyncSessionLocal", lambda: FakeSessionCM(ChatSession())
        )
        ws_manager = FakeWSManager()
        monkeypatch.setattr(ws_endpoints, "ws_manager", ws_manager)

        ws = FakeWebSocket(
            messages=[
                {"event": "send_chat_message", "data": {"text": 123}},
                {"event": "send_chat_message", "data": {"text": "   "}},
            ]
        )

        await ws_endpoints.websocket_endpoint(ws, "game-1", token="tok")

        ws_manager.broadcast_to_game.assert_not_awaited()
        ws_manager.disconnect.assert_called_once()