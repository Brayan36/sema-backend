from app.core.base_repository import BaseRepository


class RolRepository(BaseRepository):
    table = "roles"
    columns = ("nombre", "descripcion")
    sortable = ("id", "nombre", "created_at")
    searchable = ("nombre", "descripcion")
