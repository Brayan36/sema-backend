"""CRUD genérico para SQLite, con borrado lógico y protección contra inyección SQL.

Cada repositorio de una feature solo declara su tabla y sus columnas:

    class UsuarioRepository(BaseRepository):
        table = "usuarios"
        columns = ("nombre", "email", "password_hash")
        sortable = ("id", "nombre", "created_at")

Seguridad: SQLite permite pasar VALORES como parámetros `?`, pero no NOMBRES de
tabla o columna. Por eso los nombres solo pueden venir de las listas declaradas en
la clase (lista blanca) y se validan antes de armar la consulta. Este es el único
archivo del proyecto autorizado a usar `# noqa: S608`.
"""

import re
import sqlite3
from typing import Any, ClassVar

from app.core.database import utc_now_iso
from app.core.exceptions import InvalidFieldError

# Columnas que maneja el repositorio base. Las features no las escriben.
AUDIT_COLUMNS = ("id", "created_at", "updated_at", "deleted_at")
SORT_DIRECTIONS = ("ASC", "DESC")
MAX_LIMIT = 100

# Se usa con fullmatch: el nombre completo debe cumplir el patrón (sin espacios ni saltos de línea).
IDENTIFIER_PATTERN = re.compile(r"[a-z_][a-z0-9_]*")


class BaseRepository:
    table: ClassVar[str] = ""
    columns: ClassVar[tuple[str, ...]] = ()  # columnas que se pueden escribir y filtrar
    sortable: ClassVar[tuple[str, ...]] = ("id", "created_at")

    def __init__(self, connection: sqlite3.Connection):
        self._check_declaration()
        self.connection = connection

    # ---------- Lectura ----------

    def get_by_id(self, record_id: int) -> dict | None:
        row = self.connection.execute(
            f"SELECT * FROM {self.table} WHERE id = ? AND deleted_at IS NULL",  # noqa: S608
            (record_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_all(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        direction: str = "ASC",
    ) -> list[dict]:
        if order_by not in self.sortable:
            raise InvalidFieldError(f"No se puede ordenar por '{order_by}'")
        direction = direction.upper()
        if direction not in SORT_DIRECTIONS:
            raise InvalidFieldError(f"Dirección de orden inválida: '{direction}'")
        if not 1 <= limit <= MAX_LIMIT:
            raise InvalidFieldError(f"limit debe estar entre 1 y {MAX_LIMIT}")
        if offset < 0:
            raise InvalidFieldError("offset no puede ser negativo")

        rows = self.connection.execute(
            f"SELECT * FROM {self.table} WHERE deleted_at IS NULL "  # noqa: S608
            f"ORDER BY {order_by} {direction} LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_by(self, column: str, value: Any, include_deleted: bool = False) -> dict | None:
        """Primer registro activo cuya `column` vale `value`, o None si no hay.

        Ejemplo: `repository.get_by("email", "ana@sema.example")`.
        `column` debe estar en `columns` (lista blanca). Con `include_deleted=True`
        también busca entre los eliminados. Para columnas únicas devuelve el único
        registro; si hay varios, el de menor id.
        """
        self._check_columns([column])
        sql = f"SELECT * FROM {self.table} WHERE {column} = ?"  # noqa: S608
        if not include_deleted:
            sql += " AND deleted_at IS NULL"
        row = self.connection.execute(sql + " ORDER BY id LIMIT 1", (value,)).fetchone()
        return dict(row) if row else None

    def count(self) -> int:
        row = self.connection.execute(
            f"SELECT COUNT(*) FROM {self.table} WHERE deleted_at IS NULL"  # noqa: S608
        ).fetchone()
        return row[0]

    def exists_by(
        self,
        column: str,
        value: Any,
        exclude_id: int | None = None,
        include_deleted: bool = False,
    ) -> bool:
        """¿Hay un registro activo con ese valor? `exclude_id` sirve al actualizar,
        para no chocar con el propio registro (ej. email repetido).
        `include_deleted=True` también busca entre los eliminados."""
        self._check_columns([column])
        sql = f"SELECT 1 FROM {self.table} WHERE {column} = ?"  # noqa: S608
        if not include_deleted:
            sql += " AND deleted_at IS NULL"
        params: list[Any] = [value]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        return self.connection.execute(sql + " LIMIT 1", params).fetchone() is not None

    # ---------- Escritura ----------

    def create(self, data: dict) -> dict:
        self._check_columns(data.keys())
        now = utc_now_iso()
        values = {**data, "created_at": now, "updated_at": now}

        names = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        cursor = self.connection.execute(
            f"INSERT INTO {self.table} ({names}) VALUES ({placeholders})",  # noqa: S608
            tuple(values.values()),
        )
        return self.get_by_id(cursor.lastrowid)

    def update(self, record_id: int, data: dict) -> dict | None:
        """Actualiza solo los campos recibidos. Devuelve None si no existe o está eliminado."""
        self._check_columns(data.keys())
        if not data:
            return self.get_by_id(record_id)

        values = {**data, "updated_at": utc_now_iso()}
        assignments = ", ".join(f"{name} = ?" for name in values)
        cursor = self.connection.execute(
            f"UPDATE {self.table} SET {assignments} WHERE id = ? AND deleted_at IS NULL",  # noqa: S608
            (*values.values(), record_id),
        )
        return self.get_by_id(record_id) if cursor.rowcount else None

    def soft_delete(self, record_id: int) -> bool:
        """Marca el registro como eliminado. Devuelve False si no existía o ya estaba eliminado."""
        now = utc_now_iso()
        cursor = self.connection.execute(
            f"UPDATE {self.table} SET deleted_at = ?, updated_at = ? "  # noqa: S608
            "WHERE id = ? AND deleted_at IS NULL",
            (now, now, record_id),
        )
        return cursor.rowcount > 0

    # ---------- Validaciones ----------

    def _check_columns(self, names) -> None:
        """Lista blanca: solo se aceptan columnas declaradas en `columns`."""
        unknown = sorted(set(names) - set(self.columns))
        if unknown:
            raise InvalidFieldError(f"Campos no permitidos: {', '.join(unknown)}")

    def _check_declaration(self) -> None:
        """Detecta errores al declarar un repositorio, antes de ejecutar cualquier SQL."""
        name = type(self).__name__
        if not IDENTIFIER_PATTERN.fullmatch(self.table):
            raise ValueError(f"{name}.table no es un nombre de tabla válido: '{self.table}'")
        for column in self.columns:
            if not IDENTIFIER_PATTERN.fullmatch(column):
                raise ValueError(f"{name}.columns tiene un nombre inválido: '{column}'")
            if column in AUDIT_COLUMNS:
                raise ValueError(f"{name}.columns no debe incluir '{column}' (lo maneja la base)")
        allowed_sort = set(self.columns) | set(AUDIT_COLUMNS)
        invalid_sort = set(self.sortable) - allowed_sort
        if invalid_sort:
            raise ValueError(f"{name}.sortable tiene columnas desconocidas: {invalid_sort}")
