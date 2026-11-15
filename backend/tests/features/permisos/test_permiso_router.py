"""Pruebas HTTP del CRUD de permisos."""

from typing import get_args

import pytest

from app.features.permisos.repository import PermisoRepository
from app.features.permisos.schemas import OrdenPermiso

DATOS = {"nombre": "cultivos.crear", "descripcion": "Registrar cultivos"}


@pytest.fixture
def crear(client):
    def _crear(**cambios):
        response = client.post("/permisos", json={**DATOS, **cambios})
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


def test_crear_y_obtener_permiso(client):
    response = client.post("/permisos", json=DATOS)

    assert response.status_code == 201
    creado = response.json()
    assert set(creado) == {"id", "nombre", "descripcion", "created_at", "updated_at"}
    assert creado["nombre"] == "cultivos.crear"
    assert client.get(f"/permisos/{creado['id']}").json() == creado


def test_crear_rechaza_nombre_duplicado(client, crear):
    crear()

    response = client.post("/permisos", json=DATOS)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", " "),
        ("nombre", "A"),
        ("nombre", "x" * 101),
        ("descripcion", "x" * 501),
    ],
)
def test_crear_valida_datos(client, campo, valor):
    assert client.post("/permisos", json={**DATOS, campo: valor}).status_code == 422


def test_listar_pagina_busca_y_ordena(client, crear):
    crear(nombre="cultivos.crear")
    crear(nombre="informes.consultar", descripcion="Consulta informes")

    response = client.get("/permisos", params={"q": "inform", "order_by": "nombre", "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert [permiso["nombre"] for permiso in body["items"]] == ["informes.consultar"]
    assert (body["total"], body["limit"], body["offset"]) == (1, 1, 0)


def test_actualizar_permite_limpiar_descripcion(client, crear):
    permiso = crear()

    response = client.patch(f"/permisos/{permiso['id']}", json={"descripcion": None})

    assert response.status_code == 200
    assert response.json()["descripcion"] is None


@pytest.mark.parametrize("body", [{"nombre": None}, {"campo": "valor"}])
def test_actualizar_rechaza_nombre_nulo_y_campos_desconocidos(client, crear, body):
    permiso = crear()

    assert client.patch(f"/permisos/{permiso['id']}", json=body).status_code == 422


def test_eliminar_oculta_permiso_y_permite_reutilizar_nombre(client, crear):
    permiso = crear()

    assert client.delete(f"/permisos/{permiso['id']}").status_code == 204
    assert client.get(f"/permisos/{permiso['id']}").status_code == 404
    recreado = client.post("/permisos", json=DATOS)
    assert recreado.status_code == 201
    assert recreado.json()["id"] != permiso["id"]


def test_columnas_de_orden_coinciden_con_repositorio():
    assert set(get_args(OrdenPermiso)) == set(PermisoRepository.sortable)
