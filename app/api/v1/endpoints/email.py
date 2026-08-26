from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.schemas.email import (
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    RegistrationEmailRequest,
    RegistrationEmailResponse,
)
from app.services.email_service import email_service

router = APIRouter()


@router.post(
    "/password-recovery",
    response_model=PasswordRecoveryResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_recovery(
    body: PasswordRecoveryRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordRecoveryResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        return PasswordRecoveryResponse(
            success=True,
            message="If the email exists, a recovery link has been sent.",
        )

    recovery_link = f"https://burdaerata.vercel.app/reset-password?email={body.email}"

    try:
        await email_service.send_password_recovery(
            to_email=body.email,
            user_name=user.full_name or "Player",
            recovery_link=recovery_link,
        )
        return PasswordRecoveryResponse(
            success=True,
            message="Recovery email sent successfully.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send recovery email: {str(e)}",
        )


@router.post(
    "/registration-success",
    response_model=RegistrationEmailResponse,
    status_code=status.HTTP_200_OK,
)
async def send_registration_email(
    body: RegistrationEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> RegistrationEmailResponse:
    try:
        await email_service.send_registration_success(
            to_email=body.email,
            user_name=body.user_name,
        )
        return RegistrationEmailResponse(
            success=True,
            message="Registration success email sent.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send registration email: {str(e)}",
        )