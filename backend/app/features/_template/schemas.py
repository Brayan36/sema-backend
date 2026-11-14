"""Schemas de la entidad: el CONTRATO JSON con el frontend.

Reglas:
- Entrada y salida son schemas SEPARADOS. La salida nunca expone datos sensibles.
- `extra="forbid"` en la entrada: un campo desconocido responde 422.
- En el PATCH, omitir un campo es "no cambiar". Enviar `null` solo se acepta en las
  columnas que admiten NULL; en las NOT NULL se rechaza con 422 (si no, daría un 500).
- Compartir este archivo con el frontend ANTES de seguir: es el acuerdo del contrato.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.core.base_schema import AuditSchema

# ---------- Tipos reutilizables ----------

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Descripcion = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

# Columnas por las que se puede ordenar. Debe coincidir con `EjemploRepository.sortable`
# (un test lo verifica). Swagger las muestra como lista desplegable.
OrdenEjemplo = Literal["id", "nombre", "created_at"]

# Campos del PATCH que NO admiten null (columnas NOT NULL).
CAMPOS_NO_NULOS = ("nombre",)


# ---------- Entrada ----------


class EjemploCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Nombre
    descripcion: Descripcion | None = None


class EjemploUpdate(BaseModel):
    """PATCH: todos los campos son opcionales; solo se cambian los que llegan."""

    model_config = ConfigDict(extra="forbid")

    nombre: Nombre | None = None
    descripcion: Descripcion | None = None

    @model_validator(mode="after")
    def rechazar_nulos(self):
        nulos = sorted(
            campo
            for campo in self.model_fields_set
            if campo in CAMPOS_NO_NULOS and getattr(self, campo) is None
        )
        if nulos:
            raise ValueError(f"Estos campos no pueden ser null: {', '.join(nulos)}")
        return self


# ---------- Salida ----------


class EjemploOut(AuditSchema):
    """Lo que ve el frontend. Sin `deleted_at` (un registro eliminado nunca se devuelve)."""

    nombre: str
    descripcion: str | None
