"""Custom exceptions for the service layer with HTTP status code mapping."""


class ServiceError(Exception):
    """Base exception for service layer errors."""

    status_code = 400
    detail = "Service error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(ServiceError):
    """Resource not found."""

    status_code = 404
    detail = "Resource not found"


class UnauthorizedError(ServiceError):
    """Authentication required."""

    status_code = 401
    detail = "Unauthorized"


class ForbiddenError(ServiceError):
    """Authenticated but not authorized."""

    status_code = 403
    detail = "Forbidden"


class ConflictError(ServiceError):
    """Resource conflict (e.g., duplicate)."""

    status_code = 409
    detail = "Conflict"


class ValidationError(ServiceError):
    """Input validation failed."""

    status_code = 422
    detail = "Validation error"


# Game-specific exceptions
class GameNotFoundError(NotFoundError):
    detail = "Game not found"


class GameFullError(ConflictError):
    detail = "Game is full"


class GameAlreadyStartedError(ConflictError):
    detail = "Game has already started"


class GameNotInProgressError(ConflictError):
    detail = "Game is not in playing state"


class NotGameHostError(ForbiddenError):
    detail = "Only the host can perform this action"


class NotInGameError(ForbiddenError):
    detail = "You are not in this game"


class JudgeCannotSubmitError(ForbiddenError):
    detail = "Judge cannot submit answers"


class AlreadySubmittedError(ConflictError):
    detail = "You have already submitted an answer for this round"


class RoundNotAcceptingAnswersError(ConflictError):
    detail = "This round is no longer accepting answers"


class RoundAlreadyFinishedError(ConflictError):
    detail = "This round is already finished"


class InvalidCardsError(ValidationError):
    detail = "You do not have one of the submitted cards"


class NotEnoughPlayersError(ValidationError):
    detail = "Need at least 2 players to start the game"


class AllPlayersMustSubmitError(ValidationError):
    detail = "Cannot select a winner until all players have submitted their answers"


class JudgeCannotWinError(ForbiddenError):
    detail = "The judge cannot win their own round"


# Player-specific exceptions
class PlayerNotFoundError(NotFoundError):
    detail = "Player not found in game"


class PlayerAlreadyInGameError(ConflictError):
    detail = "You are already in this game"
