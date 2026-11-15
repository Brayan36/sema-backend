"""Contrato físico de la fase 1: usuarios, roles y permisos."""

import sqlite3

import pytest

from app.core.config import settings
from app.core.database import connect, run_migrations


@pytest.fixture
def connection(tmp_path):
    database = connect(tmp_path / "test.db")
    run_migrations(database)
    yield database
    database.close()


def test_creates_the_five_user_management_tables(connection):
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }

    assert {"usuarios", "roles", "permisos", "usuario_roles", "rol_permisos"} <= tables

    user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(usuarios)")}
    assert {"correo", "genero", "telefono", "is_active", "deleted_at"} <= user_columns


def test_usuario_roles_allows_only_one_role_per_user(connection):
    now = "2026-11-14T00:00:00+00:00"
    connection.execute(
        "INSERT INTO usuarios (nombre, correo, password_hash, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("Ana", "ana@sema.example", "hash", now, now),
    )
    ids = {row["nombre"]: row["id"] for row in connection.execute("SELECT id, nombre FROM roles")}
    connection.execute(
        "INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, ?)", (ids["admin"],)
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, ?)", (ids["agricultor"],)
        )


def test_base_roles_and_permissions_are_created_by_migration(connection):
    roles = {row["nombre"] for row in connection.execute("SELECT nombre FROM roles")}
    assert roles == {"admin", "agricultor"}

    def permisos(rol):
        rows = connection.execute(
            "SELECT p.nombre FROM rol_permisos rp JOIN roles r ON r.id = rp.rol_id "
            "JOIN permisos p ON p.id = rp.permiso_id WHERE r.nombre = ?",
            (rol,),
        )
        return {row["nombre"] for row in rows}

    assert permisos("admin") == {
        "usuarios.crear",
        "usuarios.consultar",
        "usuarios.actualizar",
        "usuarios.eliminar",
        "historicos.consultar",
    }
    assert permisos("agricultor") == {"usuarios.consultar", "historicos.consultar"}


def test_base_access_migration_does_not_duplicate_existing_data(tmp_path):
    """Una BD sembrada antes de la migración 007 no debe quedar con roles repetidos."""
    database = connect(tmp_path / "old.db")
    migrations = sorted(settings.migrations_path.glob("*.sql"))
    previas = tmp_path / "previas"
    previas.mkdir()
    for archivo in migrations:
        if not archivo.name.startswith("007"):
            (previas / archivo.name).write_text(archivo.read_text(encoding="utf-8"))
    run_migrations(database, previas)
    now = "2026-11-14T00:00:00+00:00"
    database.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES ('admin', ?, ?)", (now, now)
    )
    database.commit()

    run_migrations(database)

    assert database.execute("SELECT COUNT(*) FROM roles WHERE nombre = 'admin'").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 2
    database.close()
