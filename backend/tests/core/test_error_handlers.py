import logging
import sqlite3

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.exceptions import NotFoundError, UnauthorizedError

FRONTEND_ORIGIN = "http://localhost:5173"
INSERT_USUARIO = (
    "INSERT INTO usuarios (nombre, correo, password_hash, created_at, updated_at) "
    "VALUES (?, ?, 'hash', 't', 't')"
)


@pytest.fixture
def client(app):
    # Rutas de prueba que provocan cada tipo de error.
    @app.get("/test/not-found")
    def raise_not_found():
        raise NotFoundError("Usuario 7 no existe")

    @app.get("/test/unauthorized")
    def raise_unauthorized():
        raise UnauthorizedError()

    @app.get("/test/validation")
    def validate(limit: int):
        return {"limit": limit}

    @app.get("/test/crash")
    def crash():
        raise RuntimeError("detalle interno que no debe filtrarse")

    @app.post("/test/duplicate")
    def duplicate(connection: sqlite3.Connection = Depends(get_db)):
        connection.execute(INSERT_USUARIO, ("A", "repetido@sema.example"))
        connection.execute(INSERT_USUARIO, ("B", "repetido@sema.example"))

    @app.post("/test/not-null")
    def not_null(connection: sqlite3.Connection = Depends(get_db)):
        connection.execute(INSERT_USUARIO, (None, "x@sema.example"))

    @app.post("/test/write-then-crash")
    def write_then_crash(connection: sqlite3.Connection = Depends(get_db)):
        connection.execute(INSERT_USUARIO, ("A", "a-medias@sema.example"))
        raise RuntimeError("falla después de escribir")

    @app.get("/test/count")
    def count(connection: sqlite3.Connection = Depends(get_db)):
        return {"total": connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]}

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


# ---------- Errores controlados ----------


def test_app_error_uses_standard_format(client):
    response = client.get("/test/not-found")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Usuario 7 no existe"}}


def test_unauthorized_includes_www_authenticate_header(client):
    response = client.get("/test/unauthorized")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.headers["www-authenticate"] == "Bearer"


def test_validation_error_lists_invalid_fields(client):
    response = client.get("/test/validation", params={"limit": "abc"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["field"] == "query.limit"


def test_unknown_route_uses_standard_format_in_spanish(client):
    response = client.get("/no-existe")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Ruta no encontrada"}}


def test_method_not_allowed_in_spanish(client):
    response = client.post("/health")

    assert response.status_code == 405
    assert response.json()["error"]["message"] == "Método no permitido"
    assert response.headers["allow"] == "GET"


def test_body_not_utf8_returns_bad_request_in_spanish(client):
    body = '{"nombre": "Sebastián"}'.encode("latin-1")  # bytes que no son UTF-8

    response = client.post("/usuarios", content=body, headers={"Content-Type": "application/json"})

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "BAD_REQUEST",
        "message": "No se pudo leer el cuerpo de la petición: debe ser JSON en UTF-8",
    }


# ---------- Errores 500 ----------


def test_unexpected_error_hides_details_and_returns_error_id(client):
    response = client.get("/test/crash")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert error["message"] == "Error interno"
    assert len(error["error_id"]) == 12
    assert "detalle interno" not in response.text


def test_unexpected_error_is_logged_with_same_error_id(client, caplog):
    with caplog.at_level(logging.ERROR, logger="app.core.error_handlers"):
        response = client.get("/test/crash")

    error_id = response.json()["error"]["error_id"]
    record = caplog.records[-1]
    assert error_id in record.getMessage()
    assert "GET /test/crash" in record.getMessage()
    assert record.exc_info is not None  # la traza completa queda en el log


def test_error_ids_are_unique(client):
    first = client.get("/test/crash").json()["error"]["error_id"]
    second = client.get("/test/crash").json()["error"]["error_id"]

    assert first != second


def test_unexpected_error_keeps_cors_headers(client):
    # Sin esto, el navegador mostraría un falso "error de CORS" en vez del 500.
    response = client.get("/test/crash", headers={"Origin": FRONTEND_ORIGIN})

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_unexpected_error_rolls_back_writes(client):
    client.post("/test/write-then-crash")

    assert client.get("/test/count").json() == {"total": 0}


# ---------- Errores de integridad de la BD ----------


def test_unique_violation_returns_conflict(client):
    response = client.post("/test/duplicate")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "CONFLICT", "message": "Ya existe un registro con esos datos"}
    }
    assert client.get("/test/count").json() == {"total": 0}  # nada quedó a medias


def test_other_integrity_errors_are_internal_errors(client):
    response = client.post("/test/not-null")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "NOT NULL" not in response.text
