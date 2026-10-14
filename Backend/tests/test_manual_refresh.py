import os

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_refresh_is_disabled_without_admin_token(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)

    response = client.post("/jobs/ingest?market=canada")

    assert response.status_code == 403


def test_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "right-token")

    response = client.post(
        "/jobs/ingest?market=canada",
        headers={"X-Admin-Token": "wrong"},
    )

    assert response.status_code == 403
