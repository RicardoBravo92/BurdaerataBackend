from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ClerkUserId
from app.core.database import get_db
from app.services.game_service import game_service

router = APIRouter()


class CreateGameBody(BaseModel):
    max_players: int = Field(default=8, ge=2)
    score_to_win: int = Field(default=7, ge=1)


class JoinGameBody(BaseModel):
    code: str


class CardsBody(BaseModel):
    cards: list[str]


class CreateRoundAnswerBody(BaseModel):
    cards_used: list[str]


class SelectWinnerBody(BaseModel):
    winning_answer_id: str


def _as_http_error(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_game(
    body: CreateGameBody,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.create_game(
            db, user_id, body.max_players, body.score_to_win
        )
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/by-code/{code}")
async def get_game_by_code(
    code: str, _user_id: ClerkUserId, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    game = await game_service.get_game_by_code(db, code)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.get("/{game_id}")
async def get_game(
    game_id: str, _user_id: ClerkUserId, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    game = await game_service.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.post("/join")
async def join_game(
    body: JoinGameBody,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.join_game(db, user_id, body.code)
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/{game_id}/players")
async def get_game_players(
    game_id: str, _user_id: ClerkUserId, db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    return await game_service.get_game_players(db, game_id)


@router.post("/{game_id}/start")
async def start_game(
    game_id: str,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.start_game(db, user_id, game_id)
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/{game_id}/rounds/last")
async def get_last_round(
    game_id: str, _user_id: ClerkUserId, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    last_round = await game_service.get_last_round(db, game_id)
    if not last_round:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rounds found")
    return last_round


@router.post("/{game_id}/rounds/next")
async def start_next_round(
    game_id: str,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.start_next_round(db, user_id, game_id)
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/rounds/{round_id}/answers")
async def get_round_answers(
    round_id: str, _user_id: ClerkUserId, db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    return await game_service.get_round_answers(db, round_id)


@router.post("/rounds/{round_id}/answers", status_code=status.HTTP_201_CREATED)
async def create_round_answer(
    round_id: str,
    body: CreateRoundAnswerBody,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.create_round_answer(
            db, round_id, user_id, body.cards_used
        )
    except Exception as error:
        raise _as_http_error(error) from error


@router.post("/rounds/{round_id}/winner")
async def select_winner(
    round_id: str,
    body: SelectWinnerBody,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await game_service.select_winner(
            db, user_id, round_id, body.winning_answer_id
        )
    except Exception as error:
        raise _as_http_error(error) from error


@router.get("/{game_id}/players/me/cards")
async def get_my_cards(
    game_id: str,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await game_service.get_player_cards(db, game_id, user_id)


@router.put("/{game_id}/players/me/cards")
async def update_my_cards(
    game_id: str,
    body: CardsBody,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await game_service.update_player_cards(db, game_id, user_id, body.cards)


@router.post("/{game_id}/leave")
async def leave_game(
    game_id: str,
    user_id: ClerkUserId,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await game_service.leave_game(db, user_id, game_id)
