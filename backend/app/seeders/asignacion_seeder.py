from app.core.base_seeder import BaseSeeder

# Los roles y permisos base los crea la migración 007. Aquí solo se asignan a los usuarios
# de ejemplo: un único admin; backend, frontend y demo son agricultores.
ROLES_DE_EJEMPLO = {
    "admin@sema.example": "admin",
    "backend@sema.example": "agricultor",
    "frontend@sema.example": "agricultor",
    "demo@sema.example": "agricultor",
}


class AsignacionSeeder(BaseSeeder):
    def run(self) -> int:
        created = 0
        for correo, rol in ROLES_DE_EJEMPLO.items():
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO usuario_roles (usuario_id, rol_id) "
                "SELECT u.id, r.id FROM usuarios u JOIN roles r "
                "WHERE u.correo = ? AND u.deleted_at IS NULL "
                "AND r.nombre = ? AND r.deleted_at IS NULL",
                (correo, rol),
            )
            created += cursor.rowcount
        return created
