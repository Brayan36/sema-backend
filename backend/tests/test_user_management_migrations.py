"""Contrato físico de la fase 1: usuarios, roles y permisos."""

import sqlite3

import pytest

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
    connection.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("admin", now, now),
    )
    connection.execute(
        "INSERT INTO roles (nombre, created_at, updated_at) VALUES (?, ?, ?)",
        ("agricultor", now, now),
    )
    connection.execute("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, 1)")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (1, 2)")
