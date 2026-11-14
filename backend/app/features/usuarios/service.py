"""Lógica de negocio de usuarios.

El service decide QUÉ hacer y en qué ORDEN. No sabe nada de HTTP: no usa
`Request`, `HTTPException` ni códigos de estado. Cuando algo falla, lanza una
excepción del core (`NotFoundError`, `ConflictError`) y el handler central la
convierte en la respuesta HTTP correcta.
"""

from collections.abc import Mapping
from typing import Any

from app.core.base_repository import RangeValue
from app.core.base_schema import PageSchema
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate


class UsuarioService:
    # Composición: el service RECIBE su repositorio en vez de crearlo. Así en los
    # tests se le puede pasar un repositorio con una BD temporal.
    def __init__(self, repository: UsuarioRepository):
        self.repository = repository

    def crear(self, datos: UsuarioCreate) -> UsuarioOut:
        self._validar_email_disponible(datos.email)
        registro = self.repository.create(
            {
                "nombre": datos.nombre,
                "email": datos.email,
                "password_hash": hash_password(datos.password),  # nunca en texto plano
            }
        )
        return UsuarioOut.model_validate(registro)

    def listar(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        direction: str = "asc",
        search: str | None = None,
        ranges: Mapping[str, RangeValue] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> PageSchema[UsuarioOut]:
        # Los mismos filtros van al listado y al conteo: `total` cuenta lo filtrado.
        criterios = {"filters": filters, "ranges": ranges, "search": search}
        registros = self.repository.list_all(
            limit=limit, offset=offset, order_by=order_by, direction=direction, **criterios
        )
        return PageSchema[UsuarioOut](
            items=[UsuarioOut.model_validate(registro) for registro in registros],
            total=self.repository.count(**criterios),
            limit=limit,
            offset=offset,
        )

    def obtener(self, usuario_id: int) -> UsuarioOut:
        return UsuarioOut.model_validate(self._buscar(usuario_id))

    def actualizar(self, usuario_id: int, datos: UsuarioUpdate) -> UsuarioOut:
        # 1. Primero, que exista: si no existe, es 404 aunque el email esté repetido.
        self._buscar(usuario_id)

        # 2. Solo los campos que llegaron en el JSON (exclude_unset).
        cambios = datos.model_dump(exclude_unset=True)

        if "email" in cambios:
            # exclude_id: conservar su propio email no es un conflicto.
            self._validar_email_disponible(cambios["email"], excluir_id=usuario_id)
        if "password" in cambios:
            cambios["password_hash"] = hash_password(cambios.pop("password"))

        registro = self.repository.update(usuario_id, cambios)
        if registro is None:  # alguien lo eliminó entre el paso 1 y este
            raise NotFoundError(f"Usuario {usuario_id} no existe")
        return UsuarioOut.model_validate(registro)

    def eliminar(self, usuario_id: int) -> None:
        # Borrado lógico: el registro queda en la BD con deleted_at.
        if not self.repository.soft_delete(usuario_id):
            raise NotFoundError(f"Usuario {usuario_id} no existe")

    # ---------- Ayudantes privados ----------

    def _buscar(self, usuario_id: int) -> dict:
        registro = self.repository.get_by_id(usuario_id)
        if registro is None:
            raise NotFoundError(f"Usuario {usuario_id} no existe")
        return registro

    def _validar_email_disponible(self, email: str, excluir_id: int | None = None) -> None:
        if self.repository.exists_by("email", email, exclude_id=excluir_id):
            raise ConflictError(f"El email {email} ya está registrado")
