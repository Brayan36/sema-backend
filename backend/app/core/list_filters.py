"""Filtros comunes de los listados, reutilizables en cualquier router.

Uso en un router:

    @router.get("")
    def listar(
        ...,
        filtros: ListFilters = Depends(list_filters),
    ) -> PageSchema[CultivoOut]:
        return service.listar(..., **filtros.as_kwargs())

Genera estos parámetros en Swagger:
    q             texto a buscar (en las columnas `searchable` del repositorio)
    created_from  creados desde esta fecha y hora (inclusive)
    created_to    creados hasta esta fecha y hora (inclusive)

Las fechas se escriben en ISO 8601, preferiblemente en UTC con `Z`:
`2026-11-14T00:00:00Z`. Sin zona horaria se asumen UTC. Si el offset lleva `+`
(`-05:00` no lo necesita), debe ir codificado en la URL como `%2B`.

Si una feature necesita filtros propios (por ejemplo `estado`), los agrega como
parámetros `Query` en su router y los pasa al service dentro de `filters`.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import Query


@dataclass(frozen=True)
class ListFilters:
    q: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None

    def as_kwargs(self) -> dict[str, Any]:
        """Argumentos listos para `BaseRepository.list_all` y `count`."""
        kwargs: dict[str, Any] = {"search": self.q}
        if self.created_from or self.created_to:
            kwargs["ranges"] = {"created_at": (self.created_from, self.created_to)}
        return kwargs


def list_filters(
    q: str | None = Query(None, min_length=1, max_length=100, description="Texto a buscar"),
    created_from: datetime | None = Query(None, description="Creados desde (inclusive), UTC"),
    created_to: datetime | None = Query(None, description="Creados hasta (inclusive), UTC"),
) -> ListFilters:
    return ListFilters(q=q, created_from=created_from, created_to=created_to)
