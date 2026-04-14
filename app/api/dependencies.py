from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from clerk_backend_api.security import authenticate_request_async
from clerk_backend_api.security.types import AuthenticateRequestOptions

from app.core.config import get_settings


def _authorized_parties() -> Optional[list[str]]:
    raw = get_settings().AUTHORIZED_PARTIES.strip()
    if not raw:
        return None
    parties = [p.strip() for p in raw.split(",") if p.strip()]
    return parties or None


async def get_clerk_user_id(request: Request) -> str:
    settings = get_settings()
    if not settings.CLERK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CLERK_SECRET_KEY is not configured on the server",
        )

    options = AuthenticateRequestOptions(
        secret_key=settings.CLERK_SECRET_KEY,
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


ClerkUserId = Annotated[str, Depends(get_clerk_user_id)]
