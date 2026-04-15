from typing import Any, Optional, Sequence

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.game_player import GamePlayer
from app.models.player_card import PlayerCard
from app.models.round import Round
from app.models.round_answer import RoundAnswer


class GameRepository:
    async def get_game_by_id(self, db: AsyncSession, game_id: str) -> Optional[Game]:
        return await db.get(Game, game_id)

    async def get_game_by_code(self, db: AsyncSession, code: str) -> Optional[Game]:
        result = await db.execute(select(Game).where(Game.code == code))
        return result.scalar_one_or_none()

    async def resolve_game(self, db: AsyncSession, code_or_id: str) -> Optional[Game]:
        g = await self.get_game_by_id(db, code_or_id)
        if g:
            return g
        return await self.get_game_by_code(db, code_or_id)

    async def code_exists(self, db: AsyncSession, code: str) -> bool:
        g = await self.get_game_by_code(db, code)
        return g is not None

    async def add(self, db: AsyncSession, obj: Any) -> None:
        db.add(obj)
        await db.flush()
        await db.refresh(obj)

    async def list_players(self, db: AsyncSession, game_id: str) -> Sequence[GamePlayer]:
        result = await db.execute(select(GamePlayer).where(GamePlayer.game_id == game_id))
        return result.scalars().all()

    async def count_players(self, db: AsyncSession, game_id: str) -> int:
        result = await db.execute(
            select(func.count()).select_from(GamePlayer).where(GamePlayer.game_id == game_id)
        )
        return int(result.scalar_one())

    async def get_player_row(
        self, db: AsyncSession, game_id: str, user_id: str
    ) -> Optional[GamePlayer]:
        result = await db.execute(
            select(GamePlayer).where(
                GamePlayer.game_id == game_id,
                GamePlayer.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_player(self, db: AsyncSession, game_id: str, user_id: str) -> None:
        await db.execute(
            delete(GamePlayer).where(
                GamePlayer.game_id == game_id,
                GamePlayer.user_id == user_id,
            )
        )

    async def delete_player_cards(self, db: AsyncSession, game_id: str, user_id: str) -> None:
        await db.execute(
            delete(PlayerCard).where(
                PlayerCard.game_id == game_id,
                PlayerCard.user_id == user_id,
            )
        )

    async def get_last_round(self, db: AsyncSession, game_id: str) -> Optional[Round]:
        result = await db.execute(
            select(Round)
            .where(Round.game_id == game_id)
            .order_by(desc(Round.round_number))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_round(self, db: AsyncSession, round_id: str) -> Optional[Round]:
        return await db.get(Round, round_id)

    async def list_answers(self, db: AsyncSession, round_id: str) -> Sequence[RoundAnswer]:
        result = await db.execute(
            select(RoundAnswer)
            .where(RoundAnswer.round_id == round_id)
            .order_by(RoundAnswer.id)
        )
        return result.scalars().all()

    async def get_answer(self, db: AsyncSession, answer_id: str) -> Optional[RoundAnswer]:
        return await db.get(RoundAnswer, answer_id)

    async def get_answer_by_user(
        self, db: AsyncSession, round_id: str, user_id: str
    ) -> Optional[RoundAnswer]:
        result = await db.execute(
            select(RoundAnswer).where(
                RoundAnswer.round_id == round_id,
                RoundAnswer.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_player_cards_row(
        self, db: AsyncSession, game_id: str, user_id: str
    ) -> Optional[PlayerCard]:
        result = await db.execute(
            select(PlayerCard).where(
                PlayerCard.game_id == game_id,
                PlayerCard.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_game_cascade(self, db: AsyncSession, game_id: str) -> None:
        round_ids_result = await db.execute(select(Round.id).where(Round.game_id == game_id))
        round_ids = [row[0] for row in round_ids_result.all()]
        if round_ids:
            await db.execute(delete(RoundAnswer).where(RoundAnswer.round_id.in_(round_ids)))
        await db.execute(delete(Round).where(Round.game_id == game_id))
        await db.execute(delete(PlayerCard).where(PlayerCard.game_id == game_id))
        await db.execute(delete(GamePlayer).where(GamePlayer.game_id == game_id))
        await db.execute(delete(Game).where(Game.id == game_id))


game_repository = GameRepository()
