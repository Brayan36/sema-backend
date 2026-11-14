"""Endpoints de usuarios.

El router solo traduce HTTP: recibe, delega al service y responde. Cada
endpoint tiene 1 línea de lógica. Si un endpoint crece, la lógica se está
filtrando al router y debe ir al service.

- La validación de entrada la hace FastAPI con los schemas y con `Query`.
- El tipo de retorno (`-> UsuarioOut`) define qué JSON se devuelve: FastAPI
  filtra cualquier campo que no esté en el schema (ej. password_hash).
- Autenticación (pendiente): aquí se agregará `dependencies=[Depends(get_current_user)]`.
"""

from fastapi import APIRouter, Depends, Query

from app.core.base_repository import MAX_LIMIT
from app.core.base_schema import PageSchema, SortDirection
from app.core.database import DbConnection
from app.core.list_filters import ListFilters, list_filters
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import OrdenUsuario, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.features.usuarios.service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def get_usuario_service(connection: DbConnection) -> UsuarioService:
    """Arma el service con una conexión de esta petición (hace commit o rollback al terminar)."""
    return UsuarioService(UsuarioRepository(connection))


@router.post("", status_code=201)
def crear(
    datos: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOut:
    return service.crear(datos)


@router.get("")
def listar(
    limit: int = Query(20, ge=1, le=MAX_LIMIT, description="Cuántos registros devolver"),
    offset: int = Query(0, ge=0, description="Cuántos registros saltar"),
    order_by: OrdenUsuario = Query("id", description="Columna para ordenar"),
    direction: SortDirection = Query("asc", description="asc o desc"),
    filtros: ListFilters = Depends(list_filters),
    service: UsuarioService = Depends(get_usuario_service),
) -> PageSchema[UsuarioOut]:
    return service.listar(
        limit=limit, offset=offset, order_by=order_by, direction=direction, **filtros.as_kwargs()
    )


@router.get("/{usuario_id}")
def obtener(
    usuario_id: int,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOut:
    return service.obtener(usuario_id)


@router.patch("/{usuario_id}")
def actualizar(
    usuario_id: int,
    datos: UsuarioUpdate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioOut:
    return service.actualizar(usuario_id, datos)


@router.delete("/{usuario_id}", status_code=204)
def eliminar(
    usuario_id: int,
    service: UsuarioService = Depends(get_usuario_service),
) -> None:
    service.eliminar(usuario_id)
