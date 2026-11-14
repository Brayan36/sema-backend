"""Conexión a SQLite, migraciones y utilidades de fecha.

- `get_db`: dependencia de FastAPI que entrega una conexión por petición.
- `run_migrations`: aplica, en orden, los archivos .sql pendientes de migrations/.
- `utc_now_iso`, `local_now`, `to_local`: fechas. Se GUARDAN en UTC; la hora local
  (zona de `settings.timezone`) solo se usa en la lógica que depende de nuestra
  ubicación, por ejemplo saber qué día o mes es hoy en Colombia.
"""

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends

from app.core.config import settings


def utc_now_iso() -> str:
    """Fecha y hora actual en UTC, formato ISO 8601 (así se guardan todas las fechas)."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def local_now() -> datetime:
    """Fecha y hora actual en la zona horaria configurada (TIMEZONE)."""
    return datetime.now(ZoneInfo(settings.timezone))


def to_local(value: datetime | str) -> datetime:
    """Convierte una fecha UTC (datetime o texto ISO, como viene de la BD) a hora local.

    Ejemplo con TIMEZONE=America/Bogota:
        to_local("2026-11-09T00:17:45+00:00")  ->  2026-11-08 19:17:45-05:00
    """
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:  # sin zona: se asume UTC, que es como se guarda todo
        value = value.replace(tzinfo=UTC)
    return value.astimezone(ZoneInfo(settings.timezone))


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    # check_same_thread=False: FastAPI puede abrir la conexión en un hilo y usarla
    # en otro dentro de la MISMA petición. Es seguro porque nunca se comparte
    # entre peticiones.
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row  # leer columnas por nombre: row["email"]
    connection.execute("PRAGMA foreign_keys = ON")  # SQLite no lo activa por defecto
    # WAL: los lectores no bloquean al que escribe (y al revés). busy_timeout: si la
    # BD está ocupada, espera hasta 5 s en vez de fallar con "database is locked".
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def get_db() -> Iterator[sqlite3.Connection]:
    """Una conexión por petición: commit si todo sale bien, rollback si hay error."""
    connection = connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# Así se pide la conexión en un router: `connection: DbConnection`.
# scope="function" hace que el commit (o rollback) de get_db ocurra ANTES de enviar la
# respuesta. Sin él, FastAPI lo ejecuta después: el cliente podría recibir el 201 y
# hacer un GET inmediato sin ver todavía el dato que acaba de guardar.
DbConnection = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]


class MigrationError(Exception):
    pass


def run_migrations(
    connection: sqlite3.Connection, migrations_path: Path | None = None
) -> list[str]:
    """Aplica las migraciones pendientes y devuelve los nombres de las aplicadas.

    Cada archivo corre en su propia transacción junto con su registro en
    schema_migrations: o se aplica completo, o no se aplica nada.
    """
    path = migrations_path or settings.migrations_path
    applied = _applied_migrations(connection)
    newly_applied = []

    for file in sorted(path.glob("*.sql")):
        if file.name in applied:
            continue
        script = file.read_text(encoding="utf-8")
        try:
            # executescript no acepta parámetros ni abre transacción por sí solo,
            # por eso se antepone BEGIN y el registro se inserta antes del commit.
            connection.executescript("BEGIN;\n" + script)
            connection.execute(
                "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                (file.name, utc_now_iso()),
            )
            connection.commit()
        except sqlite3.Error as error:
            connection.rollback()
            raise MigrationError(f"Falló la migración {file.name}: {error}") from error
        newly_applied.append(file.name)

    return newly_applied


def migration_status(
    connection: sqlite3.Connection, migrations_path: Path | None = None
) -> list[tuple[str, str | None]]:
    """Lista (archivo, fecha de aplicación). La fecha es None si está pendiente."""
    path = migrations_path or settings.migrations_path
    applied = _applied_migrations(connection)
    return [(file.name, applied.get(file.name)) for file in sorted(path.glob("*.sql"))]


def _applied_migrations(connection: sqlite3.Connection) -> dict[str, str]:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    connection.commit()
    rows = connection.execute("SELECT filename, applied_at FROM schema_migrations")
    return {row["filename"]: row["applied_at"] for row in rows}
