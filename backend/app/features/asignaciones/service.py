"""Reglas de negocio para asignar roles y permisos."""

from app.core.exceptions import NotFoundError
from app.features.asignaciones.repository import AsignacionRepository
from app.features.asignaciones.schemas import (
    PermisoResumen,
    RolResumen,
    UsuarioResumen,
    UsuarioRolOut,
)


class AsignacionService:
    def __init__(self, repository: AsignacionRepository):
        self.repository = repository

    def asignar_rol(self, usuario_id: int, rol_id: int) -> UsuarioRolOut:
        self._require_usuario(usuario_id)
        self._require_rol(rol_id)
        self.repository.asignar_rol(usuario_id, rol_id)
        return UsuarioRolOut.model_validate(self.repository.obtener_rol_usuario(usuario_id))

    def obtener_rol(self, usuario_id: int) -> UsuarioRolOut:
        self._require_usuario(usuario_id)
        relacion = self.repository.obtener_rol_usuario(usuario_id)
        if relacion is None:
            raise NotFoundError(f"El usuario {usuario_id} no tiene un rol asignado")
        return UsuarioRolOut.model_validate(relacion)

    def retirar_rol(self, usuario_id: int) -> None:
        self._require_usuario(usuario_id)
        if not self.repository.retirar_rol(usuario_id):
            raise NotFoundError(f"El usuario {usuario_id} no tiene un rol asignado")

    def listar_usuarios_de_rol(self, rol_id: int) -> list[UsuarioResumen]:
        self._require_rol(rol_id)
        return [
            UsuarioResumen.model_validate(row) for row in self.repository.usuarios_de_rol(rol_id)
        ]

    def asignar_permiso(self, rol_id: int, permiso_id: int) -> None:
        self._require_rol(rol_id)
        self._require_permiso(permiso_id)
        self.repository.asignar_permiso(rol_id, permiso_id)

    def listar_permisos_de_rol(self, rol_id: int) -> list[PermisoResumen]:
        self._require_rol(rol_id)
        return [
            PermisoResumen.model_validate(row) for row in self.repository.permisos_de_rol(rol_id)
        ]

    def retirar_permiso(self, rol_id: int, permiso_id: int) -> None:
        self._require_rol(rol_id)
        if not self.repository.retirar_permiso(rol_id, permiso_id):
            raise NotFoundError(f"El permiso {permiso_id} no está asignado al rol {rol_id}")

    def listar_roles_de_permiso(self, permiso_id: int) -> list[RolResumen]:
        self._require_permiso(permiso_id)
        return [
            RolResumen.model_validate(row) for row in self.repository.roles_de_permiso(permiso_id)
        ]

    def _require_usuario(self, usuario_id: int) -> None:
        if not self.repository.usuario_activo(usuario_id):
            raise NotFoundError(f"Usuario {usuario_id} no existe")

    def _require_rol(self, rol_id: int) -> None:
        if not self.repository.rol_activo(rol_id):
            raise NotFoundError(f"Rol {rol_id} no existe")

    def _require_permiso(self, permiso_id: int) -> None:
        if not self.repository.permiso_activo(permiso_id):
            raise NotFoundError(f"Permiso {permiso_id} no existe")
