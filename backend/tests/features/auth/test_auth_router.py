from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import connect
from app.core.security import hash_password
from app.main import create_app


@pytest.fixture
def auth_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    app = create_app()
    with TestClient(app) as client:
        connection = connect(settings.db_path)
        connection.execute(
            "INSERT INTO usuarios "
            "(nombre, correo, password_hash, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                "Ana",
                "ana@sema.example",
                hash_password("clave-segura-1"),
                1,
                "2026-11-14T00:00:00+00:00",
                "2026-11-14T00:00:00+00:00",
            ),
        )
        connection.commit()
        connection.close()
        yield client


def test_health_is_public_and_users_are_protected(auth_client):
    assert auth_client.get("/health").status_code == 200
    assert auth_client.get("/usuarios").status_code == 401


def test_login_returns_token_and_me_returns_user(auth_client):
    response = auth_client.post(
        "/auth/login",
        data={"username": "ana@sema.example", "password": "clave-segura-1"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]
    me = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["correo"] == "ana@sema.example"
    assert "password_hash" not in me.text


def test_invalid_login_and_invalid_token_are_unauthorized(auth_client):
    invalid_login = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "incorrecta"}
    )
    assert invalid_login.status_code == 401
    assert invalid_login.json()["error"]["code"] == "UNAUTHORIZED"

    invalid_token = auth_client.get("/auth/me", headers={"Authorization": "Bearer no-es-valido"})
    assert invalid_token.status_code == 401


def test_login_normalizes_correo_and_rejects_inactive_user(auth_client):
    normalized = auth_client.post(
        "/auth/login",
        data={"username": "  ANA@SEMA.EXAMPLE ", "password": "clave-segura-1"},
    )
    assert normalized.status_code == 200

    connection = connect(settings.db_path)
    connection.execute("UPDATE usuarios SET is_active = 0 WHERE correo = ?", ("ana@sema.example",))
    connection.commit()
    connection.close()

    inactive = auth_client.post(
        "/auth/login",
        data={"username": "ana@sema.example", "password": "clave-segura-1"},
    )
    assert inactive.status_code == 401
