import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import DbDep
from app.core.config import settings
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.email import (
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    RegistrationEmailRequest,
    RegistrationEmailResponse,
)
from app.services.email_service import email_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Generic message returned regardless of user existence (prevents enumeration)
RECOVERY_MESSAGE = "If the email exists, a recovery link has been sent."


@router.post(
    "/password-recovery",
    response_model=PasswordRecoveryResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("3/minute")
async def request_password_recovery(
    request: Request,
    body: PasswordRecoveryRequest,
    db: DbDep,
) -> PasswordRecoveryResponse:
    # Always check user existence but don't reveal it
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    # Use config for frontend URL, put token in path not query param
    # For now, use the same message for both cases
    recovery_link = f"{settings.frontend_url}/reset-password" if hasattr(settings, 'frontend_url') else "https://burdaerata.vercel.app/reset-password"

    if user:
        try:
            await email_service.send_password_recovery(
                to_email=body.email,
                user_name=user.full_name or "Player",
                recovery_link=recovery_link,
            )
        except Exception:
            logger.exception("Failed to send password recovery email to %s", body.email)

    # Always return same response to prevent user enumeration
    return PasswordRecoveryResponse(
        success=True,
        message=RECOVERY_MESSAGE,
    )


@router.post(
    "/registration-success",
    response_model=RegistrationEmailResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
async def send_registration_email(
    request: Request,
    body: RegistrationEmailRequest,
    db: DbDep,
) -> RegistrationEmailResponse:
    try:
        await email_service.send_registration_success(
            to_email=body.email,
            user_name=body.user_name,
        )
    except Exception:
        logger.exception("Failed to send registration email to %s", body.email)
        # Don't leak internal error details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send registration email. Please try again later.",
        )

    return RegistrationEmailResponse(
        success=True,
        message="Registration success email sent.",
    )