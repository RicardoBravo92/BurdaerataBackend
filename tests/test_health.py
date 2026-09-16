from fastapi.testclient import TestClient

from app.main import app


def test_health(monkeypatch) -> None:
    # The lifespan calls init_db(), which would touch the configured database.
    # Patch it so the health test stays isolated from the real DB.
    async def _noop_init_db():
        return None

    monkeypatch.setattr("app.main.init_db", _noop_init_db)

    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}