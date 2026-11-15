from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.features.auth.dependencies import get_current_user
from app.features.usuarios.schemas import UsuarioOut
from app.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch) -> FastAPI:
    """App de prueba con una base de datos temporal (se borra al terminar el test)."""
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    application = create_app()
    application.dependency_overrides[get_current_user] = lambda: UsuarioOut(
        id=1,
        nombre="Usuario de pruebas",
        correo="test@sema.example",
        genero=None,
        telefono=None,
        is_active=True,
        created_at="2026-11-14T00:00:00Z",
        updated_at="2026-11-14T00:00:00Z",
    )
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # `with` ejecuta el lifespan (migraciones) igual que al arrancar el servidor.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
