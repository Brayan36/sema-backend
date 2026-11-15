"""Contrato JSON de permisos."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.core.base_schema import AuditSchema

NombrePermiso = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
]
DescripcionPermiso = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
OrdenPermiso = Literal["id", "nombre", "created_at"]


class PermisoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombrePermiso
    descripcion: DescripcionPermiso | None = None


class PermisoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombrePermiso | None = None
    descripcion: DescripcionPermiso | None = None

    @model_validator(mode="after")
    def rechazar_nombre_nulo(self):
        if "nombre" in self.model_fields_set and self.nombre is None:
            raise ValueError("Estos campos no pueden ser null: nombre")
        return self


class PermisoOut(AuditSchema):
    nombre: str
    descripcion: str | None
