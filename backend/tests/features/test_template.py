"""Tests de la plantilla `features/_template`: el molde debe seguir funcionando.

También sirven de ejemplo para los tests de una feature nueva: copiar este archivo a
`tests/features/<feature>/` y adaptarlo. La plantilla no está registrada en `main.py`
ni tiene migración, así que aquí se registra y se crea su tabla solo para estas pruebas.
"""

from pathlib import Path
from typing import get_args

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import connect
from app.features._template import router as template_router
from app.features._template.repository import EjemploRepository
from app.features._template.schemas import OrdenEjemplo

MIGRATION = Path(template_router.__file__).parent / "migration.sql.example"


@pytest.fixture
def client(app):
    """Cliente con el router de la plantilla registrado y su tabla creada."""
    connection = connect(settings.db_path)
    connection.executescript(MIGRATION.read_text(encoding="utf-8"))
    connection.close()
    app.include_router(template_router.router)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def crear(client):
    def _crear(**campos):
        response = client.post("/ejemplos", json={"nombre": "Riego", **campos})
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


def test_migration_matches_repository_columns(client):
    connection = connect(settings.db_path)
    columnas = {row["name"] for row in connection.execute("PRAGMA table_info(ejemplos)")}
    connection.close()

    esperadas = {*EjemploRepository.columns, "id", "created_at", "updated_at", "deleted_at"}
    assert columnas == esperadas


def test_order_options_match_repository():
    assert set(get_args(OrdenEjemplo)) == set(EjemploRepository.sortable)


def test_crud_flow(client, crear):
    creado = crear(descripcion="Cada 3 días")
    assert creado["id"] == 1
    assert "deleted_at" not in creado

    assert client.get("/ejemplos/1").json()["nombre"] == "Riego"

    cambiado = client.patch("/ejemplos/1", json={"nombre": "Riego diario"})
    assert cambiado.status_code == 200
    assert cambiado.json()["nombre"] == "Riego diario"
    assert cambiado.json()["descripcion"] == "Cada 3 días"  # no se tocó

    assert client.delete("/ejemplos/1").status_code == 204
    assert client.get("/ejemplos/1").status_code == 404


def test_list_is_paginated_and_ordered(client, crear):
    for nombre in ["Cosecha", "Abono", "Siembra"]:
        crear(nombre=nombre)

    response = client.get("/ejemplos?limit=2&order_by=nombre&direction=asc")

    pagina = response.json()
    assert [item["nombre"] for item in pagina["items"]] == ["Abono", "Cosecha"]
    assert (pagina["total"], pagina["limit"], pagina["offset"]) == (3, 2, 0)


def test_duplicate_name_responds_409(client, crear):
    crear()

    assert client.post("/ejemplos", json={"nombre": "Riego"}).status_code == 409


def test_keeping_own_name_on_update_is_not_a_conflict(client, crear):
    crear()

    assert client.patch("/ejemplos/1", json={"nombre": "Riego"}).status_code == 200


def test_deleted_record_does_not_block_its_name(client, crear):
    crear()
    client.delete("/ejemplos/1")

    assert client.post("/ejemplos", json={"nombre": "Riego"}).status_code == 201


@pytest.mark.parametrize("ruta", ["/ejemplos/999"])
def test_missing_record_responds_404(client, ruta):
    assert client.get(ruta).status_code == 404
    assert client.patch(ruta, json={"nombre": "Otro"}).status_code == 404
    assert client.delete(ruta).status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"nombre": "x"},  # muy corto
        {"nombre": "   "},  # solo espacios
        {"nombre": "Riego", "rol": "admin"},  # campo desconocido
        {"nombre": "Riego", "deleted_at": "2026-01-01"},  # columna de auditoría
    ],
)
def test_invalid_create_responds_422(client, body):
    assert client.post("/ejemplos", json=body).status_code == 422


def test_patch_rejects_null_in_not_null_field_but_allows_it_in_nullable(client, crear):
    crear(descripcion="Algo")

    assert client.patch("/ejemplos/1", json={"nombre": None}).status_code == 422

    limpiado = client.patch("/ejemplos/1", json={"descripcion": None})
    assert limpiado.status_code == 200
    assert limpiado.json()["descripcion"] is None


def test_list_filters_search_and_date_range(client, crear):
    crear(nombre="Riego", descripcion="Cada tres días")
    crear(nombre="Abono")

    por_texto = client.get("/ejemplos", params={"q": "días"}).json()
    assert [item["nombre"] for item in por_texto["items"]] == ["Riego"]
    assert por_texto["total"] == 1

    futuro = client.get("/ejemplos", params={"created_from": "2999-01-01T00:00:00Z"}).json()
    assert (futuro["items"], futuro["total"]) == ([], 0)
