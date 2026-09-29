from types import SimpleNamespace

from app.services.email_service import email_service


class TestEmailService:
    async def test_send_password_recovery(self, monkeypatch):
        captured = {}

        def _fake_send(params):
            captured["params"] = params
            return SimpleNamespace(id="email-1")

        monkeypatch.setattr(
            "app.services.email_service.resend.Emails.send", _fake_send
        )

        result = await email_service.send_password_recovery(
            "ana@example.com", "Ana", "https://burdaerata.app/reset?token=abc"
        )

        assert result == {"success": True, "id": "email-1"}
        params = captured["params"]
        assert params["to"] == ["ana@example.com"]
        assert params["subject"] == "Password Recovery - Burdaerata"
        assert params["from"] == "Burdaerata <onboarding@resend.dev>"
        assert "Ana" in params["html"]
        assert "https://burdaerata.app/reset?token=abc" in params["html"]

    async def test_send_registration_success(self, monkeypatch):
        captured = {}

        def _fake_send(params):
            captured["params"] = params
            return SimpleNamespace(id="email-2")

        monkeypatch.setattr(
            "app.services.email_service.resend.Emails.send", _fake_send
        )

        result = await email_service.send_registration_success("ana@example.com", "Ana")

        assert result == {"success": True, "id": "email-2"}
        params = captured["params"]
        assert params["to"] == ["ana@example.com"]
        assert params["subject"] == "Welcome to Burdaerata!"
        assert "Ana" in params["html"]