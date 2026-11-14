import pytest
from pydantic import EmailStr, TypeAdapter

from app.core.database import connect, run_migrations
from app.core.security import verify_password
from app.features.usuarios.repository import UsuarioRepository
from app.seeders.usuario_seeder import DEMO_PASSWORD, USUARIO_ELIMINADO, USUARIOS, UsuarioSeeder


@pytest.fixture
def connection(tmp_path):
    conn = connect(tmp_path / "test.db")
    run_migrations(conn)
    yield conn
    conn.close()


def test_creates_active_users_and_one_deleted(connection):
    created = UsuarioSeeder(connection).run()

    repository = UsuarioRepository(connection)
    assert created == len(USUARIOS) + 1
    assert repository.count() == len(USUARIOS)
    assert repository.exists_by("email", "eliminado@sema.example") is False
    assert repository.exists_by("email", "eliminado@sema.example", include_deleted=True) is True


def test_is_idempotent(connection):
    UsuarioSeeder(connection).run()

    assert UsuarioSeeder(connection).run() == 0
    total = connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    assert total == len(USUARIOS) + 1


@pytest.mark.parametrize("usuario", [*USUARIOS, USUARIO_ELIMINADO], ids=lambda u: u["email"])
def test_emails_pass_api_validation(usuario):
    # EmailStr rechaza dominios de uso especial (.local, .test, localhost).
    # Si un email de ejemplo no pasa, la API fallaría al devolver ese usuario.
    assert TypeAdapter(EmailStr).validate_python(usuario["email"]) == usuario["email"]


def test_passwords_are_hashed(connection):
    UsuarioSeeder(connection).run()

    usuario = UsuarioRepository(connection).list_all(limit=1)[0]
    assert usuario["password_hash"] != DEMO_PASSWORD
    assert verify_password(DEMO_PASSWORD, usuario["password_hash"])
