"""Acceso a la BD de la entidad. Solo declara tabla y columnas: el CRUD se hereda.

- `table`: nombre de la tabla (español, plural, snake_case).
- `columns`: columnas que se pueden escribir y filtrar. NO incluir id, created_at,
  updated_at ni deleted_at: las maneja `BaseRepository`.
- `sortable`: columnas por las que se permite ordenar el listado.
- `searchable`: columnas de texto donde busca el filtro `q` (puede quedar vacío).
"""

from app.core.base_repository import BaseRepository


class EjemploRepository(BaseRepository):
    table = "ejemplos"
    columns = ("nombre", "descripcion")
    sortable = ("id", "nombre", "created_at")
    searchable = ("nombre", "descripcion")  # columnas donde busca el filtro `q`
