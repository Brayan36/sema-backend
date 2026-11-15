"""Pruebas de usuario-rol y rol-permiso."""

import pytest


@pytest.fixture
def datos(client):
    usuario = client.post(
        "/usuarios",
        json={"nombre": "Ana Pérez", "correo": "ana@sema.example", "password": "clave-segura-1"},
    ).json()
    rol = client.post("/roles", json={"nombre": "Administrador"}).json()
    permiso = client.post("/permisos", json={"nombre": "cultivos.crear"}).json()
    return usuario, rol, permiso


def test_asignar_consultar_y_reemplazar_rol_de_usuario(client, datos):
    usuario, rol, _ = datos

    response = client.put(f"/asignaciones/usuarios/{usuario['id']}/rol", json={"rol_id": rol["id"]})
    assert response.status_code == 200
    assert response.json()["rol_id"] == rol["id"]
    assert client.get(f"/asignaciones/usuarios/{usuario['id']}/rol").json() == response.json()


def test_retirar_rol_y_listar_usuarios(client, datos):
    usuario, rol, _ = datos
    client.put(f"/asignaciones/usuarios/{usuario['id']}/rol", json={"rol_id": rol["id"]})

    assert client.get(f"/asignaciones/roles/{rol['id']}/usuarios").json()[0]["id"] == usuario["id"]
    assert client.delete(f"/asignaciones/usuarios/{usuario['id']}/rol").status_code == 204
    assert client.get(f"/asignaciones/roles/{rol['id']}/usuarios").json() == []


def test_asignar_listar_y_retirar_permiso(client, datos):
    _, rol, permiso = datos
    ruta = f"/asignaciones/roles/{rol['id']}/permisos/{permiso['id']}"

    assert client.put(ruta).status_code == 204
    permisos = client.get(f"/asignaciones/roles/{rol['id']}/permisos").json()
    assert [item["id"] for item in permisos] == [permiso["id"]]
    assert client.get(f"/asignaciones/permisos/{permiso['id']}/roles").json()[0]["id"] == rol["id"]
    assert client.delete(ruta).status_code == 204
    assert client.get(f"/asignaciones/roles/{rol['id']}/permisos").json() == []


def test_no_permite_asignar_recursos_inexistentes(client, datos):
    usuario, rol, permiso = datos

    assert (
        client.put(f"/asignaciones/usuarios/{usuario['id']}/rol", json={"rol_id": 999}).status_code
        == 404
    )
    assert (
        client.put("/asignaciones/usuarios/999/rol", json={"rol_id": rol["id"]}).status_code == 404
    )
    assert client.put(f"/asignaciones/roles/{rol['id']}/permisos/999").status_code == 404
    assert client.get("/asignaciones/permisos/999/roles").status_code == 404


def test_retirar_relacion_inexistente_responde_404(client, datos):
    usuario, rol, permiso = datos

    assert client.delete(f"/asignaciones/usuarios/{usuario['id']}/rol").status_code == 404
    assert (
        client.delete(f"/asignaciones/roles/{rol['id']}/permisos/{permiso['id']}").status_code
        == 404
    )
