from collections.abc import Iterator

import jwt
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


@pytest.mark.parametrize(
    "path",
    [
        "/usuarios",
        "/roles",
        "/permisos",
        "/asignaciones/usuarios/1/rol",
        "/asignaciones/roles/1/usuarios",
        "/asignaciones/roles/1/permisos",
        "/asignaciones/permisos/1/roles",
        "/auth/me",
    ],
)
def test_business_routes_require_bearer_token(auth_client, path):
    assert auth_client.get(path).status_code == 401


def test_public_documentation_routes_remain_available(auth_client):
    assert auth_client.get("/docs").status_code == 200
    assert auth_client.get("/openapi.json").status_code == 200


def test_authenticated_user_without_role_cannot_manage_roles(auth_client):
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]

    response = auth_client.get("/roles", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_role_can_manage_roles(auth_client):
    connection = connect(settings.db_path)
    connection.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("admin", "2026-11-14T00:00:00Z", "2026-11-14T00:00:00Z"),
    )
    connection.execute("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, 1)")
    connection.commit()
    connection.close()
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]

    response = auth_client.get("/roles", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_permission_controls_user_read_access(auth_client):
    connection = connect(settings.db_path)
    connection.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("agricultor", "2026-11-14T00:00:00Z", "2026-11-14T00:00:00Z"),
    )
    connection.execute(
        "INSERT INTO permisos (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("usuarios.consultar", "2026-11-14T00:00:00Z", "2026-11-14T00:00:00Z"),
    )
    connection.execute("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, 1)")
    connection.execute("INSERT INTO rol_permisos (rol_id, permiso_id) VALUES (1, 1)")
    connection.commit()
    connection.close()
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]

    response = auth_client.get("/usuarios", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_expired_token_is_rejected(auth_client):
    token = jwt.encode(
        {"sub": "1", "exp": 1}, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    response = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_tampered_token_is_rejected(auth_client):
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    response = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})

    assert response.status_code == 401


def test_deleted_admin_role_revokes_administrative_access(auth_client):
    connection = connect(settings.db_path)
    connection.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("admin", "2026-11-14T00:00:00Z", "2026-11-14T00:00:00Z"),
    )
    connection.execute("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, 1)")
    connection.commit()
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]
    connection.execute("UPDATE roles SET deleted_at = ? WHERE id = 1", ("2026-11-15T00:00:00Z",))
    connection.commit()
    connection.close()

    response = auth_client.get("/roles", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_bootstrap_creates_first_user(tmp_path, monkeypatch):
    from app.core.database import connect, run_migrations
    from app.features.auth.service import bootstrap_first_user

    monkeypatch.setattr(settings, "db_path", tmp_path / "bootstrap.db")
    monkeypatch.setattr(settings, "first_user_email", "admin@sema.example")
    monkeypatch.setattr(settings, "first_user_password", "clave-admin-1")
    connection = connect(settings.db_path)
    run_migrations(connection)

    assert bootstrap_first_user(connection) is True
    assert bootstrap_first_user(connection) is False
    assert connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 1
    connection.close()


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


def test_me_invalidates_token_when_user_is_soft_deleted(auth_client):
    token = auth_client.post(
        "/auth/login", data={"username": "ana@sema.example", "password": "clave-segura-1"}
    ).json()["access_token"]
    connection = connect(settings.db_path)
    connection.execute(
        "UPDATE usuarios SET deleted_at = ? WHERE correo = ?",
        ("2026-11-14T01:00:00Z", "ana@sema.example"),
    )
    connection.commit()
    connection.close()

    response = auth_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
