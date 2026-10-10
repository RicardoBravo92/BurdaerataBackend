import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.api.dependencies import get_clerk_user_id
from app.core.database import get_db
from app.models.chat_message import ChatMessage
from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.player_card import PlayerCard
from app.models.round import Round
from app.models.round_answer import RoundAnswer
from app.models.user import User

TEST_USER_ID = "user_test_123"
OTHER_USER_ID = "user_test_456"


import pytest_asyncio

@pytest_asyncio.fixture
async def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine
    await engine.dispose()


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
async def mock_db_session(test_engine):
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


# Override the authentication dependency directly for all tests
async def _override_get_clerk_user_id(request):
    """Override that extracts user ID from Authorization header."""
    token = (
        request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    ) or TEST_USER_ID
    return token


@pytest.fixture
async def client(mock_clerk_user_api, mock_db_session, monkeypatch):
    """Create an async test client with mocked dependencies."""
    from app.core.database import get_db

    # Override database dependency
    app.dependency_overrides[get_db] = mock_db_session
    
    # Override authentication dependency - bypasses Clerk entirely
    app.dependency_overrides[get_clerk_user_id] = _override_get_clerk_user_id

    # Disable rate limiting for tests
    app.state.limiter = None
    
    # Also patch the module-level limiter to no-op
    import app.core.rate_limit as rate_limit_module
    from slowapi import Limiter
    noop_limiter = Limiter(key_func=lambda r: "test", default_limits=[])
    noop_limiter._limit = lambda limit: lambda f: f
    rate_limit_module.limiter = noop_limiter

    # Avoid touching the configured (production) database during the app lifespan.
    async def _noop_init_db():
        return None

    monkeypatch.setattr("app.main.init_db", _noop_init_db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


TEST_USER_ID = "user_test_123"
OTHER_USER_ID = "user_test_456"


@pytest.fixture
def auth_headers():
    """Headers for the host / creator user."""
    return {"Authorization": f"Bearer {TEST_USER_ID}"}


@pytest.fixture
def other_auth_headers():
    """Headers for a second, distinct player."""
    return {"Authorization": f"Bearer {OTHER_USER_ID}"}