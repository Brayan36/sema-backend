"""Acceso a la BD de la entidad. Solo declara tabla y columnas: el CRUD se hereda.

- `table`: nombre de la tabla (español, plural, snake_case).
- `columns`: columnas que se pueden escribir y filtrar. NO incluir id, created_at,
  updated_at ni deleted_at: las maneja `BaseRepository`.
- `sortable`: columnas por las que se permite ordenar el listado.
"""

from app.core.base_repository import BaseRepository


class EjemploRepository(BaseRepository):
    table = "ejemplos"
    columns = ("nombre", "descripcion")
    sortable = ("id", "nombre", "created_at")
