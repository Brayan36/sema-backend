"""Endpoints de la entidad.

El router solo traduce HTTP: recibe, delega al service y responde. Cada endpoint
tiene una línea de lógica. Si un endpoint crece, la lógica se está filtrando al
router y debe ir al service.

- La validación de entrada la hace FastAPI con los schemas y con `Query`.
- El tipo de retorno (`-> EjemploOut`) define qué JSON sale: FastAPI descarta cualquier
  campo que no esté en el schema.
- La conexión se pide con `DbConnection` (hace commit ANTES de responder). Nunca
  con `Depends(get_db)` a secas.
- Cuando exista la autenticación: `APIRouter(..., dependencies=[Depends(get_current_user)])`.
  Toda feature nueva va protegida, salvo que sea pública a propósito.
"""

from fastapi import APIRouter, Depends, Query

from app.core.base_repository import MAX_LIMIT
from app.core.base_schema import PageSchema, SortDirection
from app.core.database import DbConnection
from app.core.list_filters import ListFilters, list_filters
from app.features._template.repository import EjemploRepository
from app.features._template.schemas import (
    EjemploCreate,
    EjemploOut,
    EjemploUpdate,
    OrdenEjemplo,
)
from app.features._template.service import EjemploService

router = APIRouter(prefix="/ejemplos", tags=["ejemplos"])


def get_ejemplo_service(connection: DbConnection) -> EjemploService:
    return EjemploService(EjemploRepository(connection))


@router.post("", status_code=201)
def crear(
    datos: EjemploCreate,
    service: EjemploService = Depends(get_ejemplo_service),
) -> EjemploOut:
    return service.crear(datos)


@router.get("")
def listar(
    limit: int = Query(20, ge=1, le=MAX_LIMIT, description="Cuántos registros devolver"),
    offset: int = Query(0, ge=0, description="Cuántos registros saltar"),
    order_by: OrdenEjemplo = Query("id", description="Columna para ordenar"),
    direction: SortDirection = Query("asc", description="asc o desc"),
    filtros: ListFilters = Depends(list_filters),  # q, created_from, created_to
    service: EjemploService = Depends(get_ejemplo_service),
) -> PageSchema[EjemploOut]:
    # Un filtro propio (ej. `estado`) se agrega como parámetro `Query` y se pasa a
    # `service.listar(..., filters={"estado": estado})`.
    return service.listar(
        limit=limit, offset=offset, order_by=order_by, direction=direction, **filtros.as_kwargs()
    )


@router.get("/{ejemplo_id}")
def obtener(
    ejemplo_id: int,
    service: EjemploService = Depends(get_ejemplo_service),
) -> EjemploOut:
    return service.obtener(ejemplo_id)


@router.patch("/{ejemplo_id}")
def actualizar(
    ejemplo_id: int,
    datos: EjemploUpdate,
    service: EjemploService = Depends(get_ejemplo_service),
) -> EjemploOut:
    return service.actualizar(ejemplo_id, datos)


@router.delete("/{ejemplo_id}", status_code=204)
def eliminar(
    ejemplo_id: int,
    service: EjemploService = Depends(get_ejemplo_service),
) -> None:
    service.eliminar(ejemplo_id)
