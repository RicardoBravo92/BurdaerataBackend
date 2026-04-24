import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient


class TestHealth:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test that health check returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestGameEndpoints:
    """Test game-related API endpoints."""

    def test_create_game(self, client, auth_headers):
        """Test creating a new game."""
        response = client.post(
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

    def test_create_game_default_values(self, client, auth_headers):
        """Test creating a game with default values."""
        response = client.post(
            "/api/v1/games",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["max_players"] == 8
        assert data["score_to_win"] == 7

    def test_create_game_invalid_max_players(self, client, auth_headers):
        """Test creating a game with invalid max_players."""
        response = client.post(
            "/api/v1/games",
            json={"max_players": 1},
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    def test_get_game_by_id(self, client, auth_headers):
        """Test getting a game by ID."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.get(f"/api/v1/games/{game_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id

    def test_get_game_not_found(self, client, auth_headers):
        """Test getting a non-existent game."""
        response = client.get(
            "/api/v1/games/non-existent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_game_by_code(self, client, auth_headers):
        """Test getting a game by code."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_code = create_response.json()["code"]

        response = client.get(
            f"/api/v1/games/by-code/{game_code}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == game_code

    def test_get_game_by_code_not_found(self, client, auth_headers):
        """Test getting a game by invalid code."""
        response = client.get(
            "/api/v1/games/by-code/000000",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGamePlayers:
    """Test game player-related endpoints."""

    def test_get_game_players(self, client, auth_headers):
        """Test getting players in a game."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/games/{game_id}/players",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1  # Creator is automatically a player

    def test_join_game(self, client, auth_headers):
        """Test joining a game by code."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_code = create_response.json()["code"]

        response = client.post(
            "/api/v1/games/join",
            json={"code": game_code},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == game_code

    def test_join_game_invalid_code(self, client, auth_headers):
        """Test joining a game with invalid code."""
        response = client.post(
            "/api/v1/games/join",
            json={"code": "000000"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_leave_game(self, client, auth_headers):
        """Test leaving a game."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/games/{game_id}/leave",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestRounds:
    """Test round-related endpoints."""

    def test_start_game(self, client, auth_headers):
        """Test starting a game (creating first round)."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["round_number"] == 1
        assert "question_card_id" in data

    def test_get_last_round(self, client, auth_headers):
        """Test getting the last round of a game."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        start_response = client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        round_id = start_response.json()["id"]

        response = client.get(
            f"/api/v1/games/{game_id}/rounds/last",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == round_id

    def test_get_last_round_no_rounds(self, client, auth_headers):
        """Test getting last round when no rounds exist."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/games/{game_id}/rounds/last",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestRoundAnswers:
    """Test round answer-related endpoints."""

    def test_submit_answer(self, client, auth_headers):
        """Test submitting an answer to a round."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        start_response = client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        round_id = start_response.json()["id"]

        response = client.post(
            f"/api/v1/rounds/{round_id}/answers",
            json={"cards_used": ["card1", "card2"]},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cards_used"] == ["card1", "card2"]

    def test_get_round_answers(self, client, auth_headers):
        """Test getting answers for a round."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        start_response = client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        round_id = start_response.json()["id"]

        client.post(
            f"/api/v1/rounds/{round_id}/answers",
            json={"cards_used": ["card1"]},
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/rounds/{round_id}/answers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_select_winner(self, client, auth_headers):
        """Test selecting a winner for a round."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        start_response = client.post(
            f"/api/v1/games/{game_id}/start",
            headers=auth_headers,
        )
        round_id = start_response.json()["id"]

        answer_response = client.post(
            f"/api/v1/rounds/{round_id}/answers",
            json={"cards_used": ["card1"]},
            headers=auth_headers,
        )
        answer_id = answer_response.json()["id"]

        response = client.post(
            f"/api/v1/rounds/{round_id}/winner",
            json={"winning_answer_id": answer_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_winner"] is True


class TestPlayerCards:
    """Test player card-related endpoints."""

    def test_get_my_cards(self, client, auth_headers):
        """Test getting my cards in a game."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/games/{game_id}/players/me/cards",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "cards" in data
        assert isinstance(data["cards"], list)

    def test_update_my_cards(self, client, auth_headers):
        """Test updating my cards in a game."""
        create_response = client.post(
            "/api/v1/games",
            json={"max_players": 4, "score_to_win": 5},
            headers=auth_headers,
        )
        game_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/games/{game_id}/players/me/cards",
            json={"cards": ["card1", "card2", "card3"]},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cards"] == ["card1", "card2", "card3"]
