import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.models.user import User
from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.round import Round
from app.models.round_answer import RoundAnswer
from app.models.player_card import PlayerCard
from app.models.chat_message import ChatMessage
from app.models.question_card import QuestionCard
from app.models.answer_card import AnswerCard


TEST_USER_ID = "user_test_123"
TEST_TOKEN = "test_token"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
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
def mock_db_session(test_engine):
    """Create an async session for testing."""

    async def _get_session() -> AsyncSession:
        async with AsyncSession(test_engine) as session:
            yield session

    return _get_session


@pytest.fixture
def mock_clerk_auth():
    """Mock Clerk authentication to return a test user ID."""
    with patch("app.api.dependencies.authenticate_request_async") as mock_auth:
        mock_state = MagicMock()
        mock_state.is_signed_in = True
        mock_state.payload = {"sub": TEST_USER_ID}
        mock_state.message = None
        mock_auth.return_value = mock_state
        yield mock_auth


@pytest.fixture
def client(mock_clerk_auth, mock_db_session):
    """Create a test client with mocked dependencies."""
    from app.core.database import get_db

    app.dependency_overrides[get_db] = mock_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return authorization headers for tests."""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}
