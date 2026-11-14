from app.core.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    table = "usuarios"
    columns = ("nombre", "email", "password_hash")
    sortable = ("id", "nombre", "email", "created_at")
