from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import game as game_endpoints
from app.models.game import Game
from app.models.round import Round
from app.models.round_answer import RoundAnswer


def _game(**overrides):
    values = dict(
        id="game-1",
        code="123456",
        host_player_id="user-1",
        status="waiting",
        max_players=8,
        score_to_win=7,
        public=True,
    )
    values.update(overrides)
    return Game(**values)


def _round(**overrides):
    values = dict(
        id="round-1",
        game_id="game-1",
        round_number=1,
        question_card_id="q1",
        judge_user_id="user-3",
        status="submitting",
        winning_answer_id=None,
    )
    values.update(overrides)
    return Round(**values)


def _answer(**overrides):
    values = dict(
        id="ans-1",
        round_id="round-1",
        user_id="user-2",
        cards_used=["a1"],
        final_text="",
        is_winner=False,
    )
    values.update(overrides)
    return RoundAnswer(**values)


@pytest.fixture
def mock_service(monkeypatch):
    service = AsyncMock()
    monkeypatch.setattr(game_endpoints, "game_service", service)
    return service


class TestCreateGame:
    async def test_success(self, mock_service):
        game = _game(max_players=4, score_to_win=5)
        mock_service.create_game.return_value = game

        result = await game_endpoints.create_game(
            game_endpoints.CreateGameBody(max_players=4, score_to_win=5),
            "user-1",
            AsyncMock(),
        )

        assert result is game

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.create_game.side_effect = ValueError("boom")

        with pytest.raises(HTTPException) as exc:
            await game_endpoints.create_game(
                game_endpoints.CreateGameBody(), "user-1", AsyncMock()
            )

        assert exc.value.status_code == 400
        assert "boom" in exc.value.detail


class TestGetGameByCode:
    async def test_success(self, mock_service):
        game = _game()
        mock_service.get_game_by_code.return_value = game
        result = await game_endpoints.get_game_by_code("123456", "user-1", AsyncMock())
        assert result is game

    async def test_not_found(self, mock_service):
        mock_service.get_game_by_code.return_value = None
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.get_game_by_code("123456", "user-1", AsyncMock())
        assert exc.value.status_code == 404


class TestGetGame:
    async def test_success(self, mock_service):
        game = _game()
        mock_service.get_game_by_id.return_value = game
        result = await game_endpoints.get_game("game-1", "user-1", AsyncMock())
        assert result is game

    async def test_not_found(self, mock_service):
        mock_service.get_game_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.get_game("game-1", "user-1", AsyncMock())
        assert exc.value.status_code == 404


class TestJoinGame:
    async def test_success(self, mock_service):
        game = _game()
        mock_service.join_game.return_value = game
        result = await game_endpoints.join_game(
            game_endpoints.JoinGameBody(code="123456"), "user-2", AsyncMock()
        )
        assert result is game

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.join_game.side_effect = ValueError("Game is full")
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.join_game(
                game_endpoints.JoinGameBody(code="123456"), "user-2", AsyncMock()
            )
        assert exc.value.status_code == 400


class TestGetGamePlayers:
    async def test_success(self, mock_service):
        mock_service.get_game_players.return_value = [{"user_id": "user-1"}]
        result = await game_endpoints.get_game_players("game-1", "user-1", AsyncMock())
        assert result == [{"user_id": "user-1"}]


class TestStartGame:
    async def test_success(self, mock_service):
        round = _round()
        mock_service.start_game.return_value = round
        result = await game_endpoints.start_game("game-1", "user-1", AsyncMock())
        assert result is round

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.start_game.side_effect = ValueError("Need at least 2 players")
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.start_game("game-1", "user-1", AsyncMock())
        assert exc.value.status_code == 400


class TestGetLastRound:
    async def test_success(self, mock_service):
        round = _round()
        mock_service.get_last_round.return_value = round
        result = await game_endpoints.get_last_round("game-1", "user-1", AsyncMock())
        assert result is round

    async def test_not_found(self, mock_service):
        mock_service.get_last_round.return_value = None
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.get_last_round("game-1", "user-1", AsyncMock())
        assert exc.value.status_code == 404


class TestStartNextRound:
    async def test_success(self, mock_service):
        round = _round(round_number=2)
        mock_service.start_next_round.return_value = round
        result = await game_endpoints.start_next_round("game-1", "user-1", AsyncMock())
        assert result is round

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.start_next_round.side_effect = ValueError("not playing")
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.start_next_round("game-1", "user-1", AsyncMock())
        assert exc.value.status_code == 400


class TestGetRoundAnswers:
    async def test_success(self, mock_service):
        mock_service.get_round_answers.return_value = [_answer()]
        result = await game_endpoints.get_round_answers("round-1", "user-1", AsyncMock())
        assert len(result) == 1
        assert result[0].id == "ans-1"


class TestCreateRoundAnswer:
    async def test_success(self, mock_service):
        answer = _answer()
        mock_service.create_round_answer.return_value = answer
        result = await game_endpoints.create_round_answer(
            "round-1",
            game_endpoints.CreateRoundAnswerBody(cards_used=["a1"]),
            "user-2",
            AsyncMock(),
        )
        assert result is answer

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.create_round_answer.side_effect = ValueError("already submitted")
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.create_round_answer(
                "round-1",
                game_endpoints.CreateRoundAnswerBody(cards_used=["a1"]),
                "user-2",
                AsyncMock(),
            )
        assert exc.value.status_code == 400


class TestSelectWinner:
    async def test_success(self, mock_service):
        answer = _answer(is_winner=True)
        mock_service.select_winner.return_value = answer
        result = await game_endpoints.select_winner(
            "round-1",
            game_endpoints.SelectWinnerBody(winning_answer_id="ans-1"),
            "user-3",
            AsyncMock(),
        )
        assert result is answer

    async def test_error_mapped_to_400(self, mock_service):
        mock_service.select_winner.side_effect = ValueError("Only the judge")
        with pytest.raises(HTTPException) as exc:
            await game_endpoints.select_winner(
                "round-1",
                game_endpoints.SelectWinnerBody(winning_answer_id="ans-1"),
                "user-3",
                AsyncMock(),
            )
        assert exc.value.status_code == 400


class TestGetMyCards:
    async def test_success(self, mock_service):
        mock_service.get_player_cards.return_value = {"cards": ["a1"]}
        result = await game_endpoints.get_my_cards("game-1", "user-1", AsyncMock())
        assert result == {"cards": ["a1"]}


class TestLeaveGame:
    async def test_success(self, mock_service):
        mock_service.leave_game.return_value = {"success": True}
        result = await game_endpoints.leave_game("game-1", "user-1", AsyncMock())
        assert result == {"success": True}