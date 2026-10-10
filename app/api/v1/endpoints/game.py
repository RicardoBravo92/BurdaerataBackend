from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUserDep, DbDep
from app.core.rate_limit import limiter
from app.schemas.game import (
    CreateGameRequest,
    GameRead,
    GameListResponse,
    JoinGameRequest,
)
from app.schemas.game_player import GamePlayerRead, PlayerCardsRead, LeaveGameResponse
from app.schemas.round import RoundRead, CreateRoundAnswerRequest, SelectWinnerRequest
from app.schemas.round_answer import RoundAnswerRead
from app.services.game_service import game_service
from app.services.exceptions import (
    GameNotFoundError,
    GameFullError,
    GameAlreadyStartedError,
    GameNotInProgressError,
    NotGameHostError,
    NotInGameError,
    JudgeCannotSubmitError,
    AlreadySubmittedError,
    RoundNotAcceptingAnswersError,
    RoundAlreadyFinishedError,
    InvalidCardsError,
    NotEnoughPlayersError,
    AllPlayersMustSubmitError,
    JudgeCannotWinError,
    PlayerNotFoundError,
    PlayerAlreadyInGameError,
)

router = APIRouter()


def _handle_service_error(e: Exception) -> HTTPException:
    """Map service exceptions to HTTP exceptions."""
    if isinstance(e, GameNotFoundError):
        return HTTPException(status_code=404, detail=e.detail)
    if isinstance(e, GameFullError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, GameAlreadyStartedError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, GameNotInProgressError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, NotGameHostError):
        return HTTPException(status_code=403, detail=e.detail)
    if isinstance(e, NotInGameError):
        return HTTPException(status_code=403, detail=e.detail)
    if isinstance(e, JudgeCannotSubmitError):
        return HTTPException(status_code=403, detail=e.detail)
    if isinstance(e, AlreadySubmittedError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, RoundNotAcceptingAnswersError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, RoundAlreadyFinishedError):
        return HTTPException(status_code=409, detail=e.detail)
    if isinstance(e, InvalidCardsError):
        return HTTPException(status_code=422, detail=e.detail)
    if isinstance(e, NotEnoughPlayersError):
        return HTTPException(status_code=422, detail=e.detail)
    if isinstance(e, AllPlayersMustSubmitError):
        return HTTPException(status_code=422, detail=e.detail)
    if isinstance(e, JudgeCannotWinError):
        return HTTPException(status_code=403, detail=e.detail)
    if isinstance(e, PlayerNotFoundError):
        return HTTPException(status_code=404, detail=e.detail)
    if isinstance(e, PlayerAlreadyInGameError):
        return HTTPException(status_code=409, detail=e.detail)
    # Fallback for unexpected errors
    return HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=GameRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_game(
    request: Request,
    body: CreateGameRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GameRead:
    try:
        return await game_service.create_game(
            db, current_user.id, body.max_players, body.score_to_win
        )
    except Exception as e:
        raise _handle_service_error(e) from e


@router.get("/by-code/{code}", response_model=GameRead)
async def get_game_by_code(
    code: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GameRead:
    game = await game_service.get_game_by_code(db, code)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.get("/{game_id}", response_model=GameRead)
async def get_game(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GameRead:
    game = await game_service.get_game_by_id(db, game_id)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game


@router.post("/join", response_model=GameRead)
@limiter.limit("20/minute")
async def join_game(
    request: Request,
    body: JoinGameRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> GameRead:
    try:
        return await game_service.join_game(db, current_user.id, body.code)
    except Exception as e:
        raise _handle_service_error(e) from e


@router.get("/{game_id}/players", response_model=list[GamePlayerRead])
async def get_game_players(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[GamePlayerRead]:
    players = await game_service.get_game_players(db, game_id)
    return players


@router.post("/{game_id}/start", response_model=RoundRead)
@limiter.limit("10/minute")
async def start_game(
    request: Request,
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RoundRead:
    try:
        return await game_service.start_game(db, current_user.id, game_id)
    except Exception as e:
        raise _handle_service_error(e) from e


@router.get("/{game_id}/rounds/last", response_model=RoundRead)
async def get_last_round(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RoundRead:
    round_obj = await game_service.get_last_round(db, game_id)
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No rounds found")
    return round_obj


@router.post("/{game_id}/rounds/next", response_model=RoundRead)
async def start_next_round(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RoundRead:
    try:
        return await game_service.start_next_round(db, current_user.id, game_id)
    except Exception as e:
        raise _handle_service_error(e) from e


@router.get("/rounds/{round_id}/answers", response_model=list[RoundAnswerRead])
async def get_round_answers(
    round_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[RoundAnswerRead]:
    answers = await game_service.get_round_answers(db, round_id)
    return answers


@router.post("/rounds/{round_id}/answers", response_model=RoundAnswerRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_round_answer(
    request: Request,
    round_id: str,
    body: CreateRoundAnswerRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RoundAnswerRead:
    try:
        return await game_service.create_round_answer(
            db, round_id, current_user.id, body.cards_used
        )
    except Exception as e:
        raise _handle_service_error(e) from e


@router.post("/rounds/{round_id}/winner", response_model=RoundAnswerRead)
@limiter.limit("10/minute")
async def select_winner(
    request: Request,
    round_id: str,
    body: SelectWinnerRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> RoundAnswerRead:
    try:
        return await game_service.select_winner(
            db, current_user.id, round_id, body.winning_answer_id
        )
    except Exception as e:
        raise _handle_service_error(e) from e


@router.get("/{game_id}/players/me/cards", response_model=PlayerCardsRead)
async def get_my_cards(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> PlayerCardsRead:
    cards = await game_service.get_player_cards(db, game_id, current_user.id)
    return cards


@router.post("/{game_id}/leave", response_model=LeaveGameResponse)
async def leave_game(
    game_id: str,
    current_user: CurrentUserDep,
    db: DbDep,
) -> LeaveGameResponse:
    result = await game_service.leave_game(db, current_user.id, game_id)
    return result