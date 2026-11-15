"""Endpoints HTTP de roles."""

from fastapi import APIRouter, Depends, Query

from app.core.base_repository import MAX_LIMIT
from app.core.base_schema import PageSchema, SortDirection
from app.core.database import DbConnection
from app.core.list_filters import ListFilters, list_filters
from app.features.roles.repository import RolRepository
from app.features.roles.schemas import OrdenRol, RolCreate, RolOut, RolUpdate
from app.features.roles.service import RolService

router = APIRouter(prefix="/roles", tags=["roles"])


def get_rol_service(connection: DbConnection) -> RolService:
    return RolService(RolRepository(connection))


@router.post("", status_code=201)
def crear(datos: RolCreate, service: RolService = Depends(get_rol_service)) -> RolOut:
    return service.crear(datos)


@router.get("")
def listar(
    limit: int = Query(20, ge=1, le=MAX_LIMIT, description="Cuántos registros devolver"),
    offset: int = Query(0, ge=0, description="Cuántos registros saltar"),
    order_by: OrdenRol = Query("id", description="Columna para ordenar"),
    direction: SortDirection = Query("asc", description="asc o desc"),
    filtros: ListFilters = Depends(list_filters),
    service: RolService = Depends(get_rol_service),
) -> PageSchema[RolOut]:
    return service.listar(
        limit=limit, offset=offset, order_by=order_by, direction=direction, **filtros.as_kwargs()
    )


@router.get("/{rol_id}")
def obtener(rol_id: int, service: RolService = Depends(get_rol_service)) -> RolOut:
    return service.obtener(rol_id)


@router.patch("/{rol_id}")
def actualizar(
    rol_id: int,
    datos: RolUpdate,
    service: RolService = Depends(get_rol_service),
) -> RolOut:
    return service.actualizar(rol_id, datos)


@router.delete("/{rol_id}", status_code=204)
def eliminar(rol_id: int, service: RolService = Depends(get_rol_service)) -> None:
    service.eliminar(rol_id)
