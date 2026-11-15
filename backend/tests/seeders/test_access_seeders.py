from app.core.database import connect, run_migrations
from app.seeders.asignacion_seeder import AsignacionSeeder
from app.seeders.permiso_seeder import PermisoSeeder
from app.seeders.rol_seeder import RolSeeder
from app.seeders.usuario_seeder import UsuarioSeeder


def test_access_seeders_create_catalogs_and_assignments(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)

    UsuarioSeeder(connection).run()
    assert RolSeeder(connection).run() == 2
    assert PermisoSeeder(connection).run() == 5
    created = AsignacionSeeder(connection).run()
    connection.commit()

    assert created == 9
    assert connection.execute("SELECT COUNT(*) FROM usuario_roles").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM rol_permisos").fetchone()[0] == 7
    connection.close()


def test_access_seeders_are_idempotent(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)
    UsuarioSeeder(connection).run()
    RolSeeder(connection).run()
    PermisoSeeder(connection).run()
    AsignacionSeeder(connection).run()

    assert RolSeeder(connection).run() == 0
    assert PermisoSeeder(connection).run() == 0
    assert AsignacionSeeder(connection).run() == 0
    connection.close()
