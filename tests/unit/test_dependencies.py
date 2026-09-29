from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import dependencies


class TestAuthorizedParties:
    def test_empty_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            dependencies, "get_settings", lambda: SimpleNamespace(AUTHORIZED_PARTIES="  ")
        )
        assert dependencies._authorized_parties() is None

    def test_only_commas_returns_none(self, monkeypatch):
        monkeypatch.setattr(
            dependencies, "get_settings", lambda: SimpleNamespace(AUTHORIZED_PARTIES=", ,")
        )
        assert dependencies._authorized_parties() is None

    def test_parses_list(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(AUTHORIZED_PARTIES=" https://a.com , https://b.com "),
        )
        assert dependencies._authorized_parties() == ["https://a.com", "https://b.com"]


async def _state(is_signed_in=True, payload=None, message=None):
    return SimpleNamespace(
        is_signed_in=is_signed_in, payload=payload or {}, message=message
    )


class TestGetClerkUserId:
    async def test_missing_secret_key(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="", AUTHORIZED_PARTIES=""),
        )
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_clerk_user_id(object())
        assert exc.value.status_code == 503

    async def test_not_signed_in(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _auth(request, options):
            return await _state(is_signed_in=False, message="no session")

        monkeypatch.setattr(dependencies, "authenticate_request_async", _auth)
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_clerk_user_id(object())
        assert exc.value.status_code == 401

    async def test_payload_missing_sub(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _auth(request, options):
            return await _state()

        monkeypatch.setattr(dependencies, "authenticate_request_async", _auth)
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_clerk_user_id(object())
        assert exc.value.status_code == 401

    async def test_invalid_sub_type(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _auth(request, options):
            return await _state(payload={"sub": 42})

        monkeypatch.setattr(dependencies, "authenticate_request_async", _auth)
        with pytest.raises(HTTPException) as exc:
            await dependencies.get_clerk_user_id(object())
        assert exc.value.status_code == 401

    async def test_success(self, monkeypatch):
        monkeypatch.setattr(
            dependencies,
            "get_settings",
            lambda: SimpleNamespace(CLERK_SECRET_KEY="sk", AUTHORIZED_PARTIES="https://a.com"),
        )

        async def _auth(request, options):
            return await _state(payload={"sub": "user-1"})

        monkeypatch.setattr(dependencies, "authenticate_request_async", _auth)
        assert await dependencies.get_clerk_user_id(object()) == "user-1"