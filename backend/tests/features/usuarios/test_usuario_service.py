"""Tests del service, sin HTTP: se llama directo a sus métodos con una BD temporal."""

import pytest

from app.core.database import connect, run_migrations
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import verify_password
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import UsuarioCreate, UsuarioUpdate
from app.features.usuarios.service import UsuarioService


@pytest.fixture
def repository(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)
    yield UsuarioRepository(connection)
    connection.close()


@pytest.fixture
def service(repository):
    return UsuarioService(repository)


def nuevo(nombre="Ana Pérez", email="ana@sema.example", password="clave-segura-1"):
    return UsuarioCreate(nombre=nombre, email=email, password=password)


# ---------- crear ----------


def test_crear_guarda_password_con_hash(service, repository):
    usuario = service.crear(nuevo())

    registro = repository.get_by_id(usuario.id)
    assert registro["password_hash"] != "clave-segura-1"
    assert verify_password("clave-segura-1", registro["password_hash"])


def test_crear_normaliza_email(service):
    usuario = service.crear(nuevo(email="  Ana@SEMA.example "))

    assert usuario.email == "ana@sema.example"


def test_crear_rechaza_email_duplicado_aunque_cambien_mayusculas(service):
    service.crear(nuevo(email="ana@sema.example"))

    with pytest.raises(ConflictError):
        service.crear(nuevo(email="ANA@sema.example"))


def test_crear_permite_email_de_usuario_eliminado(service):
    eliminado = service.crear(nuevo())
    service.eliminar(eliminado.id)

    nuevo_usuario = service.crear(nuevo())

    assert nuevo_usuario.id != eliminado.id


# ---------- listar ----------


def test_listar_excluye_eliminados_y_cuenta_solo_activos(service):
    activo = service.crear(nuevo(email="activo@sema.example"))
    eliminado = service.crear(nuevo(email="eliminado@sema.example"))
    service.eliminar(eliminado.id)

    pagina = service.listar()

    assert [u.id for u in pagina.items] == [activo.id]
    assert pagina.total == 1


def test_listar_pagina_y_ordena(service):
    for nombre in ("Carla", "Ana", "Beto"):
        service.crear(nuevo(nombre=nombre, email=f"{nombre.lower()}@sema.example"))

    pagina = service.listar(limit=2, offset=0, order_by="nombre", direction="desc")

    assert [u.nombre for u in pagina.items] == ["Carla", "Beto"]
    assert (pagina.total, pagina.limit, pagina.offset) == (3, 2, 0)


# ---------- obtener ----------


def test_obtener_inexistente_lanza_not_found(service):
    with pytest.raises(NotFoundError):
        service.obtener(999)


def test_obtener_eliminado_lanza_not_found(service):
    usuario = service.crear(nuevo())
    service.eliminar(usuario.id)

    with pytest.raises(NotFoundError):
        service.obtener(usuario.id)


# ---------- actualizar ----------


def test_actualizar_cambia_solo_los_campos_enviados(service):
    usuario = service.crear(nuevo(nombre="Ana", email="ana@sema.example"))

    actualizado = service.actualizar(usuario.id, UsuarioUpdate(nombre="Ana María"))

    assert actualizado.nombre == "Ana María"
    assert actualizado.email == "ana@sema.example"


def test_actualizar_password_guarda_hash_nuevo(service, repository):
    usuario = service.crear(nuevo(password="clave-vieja-1"))

    service.actualizar(usuario.id, UsuarioUpdate(password="clave-nueva-2"))

    registro = repository.get_by_id(usuario.id)
    assert verify_password("clave-nueva-2", registro["password_hash"])
    assert not verify_password("clave-vieja-1", registro["password_hash"])


def test_actualizar_a_email_ocupado_lanza_conflict(service):
    service.crear(nuevo(email="ocupado@sema.example"))
    usuario = service.crear(nuevo(email="libre@sema.example"))

    with pytest.raises(ConflictError):
        service.actualizar(usuario.id, UsuarioUpdate(email="ocupado@sema.example"))


def test_actualizar_con_su_propio_email_no_es_conflicto(service):
    usuario = service.crear(nuevo(email="ana@sema.example"))

    actualizado = service.actualizar(usuario.id, UsuarioUpdate(email="ANA@sema.example"))

    assert actualizado.email == "ana@sema.example"


def test_actualizar_inexistente_es_not_found_antes_que_conflict(service):
    service.crear(nuevo(email="ocupado@sema.example"))

    with pytest.raises(NotFoundError):
        service.actualizar(999, UsuarioUpdate(email="ocupado@sema.example"))


# ---------- eliminar ----------


def test_eliminar_dos_veces_lanza_not_found(service):
    usuario = service.crear(nuevo())
    service.eliminar(usuario.id)

    with pytest.raises(NotFoundError):
        service.eliminar(usuario.id)
