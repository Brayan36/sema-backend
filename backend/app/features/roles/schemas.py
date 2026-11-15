"""Contrato JSON de roles."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.core.base_schema import AuditSchema

NombreRol = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
DescripcionRol = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
OrdenRol = Literal["id", "nombre", "created_at"]


class RolCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombreRol
    descripcion: DescripcionRol | None = None


class RolUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: NombreRol | None = None
    descripcion: DescripcionRol | None = None

    @model_validator(mode="after")
    def rechazar_nombre_nulo(self):
        if "nombre" in self.model_fields_set and self.nombre is None:
            raise ValueError("Estos campos no pueden ser null: nombre")
        return self


class RolOut(AuditSchema):
    nombre: str
    descripcion: str | None
