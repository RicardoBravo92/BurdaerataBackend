from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import game_service as game_service_module


class FakeSession:
    """Minimal fake AsyncSession for service unit tests."""

    def __init__(self):
        self.added = []
        self.deleted = []
        self.by_id = {}
        self.fetched = {}
        self.result_rows = []

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None):
            self.by_id[obj.id] = obj

    def delete(self, obj):
        self.deleted.append(obj)

    async def execute(self, stmt):
        rows = self.result_rows
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: rows))

    async def flush(self):
        return None

    async def commit(self):
        return None

    async def get(self, model, id):
        return self.fetched.get(id, self.by_id.get(id))

    async def refresh(self, obj):
        # For testing, just ensure the object is in by_id
        if getattr(obj, "id", None):
            self.by_id[obj.id] = obj
        return None


@pytest.fixture
def fake_session():
    return FakeSession()


class FakeQuestion:
    def __init__(self, id="q1", text="A question with a blank _____", blank_count=1):
        self.id = id
        self.text = text
        self.blank_count = blank_count


class FakeAnswer:
    def __init__(self, id="a1", text="an answer"):
        self.id = id
        self.text = text


@pytest.fixture
def mock_game_repo(monkeypatch):
    repo = AsyncMock()
    monkeypatch.setattr(game_service_module, "game_repository", repo)
    return repo


@pytest.fixture
def mock_ws(monkeypatch):
    ws = AsyncMock()
    monkeypatch.setattr(game_service_module, "ws_manager", ws)
    return ws


@pytest.fixture
def mock_cards(monkeypatch):
    cards = MagicMock()
    cards.answer_count = 20
    cards.get_random_question.return_value = FakeQuestion()
    cards.get_random_answers.return_value = [
        FakeAnswer(id=f"a{i}", text=f"answer {i}") for i in range(20)
    ]
    cards.get_random_answer.return_value = FakeAnswer(id="new-a1", text="new answer")
    cards.compose_answer_text.return_value = "Composed text"
    monkeypatch.setattr(game_service_module, "card_service", cards)
    return cards


@pytest.fixture
def mock_clerk(monkeypatch):
    async def _noop(db, user_id):
        return None

    monkeypatch.setattr(game_service_module, "ensure_clerk_user", _noop)


@pytest.fixture
def fake_profile():
    return SimpleNamespace(
        id="user-1",
        full_name="Test User",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        avatar_url="avatar-url",
    )