from datetime import datetime
from types import SimpleNamespace

import pytest

from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.player_card import PlayerCard
from app.models.round import Round
from app.models.round_answer import RoundAnswer
from app.models.user import User
from app.services.game_service import _answer_to_dict, _player_to_dict, game_service


def _game(**overrides):
    values = {
        "id": "game-1",
        "code": "123456",
        "host_player_id": "user-1",
        "status": "waiting",
        "max_players": 8,
        "score_to_win": 7,
        "public": True,
    }
    values.update(overrides)
    return Game(**values)


def _player(user_id, game_id="game-1", score=0):
    return GamePlayer(id=f"gp-{user_id}", game_id=game_id, user_id=user_id, score=score)


def _round(**overrides):
    values = {
        "id": "round-1",
        "game_id": "game-1",
        "round_number": 1,
        "question_card_id": "q1",
        "judge_user_id": "user-3",
        "status": "submitting",
        "winning_answer_id": None,
    }
    values.update(overrides)
    return Round(**values)


def _answer(**overrides):
    values = {
        "id": "ans-1",
        "round_id": "round-1",
        "user_id": "user-2",
        "cards_used": ["a1"],
        "final_text": "",
        "is_winner": False,
    }
    values.update(overrides)
    return RoundAnswer(**values)


def _hand(cards):
    return PlayerCard(id=1, game_id="game-1", user_id="user-2", cards=cards)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class TestPlayerToDict:
    def test_is_host(self, fake_profile):
        player = _player("user-1")
        out = _player_to_dict(player, host_id="user-1", profile=fake_profile)
        assert out["is_host"] is True
        assert out["score"] == 0
        assert out["is_ready"] is False
        assert out["avatar_url"] == "avatar-url"
        assert out["profile"] == {"full_name": "Test User"}

    def test_not_host_no_profile(self):
        player = _player("user-2")
        out = _player_to_dict(player, host_id="user-1", profile=None)
        assert out["is_host"] is False
        assert out["avatar_url"] == ""
        assert out["profile"] is None


class TestAnswerToDict:
    def test_with_profile(self, fake_profile):
        answer = _answer()
        out = _answer_to_dict(answer, fake_profile)
        assert out["id"] == "ans-1"
        assert out["user_id"] == "user-2"
        assert out["cards_used"] == ["a1"]
        assert out["is_winner"] is False
        assert out["user"] == {"full_name": "Test User"}

    def test_without_profile(self):
        out = _answer_to_dict(_answer(), None)
        assert "user" not in out
        assert out["final_text"] == ""

    def test_with_created_at(self):
        a = SimpleNamespace(
            id="ans-1",
            round_id="round-1",
            user_id="user-2",
            cards_used=["a1"],
            final_text="",
            is_winner=False,
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        out = _answer_to_dict(a, None)
        assert out["created_at"] == "2026-01-01T12:00:00"


# ---------------------------------------------------------------------------
# create_game
# ---------------------------------------------------------------------------


class TestCreateGame:
    async def test_success(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk, monkeypatch
    ):
        monkeypatch.setattr("secrets.token_hex", lambda n: "123456")
        mock_game_repo.code_exists.return_value = False

        game = await game_service.create_game(fake_session, "user-1", 4, 5)

        assert isinstance(game, Game)
        assert game.code == "123456"
        assert game.status == "waiting"
        assert game.host_player_id == "user-1"
        assert game.max_players == 4
        assert game.score_to_win == 5
        mock_game_repo.add.assert_awaited()
        game_obj = mock_game_repo.add.await_args_list[0].args[1]
        player_obj = mock_game_repo.add.await_args_list[1].args[1]
        assert isinstance(game_obj, Game)
        assert isinstance(player_obj, GamePlayer)
        assert player_obj.user_id == "user-1"
        mock_ws.send_to_game.assert_awaited_once()
        assert mock_ws.send_to_game.await_args.args[1] == "game_created"

    async def test_default_values(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk, monkeypatch
    ):
        monkeypatch.setattr("secrets.token_hex", lambda n: "111222")
        mock_game_repo.code_exists.return_value = False
        game = await game_service.create_game(fake_session, "user-1")
        assert game.max_players == 8
        assert game.score_to_win == 7

    async def test_retries_on_collision(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk, monkeypatch
    ):
        codes = iter(["111111", "222222"])
        monkeypatch.setattr("secrets.token_hex", lambda n: next(codes))
        mock_game_repo.code_exists.side_effect = [True, False]

        game = await game_service.create_game(fake_session, "user-1")

        assert game.code == "222222"

    async def test_fails_without_unique_code(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk, monkeypatch
    ):
        monkeypatch.setattr("secrets.token_hex", lambda n: "999999")
        mock_game_repo.code_exists.return_value = True

        with pytest.raises(ValueError, match="unique game code"):
            await game_service.create_game(fake_session, "user-1")

        mock_game_repo.add.assert_not_awaited()


# ---------------------------------------------------------------------------
# join_game
# ---------------------------------------------------------------------------


class TestJoinGame:
    async def test_game_not_found(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk
    ):
        mock_game_repo.resolve_game.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.join_game(fake_session, "user-2", "123456")

    async def test_game_already_started(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk
    ):
        mock_game_repo.resolve_game.return_value = _game(status="playing")
        from app.services.exceptions import GameAlreadyStartedError

        with pytest.raises(GameAlreadyStartedError):
            await game_service.join_game(fake_session, "user-2", "123456")

    async def test_already_in_game(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk
    ):
        mock_game_repo.resolve_game.return_value = _game()
        mock_game_repo.get_player_row.return_value = _player("user-1")
        from app.services.exceptions import PlayerAlreadyInGameError

        with pytest.raises(PlayerAlreadyInGameError):
            await game_service.join_game(fake_session, "user-1", "123456")

    async def test_game_is_full(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk
    ):
        game = _game(max_players=2)
        mock_game_repo.resolve_game.return_value = game
        mock_game_repo.get_player_row.return_value = None
        mock_game_repo.count_players.return_value = 2
        from app.services.exceptions import GameFullError

        with pytest.raises(GameFullError):
            await game_service.join_game(fake_session, "user-2", "123456")

    async def test_success(
        self, fake_session, mock_game_repo, mock_ws, mock_cards, mock_clerk
    ):
        game = _game(max_players=4)
        mock_game_repo.resolve_game.return_value = game
        mock_game_repo.get_player_row.return_value = None
        mock_game_repo.count_players.return_value = 1

        result = await game_service.join_game(fake_session, "user-2", "123456")

        assert result is game
        added_player = mock_game_repo.add.await_args.args[1]
        assert isinstance(added_player, GamePlayer)
        assert added_player.user_id == "user-2"
        mock_game_repo.add.assert_awaited()
        assert mock_ws.send_to_game.await_args.args[1] == "player_joined"


# ---------------------------------------------------------------------------
# get_game_by_id / get_game_by_code
# ---------------------------------------------------------------------------


class TestGetGame:
    async def test_get_game_by_id(self, fake_session, mock_game_repo):
        game = _game()
        mock_game_repo.get_game_by_id.return_value = game
        assert await game_service.get_game_by_id(fake_session, "game-1") is game

    async def test_get_game_by_code(self, fake_session, mock_game_repo):
        game = _game()
        mock_game_repo.get_game_by_code.return_value = game
        assert await game_service.get_game_by_code(fake_session, "123456") is game


# ---------------------------------------------------------------------------
# get_game_players
# ---------------------------------------------------------------------------


class TestGetGamePlayers:
    async def test_game_not_found(self, fake_session, mock_game_repo, mock_cards):
        mock_game_repo.get_game_by_id.return_value = None
        assert await game_service.get_game_players(fake_session, "game-1") == []

    async def test_no_players(self, fake_session, mock_game_repo, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game()
        mock_game_repo.list_players.return_value = []
        assert await game_service.get_game_players(fake_session, "game-1") == []

    async def test_success(self, fake_session, mock_game_repo, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game(host_player_id="user-1")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        fake_session.result_rows = [
            User(id="user-1", full_name="Host Name", avatar_url="a1"),
            User(id="user-2", full_name="Player Two", avatar_url="a2"),
        ]

        out = await game_service.get_game_players(fake_session, "game-1")

        assert len(out) == 2
        assert out[0]["is_host"] is True
        assert out[0]["profile"] == {"full_name": "Host Name"}
        assert out[0]["avatar_url"] == "a1"
        assert out[1]["is_host"] is False


# ---------------------------------------------------------------------------
# start_game
# ---------------------------------------------------------------------------


class TestStartGame:
    async def test_game_not_found(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.start_game(fake_session, "user-1", "game-1")

    async def test_not_waiting(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        from app.services.exceptions import GameAlreadyStartedError

        with pytest.raises(GameAlreadyStartedError):
            await game_service.start_game(fake_session, "user-1", "game-1")

    async def test_needs_two_players(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = _game()
        mock_game_repo.list_players.return_value = [_player("user-1")]
        from app.services.exceptions import NotEnoughPlayersError

        with pytest.raises(NotEnoughPlayersError):
            await game_service.start_game(fake_session, "user-1", "game-1")

    async def test_not_in_game(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game()
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        from app.services.exceptions import NotInGameError

        with pytest.raises(NotInGameError):
            await game_service.start_game(fake_session, "outsider", "game-1")

    async def test_host_only(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game(host_player_id="user-1")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        from app.services.exceptions import NotGameHostError

        with pytest.raises(NotGameHostError):
            await game_service.start_game(fake_session, "user-2", "game-1")

    async def test_success(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        players = [_player("user-1"), _player("user-2")]
        mock_game_repo.get_game_by_id.return_value = _game()
        mock_game_repo.list_players.return_value = players

        round = await game_service.start_game(fake_session, "user-1", "game-1")

        assert isinstance(round, Round)
        assert round.round_number == 1
        assert round.status == "submitting"
        assert round.judge_user_id == "user-1"
        assert round.question_card_id == "q1"
        # 10 cards dealt per player
        dealt = [
            c.args[1]
            for c in mock_game_repo.add.await_args_list
            if isinstance(c.args[1], PlayerCard)
        ]
        assert len(dealt) == 2
        for cards_row in dealt:
            assert len(cards_row.cards) == 10
        events = [c.args[1] for c in mock_ws.send_to_game.await_args_list]
        assert "game_started" in events
        assert "new_round" in events

    async def test_fails_when_pool_too_small(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_cards.answer_count = 5
        mock_game_repo.get_game_by_id.return_value = _game()
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        with pytest.raises(ValueError, match="Not enough answer cards"):
            await game_service.start_game(fake_session, "user-1", "game-1")


# ---------------------------------------------------------------------------
# get_last_round
# ---------------------------------------------------------------------------


class TestGetLastRound:
    async def test_success(self, fake_session, mock_game_repo):
        round = _round()
        mock_game_repo.get_last_round.return_value = round
        result = await game_service.get_last_round(fake_session, "game-1")
        assert result is round

    async def test_not_found(self, fake_session, mock_game_repo):
        mock_game_repo.get_last_round.return_value = None
        assert await game_service.get_last_round(fake_session, "game-1") is None


# ---------------------------------------------------------------------------
# start_next_round
# ---------------------------------------------------------------------------


class TestStartNextRound:
    async def test_game_not_found(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.start_next_round(fake_session, "user-1", "game-1")

    async def test_game_not_playing(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = _game(status="waiting")
        from app.services.exceptions import GameNotInProgressError

        with pytest.raises(GameNotInProgressError):
            await game_service.start_next_round(fake_session, "user-1", "game-1")

    async def test_not_in_game(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        from app.services.exceptions import NotInGameError

        with pytest.raises(NotInGameError):
            await game_service.start_next_round(fake_session, "outsider", "game-1")

    async def test_host_only(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        from app.services.exceptions import NotGameHostError

        with pytest.raises(NotGameHostError):
            await game_service.start_next_round(fake_session, "user-2", "game-1")

    async def test_no_previous_round(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        mock_game_repo.get_last_round.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.start_next_round(fake_session, "user-1", "game-1")

    async def test_last_round_not_finished(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = [
            _player("user-1"),
            _player("user-2"),
        ]
        mock_game_repo.get_last_round.return_value = _round(status="submitting")
        from app.services.exceptions import RoundAlreadyFinishedError

        with pytest.raises(RoundAlreadyFinishedError):
            await game_service.start_next_round(fake_session, "user-1", "game-1")

    async def test_success_with_judge_rotation(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        players = [_player("user-1"), _player("user-2")]
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = players
        mock_game_repo.get_last_round.return_value = _round(
            round_number=1, status="finished"
        )

        next_round = await game_service.start_next_round(
            fake_session, "user-1", "game-1"
        )

        assert next_round.round_number == 2
        # judge_idx = (2 - 1) % 2 = 1 -> second player
        assert next_round.judge_user_id == "user-2"
        assert mock_ws.send_to_game.await_args.args[1] == "new_round"


# ---------------------------------------------------------------------------
# create_round_answer
# ---------------------------------------------------------------------------


class TestCreateRoundAnswer:
    async def test_round_not_found(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a1"]
            )

    async def test_round_not_submitting(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round(status="finished")
        from app.services.exceptions import RoundNotAcceptingAnswersError

        with pytest.raises(RoundNotAcceptingAnswersError):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a1"]
            )

    async def test_judge_cannot_submit(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round(judge_user_id="user-2")
        from app.services.exceptions import JudgeCannotSubmitError

        with pytest.raises(JudgeCannotSubmitError):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a1"]
            )

    async def test_duplicate_answer(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.get_answer_by_user.return_value = _answer()
        from app.services.exceptions import AlreadySubmittedError

        with pytest.raises(AlreadySubmittedError):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a1"]
            )

    async def test_empty_cards(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.get_answer_by_user.return_value = None
        from app.services.exceptions import InvalidCardsError

        with pytest.raises(InvalidCardsError, match="at least one card"):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["", None]
            )

    async def test_foreign_cards_rejected(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.get_answer_by_user.return_value = None
        mock_game_repo.get_player_cards_row.return_value = _hand(["a1", "a2"])
        from app.services.exceptions import InvalidCardsError

        with pytest.raises(InvalidCardsError, match="do not have"):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a9"]
            )

    async def test_success(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        row = _hand(["a1", "a2"])
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.get_answer_by_user.return_value = None
        mock_game_repo.get_player_cards_row.return_value = row

        answer_data = await game_service.create_round_answer(
            fake_session, "round-1", "user-2", ["a1"]
        )

        assert answer_data["final_text"] == "Composed text"
        assert answer_data["cards_used"] == ["a1"]
        assert row.cards == ["a2", "new-a1"]
        added = mock_game_repo.add.await_args.args[1]
        assert isinstance(added, RoundAnswer)
        assert added.cards_used == ["a1"]
        assert mock_ws.send_to_game.await_args.args[1] == "answer_submitted"

    async def test_without_existing_hand_rejected(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        # With no hand row, `current` is empty, so any card is rejected. The
        # `else` branch that creates a new PlayerCard is dead code in practice.
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.get_answer_by_user.return_value = None
        mock_game_repo.get_player_cards_row.return_value = None
        from app.services.exceptions import InvalidCardsError

        with pytest.raises(InvalidCardsError, match="do not have"):
            await game_service.create_round_answer(
                fake_session, "round-1", "user-2", ["a1"]
            )


# ---------------------------------------------------------------------------
# get_round_answers
# ---------------------------------------------------------------------------


class TestGetRoundAnswers:
    async def test_success(self, fake_session, mock_game_repo):
        mock_game_repo.list_answers.return_value = [_answer(user_id="user-2")]
        fake_session.result_rows = [
            User(id="user-2", full_name="Player Two", avatar_url="")
        ]

        out = await game_service.get_round_answers(fake_session, "round-1")

        assert len(out) == 1
        assert out[0]["id"] == "ans-1"
        assert out[0]["user"] == {"full_name": "Player Two"}

    async def test_no_answers(self, fake_session, mock_game_repo):
        mock_game_repo.list_answers.return_value = []
        assert await game_service.get_round_answers(fake_session, "round-1") == []


# ---------------------------------------------------------------------------
# select_winner
# ---------------------------------------------------------------------------


class TestSelectWinner:
    async def test_round_not_found(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError):
            await game_service.select_winner(fake_session, "user-1", "round-1", "ans-1")

    async def test_judge_only(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        mock_game_repo.get_round.return_value = _round(judge_user_id="user-1")
        from app.services.exceptions import JudgeCannotSubmitError

        with pytest.raises(JudgeCannotSubmitError):
            await game_service.select_winner(fake_session, "user-2", "round-1", "ans-1")

    async def test_round_already_finished(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round(status="finished")
        from app.services.exceptions import RoundAlreadyFinishedError

        with pytest.raises(RoundAlreadyFinishedError):
            await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

    async def test_not_all_players_submitted(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.count_players.return_value = 3
        mock_game_repo.list_answers.return_value = [_answer()]
        from app.services.exceptions import AllPlayersMustSubmitError

        with pytest.raises(AllPlayersMustSubmitError):
            await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

    async def test_answer_not_in_round(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.count_players.return_value = 2
        mock_game_repo.list_answers.return_value = [_answer()]
        mock_game_repo.get_answer.return_value = None
        from app.services.exceptions import GameNotFoundError

        with pytest.raises(GameNotFoundError, match="Winning answer not found"):
            await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

    async def test_judge_cannot_win(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.count_players.return_value = 2
        mock_game_repo.list_answers.return_value = [_answer()]
        mock_game_repo.get_answer.return_value = _answer(user_id="user-3")
        from app.services.exceptions import JudgeCannotWinError

        with pytest.raises(JudgeCannotWinError):
            await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

    async def test_player_not_found_in_game(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        answer = _answer()
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.count_players.return_value = 2
        mock_game_repo.list_answers.return_value = [answer]
        mock_game_repo.get_answer.return_value = answer
        mock_game_repo.get_player_row.return_value = None
        from app.services.exceptions import PlayerNotFoundError

        with pytest.raises(PlayerNotFoundError):
            await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

    async def test_success(self, fake_session, mock_game_repo, mock_ws, mock_cards):
        answer = _answer()
        round = _round()
        gplayer = _player("user-2")
        game = _game(score_to_win=5)
        mock_game_repo.get_round.return_value = round
        mock_game_repo.count_players.return_value = 2
        mock_game_repo.list_answers.return_value = [answer]
        mock_game_repo.get_answer.return_value = answer
        mock_game_repo.get_player_row.return_value = gplayer
        mock_game_repo.get_game_by_id.return_value = game

        result = await game_service.select_winner(
            fake_session, "user-3", "round-1", "ans-1"
        )

        assert result["is_winner"] is True
        assert answer.is_winner is True
        assert round.status == "finished"
        assert round.winning_answer_id == "ans-1"
        assert gplayer.score == 1
        # No score_to_win reached -> game not finished, status unchanged
        assert game.status == "waiting"
        events = [c.args[1] for c in mock_ws.send_to_game.await_args_list]
        assert "round_finished" in events
        assert "game_finished" not in events

    async def test_game_finished_when_score_reached(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        answer = _answer()
        gplayer = _player("user-2")
        game = _game(score_to_win=1)
        mock_game_repo.get_round.return_value = _round()
        mock_game_repo.count_players.return_value = 2
        mock_game_repo.list_answers.return_value = [answer]
        mock_game_repo.get_answer.return_value = answer
        mock_game_repo.get_player_row.return_value = gplayer
        mock_game_repo.get_game_by_id.return_value = game

        await game_service.select_winner(fake_session, "user-3", "round-1", "ans-1")

        assert gplayer.score == 1
        assert game.status == "finished"
        events = [c.args[1] for c in mock_ws.send_to_game.await_args_list]
        assert "game_finished" in events


# ---------------------------------------------------------------------------
# get_player_cards
# ---------------------------------------------------------------------------


class TestGetPlayerCards:
    async def test_success(self, fake_session, mock_game_repo):
        mock_game_repo.get_player_cards_row.return_value = _hand(["a1", "a2"])
        out = await game_service.get_player_cards(fake_session, "game-1", "user-2")
        assert out == {"game_id": "game-1", "user_id": "user-2", "cards": ["a1", "a2"]}

    async def test_no_hand(self, fake_session, mock_game_repo):
        mock_game_repo.get_player_cards_row.return_value = None
        out = await game_service.get_player_cards(fake_session, "game-1", "user-2")
        assert out == {"game_id": "game-1", "user_id": "user-2", "cards": []}


# ---------------------------------------------------------------------------
# leave_game
# ---------------------------------------------------------------------------


class TestLeaveGame:
    async def test_empty_waiting_lobby_deleted(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        game = _game(status="waiting")
        mock_game_repo.get_last_round.return_value = None
        mock_game_repo.get_game_by_id.return_value = game
        mock_game_repo.list_players.return_value = []

        result = await game_service.leave_game(fake_session, "user-1", "game-1")

        assert result == {"success": True}
        mock_game_repo.delete_player_cards.assert_awaited()
        mock_game_repo.delete_game_cascade.assert_awaited_once()
        events = [c.args[1] for c in mock_ws.send_to_game.await_args_list]
        assert "player_left" in events
        assert "game_deleted" in events

    async def test_started_game_preserved(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        game = _game(status="playing")
        mock_game_repo.get_last_round.return_value = None
        mock_game_repo.get_game_by_id.return_value = game
        mock_game_repo.list_players.return_value = []

        await game_service.leave_game(fake_session, "user-1", "game-1")

        mock_game_repo.delete_game_cascade.assert_not_awaited()

    async def test_host_handover(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        game = _game(status="playing", host_player_id="user-1")
        mock_game_repo.get_last_round.return_value = None
        mock_game_repo.get_game_by_id.return_value = game
        mock_game_repo.list_players.return_value = [_player("user-2")]

        await game_service.leave_game(fake_session, "user-1", "game-1")

        assert game.host_player_id == "user-2"

    async def test_judge_reassignment_avoids_self_vote(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        last_round = _round(status="submitting", judge_user_id="user-1")
        players = [_player("user-2"), _player("user-3")]
        mock_game_repo.get_last_round.return_value = last_round
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = players
        # user-2 already answered, so it is skipped in favour of user-3
        mock_game_repo.list_answers.return_value = [_answer(user_id="user-2")]

        await game_service.leave_game(fake_session, "user-1", "game-1")

        assert last_round.judge_user_id == "user-3"

    async def test_judge_reassignment_fallback_to_all_players(
        self, fake_session, mock_game_repo, mock_ws, mock_cards
    ):
        last_round = _round(status="submitting", judge_user_id="user-1")
        players = [_player("user-2"), _player("user-3")]
        mock_game_repo.get_last_round.return_value = last_round
        mock_game_repo.get_game_by_id.return_value = _game(status="playing")
        mock_game_repo.list_players.return_value = players
        mock_game_repo.list_answers.return_value = []

        await game_service.leave_game(fake_session, "user-1", "game-1")

        assert last_round.judge_user_id == "user-2"
