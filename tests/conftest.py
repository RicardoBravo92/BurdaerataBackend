import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.chat_message import ChatMessage
from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.player_card import PlayerCard
from app.models.round import Round
from app.models.round_answer import RoundAnswer
from app.models.user import User

TEST_USER_ID = "user_test_123"
OTHER_USER_ID = "user_test_456"


def _run(awaitable):
    """Run a coroutine on a fresh event loop (no loop is running at fixture setup)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(awaitable)
    finally:
        loop.close()


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    _run(_create_tables())
    yield engine
    _run(engine.dispose())


@pytest.fixture
def mock_clerk_auth(monkeypatch):
    """Mock Clerk authentication, deriving the user id from the Authorization header."""

    async def _fake_auth(request, options=None):
        token = (
            request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        ) or TEST_USER_ID
        state = MagicMock()
        state.is_signed_in = True
        state.payload = {"sub": token}
        state.message = None
        return state

    monkeypatch.setattr("app.api.dependencies.authenticate_request_async", _fake_auth)


@pytest.fixture
def mock_clerk_user_api(monkeypatch):
    """Mock Clerk user lookups so services never touch the real Clerk API."""

    async def _fake_get_async(user_id="", **kwargs):
        return SimpleNamespace(
            first_name="Test",
            last_name="User",
            email_addresses=[SimpleNamespace(email_address=f"{user_id}@example.com")],
            image_url="",
        )

    monkeypatch.setattr(
        "app.repositories.user_repository.clerk_client.users.get_async",
        _fake_get_async,
    )


@pytest.fixture
def mock_db_session(test_engine):
    """Override get_db with a session backed by the in-memory engine."""

    async def _get_session():
        async with AsyncSession(test_engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return _get_session


@pytest.fixture
def client(mock_clerk_auth, mock_clerk_user_api, mock_db_session, monkeypatch):
    """Create a test client with mocked dependencies."""
    from app.core.database import get_db

    app.dependency_overrides[get_db] = mock_db_session

    # Avoid touching the configured (production) database during the app lifespan.
    async def _noop_init_db():
        return None

    monkeypatch.setattr("app.main.init_db", _noop_init_db)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Headers for the host / creator user."""
    return {"Authorization": f"Bearer {TEST_USER_ID}"}


@pytest.fixture
def other_auth_headers():
    """Headers for a second, distinct player."""
    return {"Authorization": f"Bearer {OTHER_USER_ID}"}