from app.core.base_seeder import BaseSeeder

ADMIN_PERMISOS = (
    "usuarios.crear",
    "usuarios.consultar",
    "usuarios.actualizar",
    "usuarios.eliminar",
    "historicos.consultar",
)
AGRICULTOR_PERMISOS = ("usuarios.consultar", "historicos.consultar")


class AsignacionSeeder(BaseSeeder):
    def run(self) -> int:
        created = 0
        admin = self._role_id("admin")
        agricultor = self._role_id("agricultor")
        usuarios = self._usuario_ids()
        if admin is None or agricultor is None:
            return 0

        for correo, rol_id in (("admin@sema.example", admin), ("demo@sema.example", agricultor)):
            usuario_id = usuarios.get(correo)
            if usuario_id is not None:
                cursor = self.connection.execute(
                    "INSERT OR IGNORE INTO usuario_roles (usuario_id, rol_id) VALUES (?, ?)",
                    (usuario_id, rol_id),
                )
                created += cursor.rowcount

        for rol_id, nombres in ((admin, ADMIN_PERMISOS), (agricultor, AGRICULTOR_PERMISOS)):
            for nombre in nombres:
                permiso_id = self._permission_id(nombre)
                if permiso_id is not None:
                    cursor = self.connection.execute(
                        "INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id) VALUES (?, ?)",
                        (rol_id, permiso_id),
                    )
                    created += cursor.rowcount
        return created

    def _role_id(self, nombre: str) -> int | None:
        row = self.connection.execute(
            "SELECT id FROM roles WHERE nombre = ? AND deleted_at IS NULL", (nombre,)
        ).fetchone()
        return row["id"] if row else None

    def _permission_id(self, nombre: str) -> int | None:
        row = self.connection.execute(
            "SELECT id FROM permisos WHERE nombre = ? AND deleted_at IS NULL", (nombre,)
        ).fetchone()
        return row["id"] if row else None

    def _usuario_ids(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT id, correo FROM usuarios WHERE deleted_at IS NULL"
        ).fetchall()
        return {row["correo"]: row["id"] for row in rows}
