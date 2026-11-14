"""Schemas y tipos comunes a todas las features.

- `AuditSchema`: campos comunes de los schemas de salida. Los `...Out` de cada
  feature heredan de aquí. `deleted_at` no se expone porque un registro eliminado
  nunca se devuelve.
- `PageSchema[T]`: respuesta paginada genérica (lista + total).
- `SortDirection`: dirección de orden aceptada en los listados.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SortDirection = Literal["asc", "desc"]


class AuditSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime


class PageSchema[T](BaseModel):
    """Una página de resultados. Se usa indicando el tipo: `PageSchema[UsuarioOut]`.

    `[T]` es un "tipo genérico": T se reemplaza por el schema de cada feature, así
    una sola clase sirve para paginar usuarios o cualquier otra entidad.

    `total` es la cantidad de registros activos (sin contar eliminados), para que el
    frontend sepa cuántas páginas hay.
    """

    items: list[T]
    total: int
    limit: int
    offset: int
