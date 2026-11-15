"""Pruebas HTTP del CRUD de roles."""

from typing import get_args

import pytest

from app.features.roles.repository import RolRepository
from app.features.roles.schemas import OrdenRol

DATOS = {"nombre": "Administrador", "descripcion": "Gestiona el sistema"}


@pytest.fixture
def crear(client):
    def _crear(**cambios):
        response = client.post("/roles", json={**DATOS, **cambios})
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


def test_crear_y_obtener_rol(client):
    response = client.post("/roles", json=DATOS)

    assert response.status_code == 201
    creado = response.json()
    assert set(creado) == {"id", "nombre", "descripcion", "created_at", "updated_at"}
    assert creado["nombre"] == "Administrador"
    assert client.get(f"/roles/{creado['id']}").json() == creado


def test_crear_rechaza_nombre_duplicado(client, crear):
    crear()

    response = client.post("/roles", json=DATOS)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", " "),
        ("nombre", "A"),
        ("nombre", "x" * 51),
        ("descripcion", "x" * 501),
    ],
)
def test_crear_valida_datos(client, campo, valor):
    assert client.post("/roles", json={**DATOS, campo: valor}).status_code == 422


def test_listar_pagina_busca_y_ordena(client, crear):
    crear(nombre="Supervisor")
    crear(nombre="Tecnico", descripcion="Gestiona cultivos")

    response = client.get("/roles", params={"q": "tecn", "order_by": "nombre", "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert [rol["nombre"] for rol in body["items"]] == ["Tecnico"]
    assert (body["total"], body["limit"], body["offset"]) == (1, 1, 0)


def test_actualizar_permite_limpiar_descripcion(client, crear):
    rol = crear()

    response = client.patch(f"/roles/{rol['id']}", json={"descripcion": None})

    assert response.status_code == 200
    assert response.json()["descripcion"] is None


@pytest.mark.parametrize("body", [{"nombre": None}, {"campo": "valor"}])
def test_actualizar_rechaza_nombre_nulo_y_campos_desconocidos(client, crear, body):
    rol = crear()

    assert client.patch(f"/roles/{rol['id']}", json=body).status_code == 422


def test_eliminar_oculta_rol_y_permite_reutilizar_nombre(client, crear):
    rol = crear()

    assert client.delete(f"/roles/{rol['id']}").status_code == 204
    assert client.get(f"/roles/{rol['id']}").status_code == 404
    recreado = client.post("/roles", json=DATOS)
    assert recreado.status_code == 201
    assert recreado.json()["id"] != rol["id"]


def test_columnas_de_orden_coinciden_con_repositorio():
    assert set(get_args(OrdenRol)) == set(RolRepository.sortable)
