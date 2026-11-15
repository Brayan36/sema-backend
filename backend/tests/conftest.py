from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.features.auth.authorization import (
    admin_required,
    can_create_users,
    can_delete_users,
    can_read_users,
    can_update_users,
)
from app.features.auth.dependencies import get_current_user
from app.features.usuarios.schemas import UsuarioOut
from app.main import create_app


@pytest.fixture(autouse=True)
def isolate_from_local_env(monkeypatch):
    """El .env del equipo no debe crear el primer usuario en cada test."""
    monkeypatch.setattr(settings, "first_user_email", None)
    monkeypatch.setattr(settings, "first_user_password", None)


@pytest.fixture
def app(tmp_path, monkeypatch) -> FastAPI:
    """App de prueba con una base de datos temporal (se borra al terminar el test)."""
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: UsuarioOut(
        id=999_999,  # no debe coincidir con ningún usuario creado en los tests
        nombre="Usuario de pruebas",
        correo="test@sema.example",
        genero=None,
        telefono=None,
        is_active=True,
        created_at="2026-11-14T00:00:00Z",
        updated_at="2026-11-14T00:00:00Z",
    )
    application.dependency_overrides[admin_required] = lambda: None
    for dependency in (can_create_users, can_read_users, can_update_users, can_delete_users):
        application.dependency_overrides[dependency] = lambda: None
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # `with` ejecuta el lifespan (migraciones) igual que al arrancar el servidor.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
