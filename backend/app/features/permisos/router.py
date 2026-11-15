"""Endpoints HTTP de permisos."""

from fastapi import APIRouter, Depends, Query

from app.core.base_repository import MAX_LIMIT
from app.core.base_schema import PageSchema, SortDirection
from app.core.database import DbConnection
from app.core.list_filters import ListFilters, list_filters
from app.features.permisos.repository import PermisoRepository
from app.features.permisos.schemas import OrdenPermiso, PermisoCreate, PermisoOut, PermisoUpdate
from app.features.permisos.service import PermisoService

router = APIRouter(prefix="/permisos", tags=["permisos"])


def get_permiso_service(connection: DbConnection) -> PermisoService:
    return PermisoService(PermisoRepository(connection))


@router.post("", status_code=201)
def crear(
    datos: PermisoCreate, service: PermisoService = Depends(get_permiso_service)
) -> PermisoOut:
    return service.crear(datos)


@router.get("")
def listar(
    limit: int = Query(20, ge=1, le=MAX_LIMIT, description="Cuántos registros devolver"),
    offset: int = Query(0, ge=0, description="Cuántos registros saltar"),
    order_by: OrdenPermiso = Query("id", description="Columna para ordenar"),
    direction: SortDirection = Query("asc", description="asc o desc"),
    filtros: ListFilters = Depends(list_filters),
    service: PermisoService = Depends(get_permiso_service),
) -> PageSchema[PermisoOut]:
    return service.listar(
        limit=limit, offset=offset, order_by=order_by, direction=direction, **filtros.as_kwargs()
    )


@router.get("/{permiso_id}")
def obtener(permiso_id: int, service: PermisoService = Depends(get_permiso_service)) -> PermisoOut:
    return service.obtener(permiso_id)


@router.patch("/{permiso_id}")
def actualizar(
    permiso_id: int,
    datos: PermisoUpdate,
    service: PermisoService = Depends(get_permiso_service),
) -> PermisoOut:
    return service.actualizar(permiso_id, datos)


@router.delete("/{permiso_id}", status_code=204)
def eliminar(permiso_id: int, service: PermisoService = Depends(get_permiso_service)) -> None:
    service.eliminar(permiso_id)
