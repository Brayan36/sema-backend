from app.core.base_repository import BaseRepository

ADMIN_ROLE = "admin"


class UsuarioRepository(BaseRepository):
    table = "usuarios"
    columns = ("nombre", "correo", "password_hash", "genero", "telefono", "is_active")
    sortable = ("id", "nombre", "correo", "created_at")
    searchable = ("nombre", "correo")  # columnas donde busca el filtro `q`

    def es_admin(self, usuario_id: int) -> bool:
        """¿Tiene el rol admin (vigente)? No mira si la cuenta está activa."""
        row = self.connection.execute(
            "SELECT 1 FROM usuario_roles ur JOIN roles r ON r.id = ur.rol_id "
            "WHERE ur.usuario_id = ? AND r.nombre = ? AND r.deleted_at IS NULL",
            (usuario_id, ADMIN_ROLE),
        ).fetchone()
        return row is not None

    def contar_admins_activos(self, excluir_id: int) -> int:
        """Admins que pueden iniciar sesión (activos y no eliminados), sin contar `excluir_id`."""
        return self.connection.execute(
            "SELECT COUNT(*) FROM usuario_roles ur "
            "JOIN roles r ON r.id = ur.rol_id "
            "JOIN usuarios u ON u.id = ur.usuario_id "
            "WHERE r.nombre = ? AND r.deleted_at IS NULL "
            "AND u.deleted_at IS NULL AND u.is_active = 1 AND u.id != ?",
            (ADMIN_ROLE, excluir_id),
        ).fetchone()[0]
