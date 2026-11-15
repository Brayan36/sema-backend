"""Reglas de negocio de permisos."""

from collections.abc import Mapping
from typing import Any

from app.core.base_repository import RangeValue
from app.core.base_schema import PageSchema
from app.core.exceptions import ConflictError, NotFoundError
from app.features.permisos.repository import PermisoRepository
from app.features.permisos.schemas import PermisoCreate, PermisoOut, PermisoUpdate


class PermisoService:
    def __init__(self, repository: PermisoRepository):
        self.repository = repository

    def crear(self, datos: PermisoCreate) -> PermisoOut:
        self._validar_nombre_disponible(datos.nombre)
        return PermisoOut.model_validate(self.repository.create(datos.model_dump()))

    def listar(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        direction: str = "asc",
        search: str | None = None,
        ranges: Mapping[str, RangeValue] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> PageSchema[PermisoOut]:
        criterios = {"filters": filters, "ranges": ranges, "search": search}
        registros = self.repository.list_all(
            limit=limit, offset=offset, order_by=order_by, direction=direction, **criterios
        )
        return PageSchema[PermisoOut](
            items=[PermisoOut.model_validate(registro) for registro in registros],
            total=self.repository.count(**criterios),
            limit=limit,
            offset=offset,
        )

    def obtener(self, permiso_id: int) -> PermisoOut:
        return PermisoOut.model_validate(self._buscar(permiso_id))

    def actualizar(self, permiso_id: int, datos: PermisoUpdate) -> PermisoOut:
        self._buscar(permiso_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "nombre" in cambios:
            self._validar_nombre_disponible(cambios["nombre"], excluir_id=permiso_id)
        registro = self.repository.update(permiso_id, cambios)
        if registro is None:
            raise NotFoundError(f"Permiso {permiso_id} no existe")
        return PermisoOut.model_validate(registro)

    def eliminar(self, permiso_id: int) -> None:
        if not self.repository.soft_delete(permiso_id):
            raise NotFoundError(f"Permiso {permiso_id} no existe")

    def _buscar(self, permiso_id: int) -> dict:
        registro = self.repository.get_by_id(permiso_id)
        if registro is None:
            raise NotFoundError(f"Permiso {permiso_id} no existe")
        return registro

    def _validar_nombre_disponible(self, nombre: str, excluir_id: int | None = None) -> None:
        if self.repository.exists_by("nombre", nombre, exclude_id=excluir_id):
            raise ConflictError(f"El permiso '{nombre}' ya existe")
