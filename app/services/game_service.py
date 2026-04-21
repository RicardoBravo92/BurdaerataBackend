from __future__ import annotations

from random import randint
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.player_card import PlayerCard
from app.models.round import Round
from app.models.round_answer import RoundAnswer
from app.models.user import User
from app.repositories.game_repository import game_repository
from app.repositories.user_repository import ensure_clerk_user
from app.core.ws_manager import ws_manager
from app.services.card_service import card_service



def _player_to_dict(
    p: GamePlayer, host_id: str, profile: User | None
) -> dict[str, Any]:
    return {
        "id": p.id,
        "game_id": p.game_id,
        "user_id": p.user_id,
        "score": p.score or 0,
        "is_host": p.user_id == host_id,
        "is_ready": False,
        "avatar_url": profile.avatar_url if profile else "",
        "profile": {"full_name": profile.full_name} if profile else None,
    }


def _answer_to_dict(a: RoundAnswer, profile: User | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": a.id,
        "round_id": a.round_id,
        "user_id": a.user_id,
        "cards_used": list(a.cards_used or []),
        "final_text": a.final_text or "",
        "is_winner": bool(a.is_winner),
    }
    if a.created_at:
        out["created_at"] = a.created_at.isoformat()
    if profile:
        out["user"] = {"full_name": profile.full_name}
    return out


async def _load_users_map(db: AsyncSession, user_ids: set[str]) -> dict[str, User]:
    if not user_ids:
        return {}
    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {u.id: u for u in result.scalars().all()}


class GameService:
    async def _deal_cards(
        self, db: AsyncSession, game_id: str, players: list[GamePlayer]
    ) -> None:
        n = len(players)
        need = 10 * n
        if need > card_service.answer_count:
            raise ValueError("Not enough answer cards in pool")
        picked = card_service.get_random_answers(need)
        picked_ids = [a.id for a in picked]
        for i, p in enumerate(players):
            chunk = picked_ids[i * 10 : (i + 1) * 10]
            row = PlayerCard(user_id=p.user_id, game_id=game_id, cards=list(chunk))
            await game_repository.add(db, row)

    async def create_game(
        self,
        db: AsyncSession,
        user_id: str,
        max_players: int = 8,
        score_to_win: int = 7,
    ) -> Game:
        await ensure_clerk_user(db, user_id)
        code = ""
        for _ in range(10):
            candidate = str(randint(100000, 999999))
            if not await game_repository.code_exists(db, candidate):
                code = candidate
                break
        if not code:
            raise ValueError("Failed to generate unique game code")

        gid = str(uuid4())
        game = Game(
            id=gid,
            code=code,
            host_player_id=user_id,
            status="waiting",
            max_players=max_players,
            score_to_win=score_to_win,
            public=True,
        )
        await game_repository.add(db, game)
        gp = GamePlayer(id=str(uuid4()), game_id=gid, user_id=user_id, score=0)
        await game_repository.add(db, gp)
        await ws_manager.send_to_game(gid, "game_created", game)
        return game

    async def get_game_by_id(
        self, db: AsyncSession, game_id: str
    ) -> Game:
        game = await game_repository.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Game not found")
        return game

    async def get_game_by_code(
        self, db: AsyncSession, code: str
    ) -> Game:
        game = await game_repository.get_game_by_code(db, code)
        if not game:
            raise ValueError("Game not found")
        return game

    async def join_game(
        self, db: AsyncSession, user_id: str, code_or_game_id: str
    ) -> Game:
        await ensure_clerk_user(db, user_id)
        game = await game_repository.resolve_game(db, code_or_game_id)
        if not game:
            raise ValueError("Game not found")

        if await game_repository.get_player_row(db, game.id, user_id):
            raise ValueError("You are already in this game")

        n = await game_repository.count_players(db, game.id)
        if n >= game.max_players:
            raise ValueError("Game is full")

        gp = GamePlayer(id=str(uuid4()), game_id=game.id, user_id=user_id, score=0)
        await game_repository.add(db, gp)
        await db.commit()
        await ws_manager.send_to_game(
            game.id, "player_joined", {"user_id": user_id, "game": game}
        )
        return game

    async def get_game_players(
        self, db: AsyncSession, game_id: str
    ) -> list[GamePlayer]:
        game = await game_repository.get_game_by_id(db, game_id)
        if not game:
            return []
        players = list(await game_repository.list_players(db, game_id))
        uids = {p.user_id for p in players}
        users = await _load_users_map(db, uids)
        return [
            _player_to_dict(p, game.host_player_id, users.get(p.user_id))
            for p in players
        ]

    async def start_game(
        self, db: AsyncSession, user_id: str, game_id: str
    ) -> Round:
        game = await game_repository.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Game not found")
        if game.status != "waiting":
            raise ValueError("Game has already started")

        players = list(await game_repository.list_players(db, game_id))
        if len(players) < 2:
            raise ValueError("Need at least 2 players to start the game")
        if not any(p.user_id == user_id for p in players):
            raise ValueError("You are not in this game")

        first_judge = players[0].user_id
        question = card_service.get_random_question()
        round = Round(
            id=str(uuid4()),
            game_id=game_id,
            round_number=1,
            question_card_id=question.id,
            judge_user_id=first_judge,
            status="submitting",
            winning_answer_id=None,
        )
        await game_repository.add(db, round)
        game.status = "playing"
        db.add(game)
        await db.flush()
        
        await self._deal_cards(db, game_id, players)
        await db.commit()
        
        await ws_manager.send_to_game(game_id, "game_started", {"round": round})
        await ws_manager.send_to_game(game_id, "new_round", round)
        return round

    async def get_last_round(
        self, db: AsyncSession, game_id: str
    ) -> Round | None:
        round = await game_repository.get_last_round(db, game_id)
        if not round:
            return None
        return round

    async def start_next_round(
        self, db: AsyncSession, user_id: str, game_id: str
    ) -> dict[str, Any]:
        game = await game_repository.get_game_by_id(db, game_id)
        if not game:
            raise ValueError("Game not found")
        if game.status != "playing":
            raise ValueError("Game is not in playing state")

        players = list(await game_repository.list_players(db, game_id))
        if not any(p.user_id == user_id for p in players):
            raise ValueError("You are not in this game")

        last = await game_repository.get_last_round(db, game_id)
        if not last:
            raise ValueError("No previous round found")
        
        if last.status != "finished":
            raise ValueError("Current round must be finished before starting the next one")

        next_num = last.round_number + 1
        judge_idx = (next_num - 1) % len(players)
        question = card_service.get_random_question()
        next_round = Round(
            id=str(uuid4()),
            game_id=game_id,
            round_number=next_num,
            question_card_id=question.id,
            judge_user_id=players[judge_idx].user_id,
            status="submitting",
            winning_answer_id=None,
        )
        await game_repository.add(db, next_round)
        await db.commit()
        
        await ws_manager.send_to_game(game_id, "new_round", next_round)
        return next_round

    async def create_round_answer(
        self, db: AsyncSession, round_id: str, user_id: str, cards_used: list[str]
    ) -> dict[str, Any]:
        round = await game_repository.get_round(db, round_id)
        if not round:
            raise ValueError("Round not found")
        if round.judge_user_id == user_id:
            raise ValueError("Judge cannot submit answers")
        
        existing = await game_repository.get_answer_by_user(db, round_id, user_id)
        if existing:
            raise ValueError("You have already submitted an answer for this round")

        clean = [c for c in cards_used if c]
        ans = RoundAnswer(
            id=str(uuid4()),
            round_id=round_id,
            user_id=user_id,
            cards_used=clean,
            final_text="",
            is_winner=False,
        )
        await game_repository.add(db, ans)

        row = await game_repository.get_player_cards_row(db, round.game_id, user_id)
        if row:
            current = list(row.cards or [])
            for c in clean:
                if c in current:
                    current.remove(c)
            avail = [
                card_service.get_answer_by_id(aid).id
                for aid in current
                if card_service.get_answer_by_id(aid)
            ]
            used_ids = set(current)
            new_cards = []
            for _ in range(len(clean)):
                card = card_service.get_random_answer()
                if card.id not in used_ids:
                    new_cards.append(card.id)
                    used_ids.add(card.id)
                if len(new_cards) >= len(clean):
                    break
            current.extend(new_cards)
            row.cards = current
            db.add(row)
            await db.flush()

        await db.commit()
        prof = await db.get(User, user_id)
        answer_data = _answer_to_dict(ans, prof)
        await ws_manager.send_to_game(round.game_id, "answer_submitted", answer_data)
        return answer_data

    async def get_round_answers(
        self, db: AsyncSession, round_id: str
    ) -> list[dict[str, Any]]:
        answers = list(await game_repository.list_answers(db, round_id))
        uids = {a.user_id for a in answers}
        users = await _load_users_map(db, uids)
        return [_answer_to_dict(a, users.get(a.user_id)) for a in answers]

    async def select_winner(
        self,
        db: AsyncSession,
        user_id: str,
        round_id: str,
        winning_answer_id: str,
    ) -> dict[str, Any]:
        round = await game_repository.get_round(db, round_id)
        if not round:
            raise ValueError("Round not found")
        if round.judge_user_id != user_id:
            raise ValueError("Only the judge can select winners")
        if round.status == "finished":
            raise ValueError("This round is already finished")

        players_count = await game_repository.count_players(db, round.game_id)
        answers = list(await game_repository.list_answers(db, round_id))
        if len(answers) < players_count - 1:
            raise ValueError("Cannot select a winner until all players have submitted their answers")

        answer = await game_repository.get_answer(db, winning_answer_id)
        if not answer or answer.round_id != round.id:
            raise ValueError("Winning answer not found")

        answer.is_winner = True
        round.winning_answer_id = winning_answer_id
        round.status = "finished"
        db.add(answer)
        db.add(round)
        await db.flush()

        gplayer = await game_repository.get_player_row(db, round.game_id, answer.user_id)
        if not gplayer:
            raise ValueError("Player not found in game")

        gplayer.score = (gplayer.score or 0) + 1
        db.add(gplayer)
        await db.flush()
        
        await db.commit()

        game = await game_repository.get_game_by_id(db, round.game_id)
        if (
            game
            and game.score_to_win is not None
            and gplayer.score >= game.score_to_win
        ):
            game.status = "finished"
            db.add(game)
            await db.flush()
            await ws_manager.send_to_game(
                game.id,
                "game_finished",
                {
                    "winner_user_id": answer.user_id,
                    "winner_score": gplayer.score,
                },
            )

        await ws_manager.send_to_game(
            round.game_id,
            "round_finished",
            {
                "round_id": round.id,
                "winning_answer_id": winning_answer_id,
            },
        )
        return {"success": True}

    async def get_player_cards(
        self, db: AsyncSession, game_id: str, user_id: str
    ) -> dict[str, Any]:
        row = await game_repository.get_player_cards_row(db, game_id, user_id)
        cards = list(row.cards) if row and row.cards else []
        print(f"[DEBUG] Fetching cards for user {user_id} in game {game_id}: {cards}")
        return {"game_id": game_id, "user_id": user_id, "cards": cards}

    async def update_player_cards(
        self, db: AsyncSession, game_id: str, user_id: str, cards: list[str]
    ) -> dict[str, Any]:
        clean = [c for c in cards if c]
        row = await game_repository.get_player_cards_row(db, game_id, user_id)
        if row:
            row.cards = clean
            db.add(row)
        else:
            row = PlayerCard(user_id=user_id, game_id=game_id, cards=clean)
            db.add(row)
        await db.flush()
        await db.refresh(row)
        return {"game_id": game_id, "user_id": user_id, "cards": clean}

    async def leave_game(
        self, db: AsyncSession, user_id: str, game_id: str
    ) -> dict[str, Any]:
        await game_repository.delete_player(db, game_id, user_id)
        await game_repository.delete_player_cards(db, game_id, user_id)
        await db.commit()
        remaining = await game_repository.count_players(db, game_id)
        await ws_manager.send_to_game(
            game_id, "player_left", {"user_id": user_id, "remaining": remaining}
        )
        if remaining == 0:
            await game_repository.delete_game_cascade(db, game_id)
            await ws_manager.send_to_game(game_id, "game_deleted", {"game_id": game_id})
        return {"success": True}


game_service = GameService()
