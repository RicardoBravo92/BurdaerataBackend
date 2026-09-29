from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import email as email_endpoints
from app.models.user import User
from app.schemas.email import PasswordRecoveryRequest, RegistrationEmailRequest


def _db_for(user):
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db.execute.return_value = result
    return db


class TestRequestPasswordRecovery:
    async def test_user_not_found(self):
        db = _db_for(None)

        resp = await email_endpoints.request_password_recovery(
            PasswordRecoveryRequest(email="nobody@example.com"), db
        )

        assert resp.success is True
        db.execute.assert_awaited()

    async def test_user_found(self, monkeypatch):
        sent = {}

        async def _send(**kwargs):
            sent.update(kwargs)

        service = AsyncMock()
        service.send_password_recovery = _send
        monkeypatch.setattr(email_endpoints, "email_service", service)
        db = _db_for(User(id="u1", email="ana@example.com", full_name="Ana"))

        resp = await email_endpoints.request_password_recovery(
            PasswordRecoveryRequest(email="ana@example.com"), db
        )

        assert resp.success is True
        assert sent["to_email"] == "ana@example.com"
        assert sent["user_name"] == "Ana"
        assert "ana@example.com" in sent["recovery_link"]

    async def test_send_failure(self, monkeypatch):
        async def _boom(**kwargs):
            raise RuntimeError("smtp down")

        service = AsyncMock()
        service.send_password_recovery = _boom
        monkeypatch.setattr(email_endpoints, "email_service", service)
        db = _db_for(User(id="u1", email="ana@example.com"))

        with pytest.raises(HTTPException) as exc:
            await email_endpoints.request_password_recovery(
                PasswordRecoveryRequest(email="ana@example.com"), db
            )

        assert exc.value.status_code == 500


class TestSendRegistrationEmail:
    async def test_success(self, monkeypatch):
        sent = {}

        async def _send(**kwargs):
            sent.update(kwargs)

        service = AsyncMock()
        service.send_registration_success = _send
        monkeypatch.setattr(email_endpoints, "email_service", service)

        resp = await email_endpoints.send_registration_email(
            RegistrationEmailRequest(email="ana@example.com", user_name="Ana"),
            AsyncMock(),
        )

        assert resp.success is True
        assert sent == {"to_email": "ana@example.com", "user_name": "Ana"}

    async def test_failure(self, monkeypatch):
        async def _boom(**kwargs):
            raise RuntimeError("smtp down")

        service = AsyncMock()
        service.send_registration_success = _boom
        monkeypatch.setattr(email_endpoints, "email_service", service)

        with pytest.raises(HTTPException) as exc:
            await email_endpoints.send_registration_email(
                RegistrationEmailRequest(email="ana@example.com", user_name="Ana"),
                AsyncMock(),
            )

        assert exc.value.status_code == 500