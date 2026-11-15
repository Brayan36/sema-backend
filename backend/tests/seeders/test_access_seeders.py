from app.core.database import connect, run_migrations
from app.seeders.asignacion_seeder import AsignacionSeeder
from app.seeders.usuario_seeder import UsuarioSeeder


def roles_por_correo(connection) -> dict[str, str]:
    rows = connection.execute(
        "SELECT u.correo, r.nombre FROM usuario_roles ur "
        "JOIN usuarios u ON u.id = ur.usuario_id JOIN roles r ON r.id = ur.rol_id"
    )
    return {row["correo"]: row["nombre"] for row in rows}


def test_seeders_assign_one_admin_and_the_rest_are_agricultores(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)

    UsuarioSeeder(connection).run()
    assert AsignacionSeeder(connection).run() == 4
    connection.commit()

    assert roles_por_correo(connection) == {
        "admin@sema.example": "admin",
        "backend@sema.example": "agricultor",
        "frontend@sema.example": "agricultor",
        "demo@sema.example": "agricultor",
    }
    connection.close()


def test_deleted_demo_user_gets_no_role(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)
    UsuarioSeeder(connection).run()
    AsignacionSeeder(connection).run()

    assert "eliminado@sema.example" not in roles_por_correo(connection)
    connection.close()


def test_access_seeders_are_idempotent(tmp_path):
    connection = connect(tmp_path / "test.db")
    run_migrations(connection)
    UsuarioSeeder(connection).run()
    AsignacionSeeder(connection).run()

    assert AsignacionSeeder(connection).run() == 0
    connection.close()
