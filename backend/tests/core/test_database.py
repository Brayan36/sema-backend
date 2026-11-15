from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import (
    MigrationError,
    connect,
    local_now,
    migration_status,
    run_migrations,
    to_local,
)


@pytest.fixture
def connection(tmp_path):
    conn = connect(tmp_path / "test.db")
    yield conn
    conn.close()


def test_connection_uses_wal_busy_timeout_and_foreign_keys(connection):
    assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def table_names(connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row["name"] for row in rows}


def test_applies_migrations_in_order(connection, tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "002_add_column.sql").write_text("ALTER TABLE demo ADD COLUMN nombre TEXT;")
    (migrations / "001_create_demo.sql").write_text("CREATE TABLE demo (id INTEGER PRIMARY KEY);")

    applied = run_migrations(connection, migrations)

    assert applied == ["001_create_demo.sql", "002_add_column.sql"]
    assert "demo" in table_names(connection)


def test_does_not_reapply_migrations(connection, tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_demo.sql").write_text("CREATE TABLE demo (id INTEGER PRIMARY KEY);")

    run_migrations(connection, migrations)
    applied_again = run_migrations(connection, migrations)

    assert applied_again == []


def test_migration_status_shows_applied_and_pending(connection, tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_create_demo.sql").write_text("CREATE TABLE demo (id INTEGER PRIMARY KEY);")
    run_migrations(connection, migrations)
    (migrations / "002_create_otra.sql").write_text("CREATE TABLE otra (id INTEGER PRIMARY KEY);")

    status = dict(migration_status(connection, migrations))

    assert status["001_create_demo.sql"] is not None
    assert status["002_create_otra.sql"] is None


def test_failed_migration_is_rolled_back(connection, tmp_path):
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    # La primera sentencia es válida y la segunda falla: no debe quedar nada aplicado.
    (migrations / "001_broken.sql").write_text(
        "CREATE TABLE demo (id INTEGER PRIMARY KEY);\nESTO NO ES SQL;"
    )

    with pytest.raises(MigrationError):
        run_migrations(connection, migrations)

    assert "demo" not in table_names(connection)
    recorded = connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert recorded == 0


# ---------- Hora local (TIMEZONE) ----------


def test_to_local_converts_utc_to_bogota(monkeypatch):
    monkeypatch.setattr(settings, "timezone", "America/Bogota")

    local = to_local("2026-11-09T00:17:45+00:00")  # texto, como viene de la BD

    # Las 00:17 UTC del día 9 son las 7:17 p. m. del día 8 en Colombia.
    assert (local.year, local.month, local.day, local.hour, local.minute) == (2026, 11, 8, 19, 17)
    assert local.utcoffset().total_seconds() == -5 * 3600


def test_to_local_accepts_datetime_and_assumes_utc_when_naive(monkeypatch):
    monkeypatch.setattr(settings, "timezone", "America/Bogota")

    assert to_local(datetime(2026, 11, 9, 0, 17, 45)) == to_local(
        datetime(2026, 11, 9, 0, 17, 45, tzinfo=UTC)
    )


def test_local_now_uses_configured_timezone(monkeypatch):
    monkeypatch.setattr(settings, "timezone", "America/Bogota")

    now = local_now()

    assert str(now.tzinfo) == "America/Bogota"
    assert abs((now - datetime.now(UTC)).total_seconds()) < 5  # mismo instante, otra zona


def test_write_is_committed_before_response_is_sent(app):
    """El commit debe ocurrir antes de responder: el cliente puede leer de inmediato."""
    visible_when_response_returns = []

    @app.middleware("http")
    async def check_other_connection(request, call_next):
        response = await call_next(request)
        if request.method == "POST":
            other = connect(settings.db_path)  # una conexión distinta, como otra petición
            try:
                visible_when_response_returns.append(
                    other.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
                )
            finally:
                other.close()
        return response

    datos = {"nombre": "Ana Pérez", "correo": "ana@sema.example", "password": "clave-segura-1"}
    with TestClient(app) as client:
        assert client.post("/usuarios", json=datos).status_code == 201

    assert visible_when_response_returns == [1]
