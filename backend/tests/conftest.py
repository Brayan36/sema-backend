from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


@pytest.fixture
def app(tmp_path, monkeypatch) -> FastAPI:
    """App de prueba con una base de datos temporal (se borra al terminar el test)."""
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    # `with` ejecuta el lifespan (migraciones) igual que al arrancar el servidor.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
