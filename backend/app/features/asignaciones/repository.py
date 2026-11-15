"""Persistencia de las tablas puente del modelo de acceso."""

import sqlite3


class AsignacionRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def usuario_activo(self, usuario_id: int) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM usuarios WHERE id = ? AND deleted_at IS NULL", (usuario_id,)
            ).fetchone()
            is not None
        )

    def rol_activo(self, rol_id: int) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM roles WHERE id = ? AND deleted_at IS NULL", (rol_id,)
            ).fetchone()
            is not None
        )

    def permiso_activo(self, permiso_id: int) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM permisos WHERE id = ? AND deleted_at IS NULL", (permiso_id,)
            ).fetchone()
            is not None
        )

    def asignar_rol(self, usuario_id: int, rol_id: int) -> None:
        self.connection.execute(
            "INSERT INTO usuario_roles (usuario_id, rol_id) VALUES (?, ?) "
            "ON CONFLICT(usuario_id) DO UPDATE SET rol_id = excluded.rol_id",
            (usuario_id, rol_id),
        )

    def obtener_rol_usuario(self, usuario_id: int) -> dict | None:
        row = self.connection.execute(
            "SELECT ur.usuario_id, ur.rol_id, r.nombre, r.descripcion "
            "FROM usuario_roles ur JOIN roles r ON r.id = ur.rol_id "
            "WHERE ur.usuario_id = ? AND r.deleted_at IS NULL",
            (usuario_id,),
        ).fetchone()
        return dict(row) if row else None

    def retirar_rol(self, usuario_id: int) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM usuario_roles WHERE usuario_id = ?", (usuario_id,)
        )
        return cursor.rowcount > 0

    def usuarios_de_rol(self, rol_id: int) -> list[dict]:
        rows = self.connection.execute(
            "SELECT u.id, u.nombre, u.correo, u.is_active "
            "FROM usuario_roles ur JOIN usuarios u ON u.id = ur.usuario_id "
            "WHERE ur.rol_id = ? AND u.deleted_at IS NULL "
            "ORDER BY u.id",
            (rol_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def asignar_permiso(self, rol_id: int, permiso_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO rol_permisos (rol_id, permiso_id) VALUES (?, ?)",
            (rol_id, permiso_id),
        )

    def permisos_de_rol(self, rol_id: int) -> list[dict]:
        rows = self.connection.execute(
            "SELECT p.id, p.nombre, p.descripcion "
            "FROM rol_permisos rp JOIN permisos p ON p.id = rp.permiso_id "
            "WHERE rp.rol_id = ? AND p.deleted_at IS NULL "
            "ORDER BY p.id",
            (rol_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def retirar_permiso(self, rol_id: int, permiso_id: int) -> bool:
        cursor = self.connection.execute(
            "DELETE FROM rol_permisos WHERE rol_id = ? AND permiso_id = ?",
            (rol_id, permiso_id),
        )
        return cursor.rowcount > 0

    def roles_de_permiso(self, permiso_id: int) -> list[dict]:
        rows = self.connection.execute(
            "SELECT r.id, r.nombre, r.descripcion "
            "FROM rol_permisos rp JOIN roles r ON r.id = rp.rol_id "
            "WHERE rp.permiso_id = ? AND r.deleted_at IS NULL "
            "ORDER BY r.id",
            (permiso_id,),
        ).fetchall()
        return [dict(row) for row in rows]
