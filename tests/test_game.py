import pytest

TEST_USER_ID = "user_test_123"
OTHER_USER_ID = "user_test_456"


async def _create_two_player_game(
    client, auth_headers, other_auth_headers, **kwargs
):
    create_response = await client.post(
        "/api/v1/games",
        json=kwargs or {},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    game_id = create_response.json()["id"]
    code = create_response.json()["code"]

    join_response = await client.post(
        "/api/v1/games/join",
        json={"code": code},
        headers=other_auth_headers,
    )
    assert join_response.status_code == 200
    return game_id, code


async def _start_two_player_game(client, auth_headers, other_auth_headers, **kwargs):
    game_id, _ = await _create_two_player_game(
        client, auth_headers, other_auth_headers, **kwargs
    )
    start_response = await client.post(
        f"/api/v1/games/{game_id}/start", headers=auth_headers
    )
    assert start_response.status_code == 200
    return game_id, start_response.json()


async def _get_hand(client, game_id, headers):
    response = await client.get(
        f"/api/v1/games/{game_id}/players/me/cards", headers=headers
    )
    assert response.status_code == 200
    return response.json()["cards"]


class TestHealth:
    """Test health check endpoint."""

    async def test_health_check(self, client):
        """Test that health check returns OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestGameEndpoints:
    """Test game-related API endpoints."""

    async def test_create_game(self, client, auth_headers):
        """Test creating a new game."""
        response = await client.post(
            "/api/v1/games",
            json={"max_players": 8, "score_to_win": 10},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "code" in data
        assert data["max_players"] == 8
        assert data["score_to_win"] == 10
        assert data["status"] == "waiting"

    async def test_create_game_default_values(self, client, auth_headers):
        """Test creating a game with default values."""
        response = await client.post(
            "/api/v1/games",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["max_players"] == 8
        assert data["score_to_win"] == 7

    async def test_create_game_invalid_max_players(self, client, auth_headers):
        """Test creating a game with invalid max_players."""
        response = await client.post(
            "/api/v1/games",
            json={"max_players": 1},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    async def test_get_game_by_id(self, client, auth_headers):
        """Test getting a game by ID."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/games/{game_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id

    async def test_get_game_not_found(self, client, auth_headers):
        """Test getting a non-existent game."""
        response = await client.get(
            "/api/v1/games/non-existent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_game_by_code(self, client, auth_headers):
        """Test getting a game by code."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_code = create_response.json()["code"]

        response = await client.get(
            f"/api/v1/games/by-code/{game_code}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == game_code

    async def test_get_game_by_code_not_found(self, client, auth_headers):
        """Test getting a game by invalid code."""
        response = await client.get(
            "/api/v1/games/by-code/000000",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGamePlayers:
    """Test game player-related endpoints."""

    async def test_get_game_players(self, client, auth_headers):
        """Test getting players in a game."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/games/{game_id}/players",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1  # Creator is automatically a player

    async def test_join_game(self, client, auth_headers, other_auth_headers):
        """Test joining a game by code with a second player."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_code = create_response.json()["code"]

        response = await client.post(
            "/api/v1/games/join",
            json={"code": game_code},
            headers=other_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == game_code

        players = await client.get(
            f"/api/v1/games/{response.json()['id']}/players",
            headers=auth_headers,
        )
        assert len(players.json()) == 2

    async def test_join_game_duplicate_player(self, client, auth_headers):
        """Test that the host cannot join its own game again."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_code = create_response.json()["code"]

        response = await client.post(
            "/api/v1/games/join",
            json={"code": game_code},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_join_game_invalid_code(self, client, auth_headers, other_auth_headers):
        """Test joining a game with invalid code."""
        response = await client.post(
            "/api/v1/games/join",
            json={"code": "000000"},
            headers=other_auth_headers,
        )
        assert response.status_code == 400

    async def test_leave_game(self, client, auth_headers):
        """Test leaving a game."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.post(
            f"/api/v1/games/{game_id}/leave",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_leave_game_reassigns_host(
        self, client, auth_headers, other_auth_headers
    ):
        """Test that hosting is handed over when the host leaves."""
        game_id, _ = await _create_two_player_game(
            client, auth_headers, other_auth_headers, max_players=4, score_to_win=5
        )

        leave_response = await client.post(
            f"/api/v1/games/{game_id}/leave",
            headers=auth_headers,
        )
        assert leave_response.status_code == 200

        game_response = await client.get(
            f"/api/v1/games/{game_id}",
            headers=other_auth_headers,
        )
        assert game_response.status_code == 200
        assert game_response.json()["host_player_id"] != TEST_USER_ID

    async def test_leave_started_game_preserves_record(
        self, client, auth_headers, other_auth_headers
    ):
        """Test that a started game is not deleted when the last player leaves."""
        game_id, _ = await _start_two_player_game(
            client, auth_headers, other_auth_headers, max_players=4, score_to_win=5
        )

        for headers in (auth_headers, other_auth_headers):
            response = await client.post(
                f"/api/v1/games/{game_id}/leave",
                headers=headers,
            )
            assert response.status_code == 200

        game_response = await client.get(
            f"/api/v1/games/{game_id}",
            headers=auth_headers,
        )
        assert game_response.status_code == 200
        assert game_response.json()["status"] == "playing"

    async def test_leave_empty_lobby_deletes_game(
        self, client, auth_headers
    ):
        """Test that an abandoned waiting lobby is deleted."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.post(
            f"/api/v1/games/{game_id}/leave",
            headers=auth_headers,
        )
        assert response.status_code == 200

        game_response = await client.get(
            f"/api/v1/games/{game_id}",
            headers=auth_headers,
        )
        assert game_response.status_code == 404


class TestRounds:
    """Test round-related endpoints."""

    async def test_start_game(self, client, auth_headers, other_auth_headers):
        """Test starting a game (creating first round)."""
        _, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        assert "id" in round_data
        assert round_data["round_number"] == 1
        assert "question_card_id" in round_data
        assert round_data["status"] == "submitting"

    async def test_start_game_host_only(self, client, auth_headers, other_auth_headers):
        """Test that only the host can start the game."""
        game_id, _ = await _create_two_player_game(
            client, auth_headers, other_auth_headers, max_players=4, score_to_win=5
        )
        response = await client.post(
            f"/api/v1/games/{game_id}/start",
            headers=other_auth_headers,
        )
        assert response.status_code == 400

    async def test_start_game_needs_two_players(self, client, auth_headers):
        """Test that a single player cannot start a game."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_get_last_round(self, client, auth_headers, other_auth_headers):
        """Test getting the last round of a game."""
        game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]

        response = await client.get(
            f"/api/v1/games/{game_id}/rounds/last",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == round_id

    async def test_get_last_round_no_rounds(self, client, auth_headers):
        """Test getting last round when no rounds exist."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/games/{game_id}/rounds/last",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestRoundAnswers:
    """Test round answer-related endpoints."""

    async def test_submit_answer(self, client, auth_headers, other_auth_headers):
        """Test submitting an answer to a round as a non-judge player."""
        game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        submitter_headers = (
            other_auth_headers if judge_user_id == TEST_USER_ID else auth_headers
        )
        hand = await _get_hand(client, game_id, submitter_headers)
        cards_used = hand[:2]

        response = await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": cards_used},
            headers=submitter_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cards_used"] == cards_used

    async def test_submit_answer_materializes_final_text(
        self, client, auth_headers, other_auth_headers
    ):
        """Test that final_text is composed from the question and used cards."""
        game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        submitter_headers = (
            other_auth_headers if judge_user_id == TEST_USER_ID else auth_headers
        )
        hand = await _get_hand(client, game_id, submitter_headers)
        # Fill every blank of the drawn question (questions have 1-3 blanks)
        # so the composed final_text never keeps a leftover placeholder.
        question = await client.get(
            f"/api/v1/cards/questions/{round_data['question_card_id']}"
        )
        question_data = question.json()
        cards_used = hand[: question_data["blank_count"]]

        response = await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": cards_used},
            headers=submitter_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["final_text"]
        assert "_____" not in data["final_text"]

    async def test_submit_answer_rejects_foreign_cards(
        self, client, auth_headers, other_auth_headers
    ):
        """Test that a player cannot submit cards they do not hold."""
        _game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        submitter_headers = (
            other_auth_headers if judge_user_id == TEST_USER_ID else auth_headers
        )

        response = await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": ["not-a-real-card"]},
            headers=submitter_headers,
        )
        assert response.status_code == 400

    async def test_judge_cannot_submit_answer(
        self, client, auth_headers, other_auth_headers
    ):
        """Test that the judge cannot submit an answer."""
        _, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        judge_headers = (
            auth_headers if judge_user_id == TEST_USER_ID else other_auth_headers
        )

        response = await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": ["card1"]},
            headers=judge_headers,
        )
        assert response.status_code == 400

    async def test_get_round_answers(self, client, auth_headers, other_auth_headers):
        """Test getting answers for a round."""
        game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        submitter_headers = (
            other_auth_headers if judge_user_id == TEST_USER_ID else auth_headers
        )
        hand = await _get_hand(client, game_id, submitter_headers)

        await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": hand[:1]},
            headers=submitter_headers,
        )

        response = await client.get(
            f"/api/v1/games/rounds/{round_id}/answers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    async def test_select_winner(self, client, auth_headers, other_auth_headers):
        """Test selecting a winner for a round."""
        game_id, round_data = await _start_two_player_game(
            client,
            auth_headers,
            other_auth_headers,
            max_players=4,
            score_to_win=5,
        )
        round_id = round_data["id"]
        judge_user_id = round_data["judge_user_id"]
        judge_headers = (
            auth_headers if judge_user_id == TEST_USER_ID else other_auth_headers
        )
        submitter_headers = (
            other_auth_headers if judge_user_id == TEST_USER_ID else auth_headers
        )
        hand = await _get_hand(client, game_id, submitter_headers)

        answer_response = await client.post(
            f"/api/v1/games/rounds/{round_id}/answers",
            json={"cards_used": hand[:1]},
            headers=submitter_headers,
        )
        assert answer_response.status_code == 201
        answer_id = answer_response.json()["id"]

        response = await client.post(
            f"/api/v1/games/rounds/{round_id}/winner",
            json={"winning_answer_id": answer_id},
            headers=judge_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_winner"] is True


class TestPlayerCards:
    """Test player card-related endpoints."""

    async def test_get_my_cards(self, client, auth_headers):
        """Test getting my cards in a game."""
        create_response = await client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/games/{game_id}/players/me/cards",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)