import pytest

import manage
from app.core.config import settings
from app.core.database import connect


@pytest.fixture(autouse=True)
def temp_database(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", tmp_path / "test.db")


def count_usuarios() -> int:
    connection = connect()
    try:
        return connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    finally:
        connection.close()


def test_migrate_then_status(capsys):
    manage.main(["migrate"])
    manage.main(["migrate:status"])

    output = capsys.readouterr().out
    assert "Migrada: 001_create_usuarios.sql" in output
    assert "[x] 001_create_usuarios.sql" in output


def test_migrate_twice_reports_nothing_pending(capsys):
    manage.main(["migrate"])
    manage.main(["migrate"])

    assert "No hay migraciones pendientes." in capsys.readouterr().out


def test_db_seed_creates_users():
    manage.main(["db:seed"])

    assert count_usuarios() == 5


def test_db_seed_with_unknown_class_fails():
    with pytest.raises(SystemExit, match="no existe"):
        manage.main(["db:seed", "--class", "NoExisteSeeder"])


def test_migrate_fresh_with_seed_rebuilds_database():
    manage.main(["db:seed"])
    connection = connect()
    connection.execute("DELETE FROM usuarios")
    connection.commit()
    connection.close()

    manage.main(["migrate:fresh", "--seed"])

    assert count_usuarios() == 5


@pytest.mark.parametrize("command", [["migrate:fresh"], ["db:seed"]])
def test_dev_only_commands_are_blocked_in_production(monkeypatch, command):
    monkeypatch.setattr(settings, "environment", "production")

    with pytest.raises(SystemExit, match="production"):
        manage.main(command)
