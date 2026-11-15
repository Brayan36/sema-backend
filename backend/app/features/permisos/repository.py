from app.core.base_repository import BaseRepository


class PermisoRepository(BaseRepository):
    table = "permisos"
    columns = ("nombre", "descripcion")
    sortable = ("id", "nombre", "created_at")
    searchable = ("nombre", "descripcion")
