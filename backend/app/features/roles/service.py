"""Reglas de negocio de roles."""

from collections.abc import Mapping
from typing import Any

from app.core.base_repository import RangeValue
from app.core.base_schema import PageSchema
from app.core.exceptions import ConflictError, NotFoundError
from app.features.roles.repository import RolRepository
from app.features.roles.schemas import RolCreate, RolOut, RolUpdate


class RolService:
    def __init__(self, repository: RolRepository):
        self.repository = repository

    def crear(self, datos: RolCreate) -> RolOut:
        self._validar_nombre_disponible(datos.nombre)
        return RolOut.model_validate(self.repository.create(datos.model_dump()))

    def listar(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        direction: str = "asc",
        search: str | None = None,
        ranges: Mapping[str, RangeValue] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> PageSchema[RolOut]:
        criterios = {"filters": filters, "ranges": ranges, "search": search}
        registros = self.repository.list_all(
            limit=limit, offset=offset, order_by=order_by, direction=direction, **criterios
        )
        return PageSchema[RolOut](
            items=[RolOut.model_validate(registro) for registro in registros],
            total=self.repository.count(**criterios),
            limit=limit,
            offset=offset,
        )

    def obtener(self, rol_id: int) -> RolOut:
        return RolOut.model_validate(self._buscar(rol_id))

    def actualizar(self, rol_id: int, datos: RolUpdate) -> RolOut:
        self._buscar(rol_id)
        cambios = datos.model_dump(exclude_unset=True)
        if "nombre" in cambios:
            self._validar_nombre_disponible(cambios["nombre"], excluir_id=rol_id)
        registro = self.repository.update(rol_id, cambios)
        if registro is None:
            raise NotFoundError(f"Rol {rol_id} no existe")
        return RolOut.model_validate(registro)

    def eliminar(self, rol_id: int) -> None:
        if not self.repository.soft_delete(rol_id):
            raise NotFoundError(f"Rol {rol_id} no existe")

    def _buscar(self, rol_id: int) -> dict:
        registro = self.repository.get_by_id(rol_id)
        if registro is None:
            raise NotFoundError(f"Rol {rol_id} no existe")
        return registro

    def _validar_nombre_disponible(self, nombre: str, excluir_id: int | None = None) -> None:
        if self.repository.exists_by("nombre", nombre, exclude_id=excluir_id):
            raise ConflictError(f"El rol '{nombre}' ya existe")
