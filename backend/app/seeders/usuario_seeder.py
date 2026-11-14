from app.core.base_seeder import BaseSeeder
from app.core.security import hash_password
from app.features.usuarios.repository import UsuarioRepository

# Contraseña compartida por todos los usuarios de ejemplo. Solo para desarrollo.
DEMO_PASSWORD = "Sema2026!"  # noqa: S105

USUARIOS = [
    {"nombre": "Admin SEMA", "email": "admin@sema.example"},
    {"nombre": "Equipo Backend", "email": "backend@sema.example"},
    {"nombre": "Usuario Demo", "email": "demo@sema.example"},
    {"nombre": "Equipo Frontend", "email": "frontend@sema.example"},
]

# Se crea y luego se elimina, para ver el borrado lógico en el visor SQL.
USUARIO_ELIMINADO = {"nombre": "Usuario Eliminado", "email": "eliminado@sema.example"}


class UsuarioSeeder(BaseSeeder):
    def run(self) -> int:
        repository = UsuarioRepository(self.connection)
        password_hash = hash_password(DEMO_PASSWORD)
        created = 0

        for usuario in USUARIOS:
            if not repository.exists_by("email", usuario["email"], include_deleted=True):
                repository.create({**usuario, "password_hash": password_hash})
                created += 1

        if not repository.exists_by("email", USUARIO_ELIMINADO["email"], include_deleted=True):
            registro = repository.create({**USUARIO_ELIMINADO, "password_hash": password_hash})
            repository.soft_delete(registro["id"])
            created += 1

        return created
