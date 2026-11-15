"""Dependencias de autorización basadas en el rol único del usuario."""

from collections.abc import Callable

from fastapi import Depends

from app.core.database import DbConnection
from app.core.exceptions import ForbiddenError
from app.features.auth.dependencies import get_current_user
from app.features.usuarios.schemas import UsuarioOut


def require_role(role_name: str) -> Callable:
    def dependency(
        connection: DbConnection,
        current_user: UsuarioOut = Depends(get_current_user),
    ) -> UsuarioOut:
        row = connection.execute(
            "SELECT 1 FROM usuario_roles ur "
            "JOIN roles r ON r.id = ur.rol_id "
            "WHERE ur.usuario_id = ? AND r.nombre = ? AND r.deleted_at IS NULL",
            (current_user.id, role_name),
        ).fetchone()
        if row is None:
            raise ForbiddenError("No tiene el rol requerido")
        return current_user

    return dependency


admin_required = require_role("admin")
