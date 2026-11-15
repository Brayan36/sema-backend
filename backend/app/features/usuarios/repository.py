from app.core.base_repository import BaseRepository


class UsuarioRepository(BaseRepository):
    table = "usuarios"
    columns = ("nombre", "correo", "password_hash", "genero", "telefono", "is_active")
    sortable = ("id", "nombre", "correo", "created_at")
    searchable = ("nombre", "correo")  # columnas donde busca el filtro `q`
