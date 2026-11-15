"""Tests de los endpoints: peticiones HTTP reales contra la app con una BD temporal."""

from typing import get_args

import pytest

from app.core.database import connect
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import OrdenUsuario

DATOS = {"nombre": "Ana Pérez", "correo": "ana@sema.example", "password": "clave-segura-1"}


@pytest.fixture
def crear(client):
    """Crea un usuario por la API y devuelve su JSON. Acepta cambios: crear(correo=...)."""

    def _crear(**cambios):
        response = client.post("/usuarios", json={**DATOS, **cambios})
        assert response.status_code == 201, response.text
        return response.json()

    return _crear


# ---------- POST /usuarios ----------


def test_crear_responde_201_sin_datos_sensibles(client):
    response = client.post("/usuarios", json=DATOS)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "id",
        "nombre",
        "correo",
        "genero",
        "telefono",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert body["genero"] is None
    assert body["telefono"] is None
    assert body["is_active"] is True
    assert "password" not in response.text


@pytest.mark.parametrize(
    "nombre",
    [
        "José Peña Muñoz",  # tildes y ñ (español)
        "Zoë Brontë Çelik",  # diéresis y cedilla
        "François Ångström Øster",  # francés y nórdico
        "Ελένη Παπαδοπούλου",  # alfabeto griego
        "李小龍",  # caracteres chinos
        "Ana 🌱 Agro",  # emoji (fuera del plano básico de Unicode)
    ],
)
def test_caracteres_especiales_se_guardan_intactos(client, nombre):
    # La API usa UTF-8 de punta a punta: el nombre debe salir igual que entró,
    # tanto en la respuesta como en la BD (no solo en lo que muestra la consola).
    creado = client.post("/usuarios", json={**DATOS, "nombre": nombre}).json()

    assert creado["nombre"] == nombre
    assert client.get(f"/usuarios/{creado['id']}").json()["nombre"] == nombre
    connection = connect()
    try:
        guardado = connection.execute(
            "SELECT nombre FROM usuarios WHERE id = ?", (creado["id"],)
        ).fetchone()["nombre"]
    finally:
        connection.close()
    assert guardado == nombre


def test_crear_correo_duplicado_responde_409(client, crear):
    crear()

    response = client.post("/usuarios", json=DATOS)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_crear_guarda_datos_opcionales_y_estado(client):
    response = client.post(
        "/usuarios",
        json={
            **DATOS,
            "genero": "  femenino  ",
            "telefono": "+57 (300) 123-4567",
            "is_active": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["genero"] == "femenino"
    assert response.json()["telefono"] == "+57 (300) 123-4567"
    assert response.json()["is_active"] is False


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("correo", "no-es-un-email"),
        ("correo", "ana@sema.local"),  # dominio de uso especial
        ("nombre", "   "),  # solo espacios
        ("nombre", "A"),
        ("password", "corta"),
        ("telefono", "texto-no-valido"),
        ("telefono", "123"),
    ],
)
def test_crear_con_datos_invalidos_responde_422(client, campo, valor):
    response = client.post("/usuarios", json={**DATOS, campo: valor})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("campo_extra", ["deleted_at", "password_hash", "id", "rol"])
def test_crear_con_campos_desconocidos_responde_422(client, campo_extra):
    response = client.post("/usuarios", json={**DATOS, campo_extra: "x"})

    assert response.status_code == 422


# ---------- GET /usuarios ----------


def test_listar_responde_pagina(client, crear):
    crear(correo="a@sema.example")
    crear(correo="b@sema.example")

    response = client.get("/usuarios", params={"limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert (body["limit"], body["offset"]) == (1, 0)
    assert len(body["items"]) == 1
    assert "password_hash" not in response.text


def test_listar_ordena_por_columna(client, crear):
    for nombre in ("Carla", "Ana", "Beto"):
        crear(nombre=nombre, correo=f"{nombre.lower()}@sema.example")

    body = client.get("/usuarios", params={"order_by": "nombre", "direction": "desc"}).json()

    assert [u["nombre"] for u in body["items"]] == ["Carla", "Beto", "Ana"]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"order_by": "password_hash"},
        {"order_by": "id; DROP TABLE usuarios"},
        {"direction": "sideways"},
    ],
)
def test_listar_con_parametros_invalidos_responde_422(client, params):
    response = client.get("/usuarios", params=params)

    assert response.status_code == 422


def test_columnas_de_orden_coinciden_con_el_repositorio():
    # Si alguien agrega una columna en un lado y olvida el otro, este test falla.
    assert set(get_args(OrdenUsuario)) == set(UsuarioRepository.sortable)


# ---------- GET /usuarios/{id} ----------


def test_obtener_responde_usuario(client, crear):
    usuario = crear()

    response = client.get(f"/usuarios/{usuario['id']}")

    assert response.status_code == 200
    assert response.json() == usuario


def test_obtener_inexistente_responde_404(client):
    response = client.get("/usuarios/999")

    assert response.status_code == 404
    assert response.json()["error"] == {"code": "NOT_FOUND", "message": "Usuario 999 no existe"}


# ---------- PATCH /usuarios/{id} ----------


def test_actualizar_parcial(client, crear):
    usuario = crear()

    response = client.patch(f"/usuarios/{usuario['id']}", json={"nombre": "Ana María"})

    assert response.status_code == 200
    assert response.json()["nombre"] == "Ana María"
    assert response.json()["correo"] == usuario["correo"]


def test_actualizar_permite_cambiar_estado_y_limpiar_datos_opcionales(client, crear):
    usuario = crear(genero="Masculino", telefono="300 123 4567")

    response = client.patch(
        f"/usuarios/{usuario['id']}",
        json={"is_active": False, "genero": None, "telefono": None},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["genero"] is None
    assert response.json()["telefono"] is None


def test_actualizar_con_body_vacio_no_cambia_nada(client, crear):
    usuario = crear()

    response = client.patch(f"/usuarios/{usuario['id']}", json={})

    assert response.status_code == 200
    assert response.json() == usuario


@pytest.mark.parametrize("campo", ["nombre", "correo", "password", "is_active"])
def test_actualizar_con_null_responde_422(client, crear, campo):
    usuario = crear()

    response = client.patch(f"/usuarios/{usuario['id']}", json={campo: None})

    assert response.status_code == 422


def test_actualizar_con_campo_desconocido_responde_422(client, crear):
    usuario = crear()

    response = client.patch(f"/usuarios/{usuario['id']}", json={"deleted_at": None})

    assert response.status_code == 422


def test_actualizar_inexistente_responde_404(client):
    response = client.patch("/usuarios/999", json={"nombre": "Nadie"})

    assert response.status_code == 404


def test_actualizar_a_correo_ocupado_responde_409(client, crear):
    crear(correo="ocupado@sema.example")
    usuario = crear(correo="libre@sema.example")

    response = client.patch(f"/usuarios/{usuario['id']}", json={"correo": "ocupado@sema.example"})

    assert response.status_code == 409


# ---------- DELETE /usuarios/{id} ----------


def test_eliminar_responde_204_y_el_usuario_desaparece(client, crear):
    usuario = crear()

    response = client.delete(f"/usuarios/{usuario['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/usuarios/{usuario['id']}").status_code == 404
    assert client.get("/usuarios").json()["total"] == 0


def test_eliminar_inexistente_responde_404(client):
    assert client.delete("/usuarios/999").status_code == 404


def test_se_puede_recrear_un_usuario_eliminado_con_el_mismo_correo(client, crear):
    # Criterio de "listo" de la feature usuarios.
    usuario = crear()
    client.delete(f"/usuarios/{usuario['id']}")

    response = client.post("/usuarios", json=DATOS)

    assert response.status_code == 201
    assert response.json()["id"] != usuario["id"]
