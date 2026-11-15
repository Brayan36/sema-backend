"""Schemas de entrada y salida para las asignaciones."""

from pydantic import BaseModel, ConfigDict


class AsignarRol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol_id: int


class UsuarioRolOut(BaseModel):
    usuario_id: int
    rol_id: int
    nombre: str
    descripcion: str | None


class UsuarioResumen(BaseModel):
    id: int
    nombre: str
    correo: str
    is_active: bool


class PermisoResumen(BaseModel):
    id: int
    nombre: str
    descripcion: str | None


class RolResumen(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
