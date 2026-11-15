"""Endpoints de asignación de roles y permisos."""

from fastapi import APIRouter, Depends, status

from app.core.database import DbConnection
from app.features.asignaciones.repository import AsignacionRepository
from app.features.asignaciones.schemas import (
    AsignarRol,
    PermisoResumen,
    RolResumen,
    UsuarioResumen,
    UsuarioRolOut,
)
from app.features.asignaciones.service import AsignacionService

router = APIRouter(prefix="/asignaciones", tags=["asignaciones"])


def get_service(connection: DbConnection) -> AsignacionService:
    return AsignacionService(AsignacionRepository(connection))


@router.put("/usuarios/{usuario_id}/rol")
def asignar_rol(
    usuario_id: int,
    datos: AsignarRol,
    service: AsignacionService = Depends(get_service),
) -> UsuarioRolOut:
    return service.asignar_rol(usuario_id, datos.rol_id)


@router.get("/usuarios/{usuario_id}/rol")
def obtener_rol(
    usuario_id: int, service: AsignacionService = Depends(get_service)
) -> UsuarioRolOut:
    return service.obtener_rol(usuario_id)


@router.delete("/usuarios/{usuario_id}/rol", status_code=status.HTTP_204_NO_CONTENT)
def retirar_rol(usuario_id: int, service: AsignacionService = Depends(get_service)) -> None:
    service.retirar_rol(usuario_id)


@router.get("/roles/{rol_id}/usuarios")
def listar_usuarios_de_rol(
    rol_id: int, service: AsignacionService = Depends(get_service)
) -> list[UsuarioResumen]:
    return service.listar_usuarios_de_rol(rol_id)


@router.put("/roles/{rol_id}/permisos/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
def asignar_permiso(
    rol_id: int, permiso_id: int, service: AsignacionService = Depends(get_service)
) -> None:
    service.asignar_permiso(rol_id, permiso_id)


@router.get("/roles/{rol_id}/permisos")
def listar_permisos_de_rol(
    rol_id: int, service: AsignacionService = Depends(get_service)
) -> list[PermisoResumen]:
    return service.listar_permisos_de_rol(rol_id)


@router.delete("/roles/{rol_id}/permisos/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar_permiso(
    rol_id: int, permiso_id: int, service: AsignacionService = Depends(get_service)
) -> None:
    service.retirar_permiso(rol_id, permiso_id)


@router.get("/permisos/{permiso_id}/roles")
def listar_roles_de_permiso(
    permiso_id: int, service: AsignacionService = Depends(get_service)
) -> list[RolResumen]:
    return service.listar_roles_de_permiso(permiso_id)
