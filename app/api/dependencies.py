from typing import Annotated

from clerk_backend_api.security import authenticate_request_async
from clerk_backend_api.security.types import AuthenticateRequestOptions
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def _authorized_parties() -> list[str] | None:
    parties = settings.authorized_parties
    # Return None for default/empty to allow any origin (Clerk behavior)
    if not parties or parties == ["http://localhost:3000"]:
        return None
    return parties


async def get_clerk_user_id(request: Request) -> str:
    if not settings.clerk_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_SECRET_KEY is not configured on the server",
        )

    options = AuthenticateRequestOptions(
        secret_key=settings.clerk_secret_key,
        authorized_parties=_authorized_parties(),
    )
    state = await authenticate_request_async(request, options)

    if not state.is_signed_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=state.message or "Not authenticated",
        )

    payload = state.payload or {}
    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token payload",
        )
    return user_id


async def get_current_user(
    user_id: Annotated[str, Depends(get_clerk_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    # Add any active user checks here if needed
    return current_user


# Typed dependency aliases for clean router signatures
DbDep = Annotated[AsyncSession, Depends(get_db)]
ClerkUserIdDep = Annotated[str, Depends(get_clerk_user_id)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
ActiveUserDep = Annotated[User, Depends(get_current_active_user)]
