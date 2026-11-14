"""Lógica de negocio de la entidad.

El service decide QUÉ hacer y en qué ORDEN. No sabe nada de HTTP: no usa `Request`,
`HTTPException` ni códigos de estado. Lanza excepciones del core (`NotFoundError`,
`ConflictError`...) y el handler central las convierte en la respuesta correcta.

Métodos con nombres en español: crear, listar, obtener, actualizar, eliminar.
"""

from app.core.base_schema import PageSchema
from app.core.exceptions import ConflictError, NotFoundError
from app.features._template.repository import EjemploRepository
from app.features._template.schemas import EjemploCreate, EjemploOut, EjemploUpdate


class EjemploService:
    # Composición: el service RECIBE su repositorio. Así los tests le pasan uno con BD temporal.
    # Si necesita otra feature, recibe el SERVICE de esa feature, nunca su repository.
    def __init__(self, repository: EjemploRepository):
        self.repository = repository

    def crear(self, datos: EjemploCreate) -> EjemploOut:
        self._validar_nombre_disponible(datos.nombre)
        registro = self.repository.create(datos.model_dump())
        return EjemploOut.model_validate(registro)

    def listar(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "id",
        direction: str = "asc",
    ) -> PageSchema[EjemploOut]:
        registros = self.repository.list_all(
            limit=limit, offset=offset, order_by=order_by, direction=direction
        )
        return PageSchema[EjemploOut](
            items=[EjemploOut.model_validate(registro) for registro in registros],
            total=self.repository.count(),
            limit=limit,
            offset=offset,
        )

    def obtener(self, ejemplo_id: int) -> EjemploOut:
        return EjemploOut.model_validate(self._buscar(ejemplo_id))

    def actualizar(self, ejemplo_id: int, datos: EjemploUpdate) -> EjemploOut:
        # 1. Primero, que exista: si no existe, es 404 aunque el nombre esté repetido.
        self._buscar(ejemplo_id)

        # 2. Solo los campos que llegaron en el JSON.
        cambios = datos.model_dump(exclude_unset=True)

        if "nombre" in cambios:
            # excluir_id: conservar su propio nombre no es un conflicto.
            self._validar_nombre_disponible(cambios["nombre"], excluir_id=ejemplo_id)

        registro = self.repository.update(ejemplo_id, cambios)
        if registro is None:  # lo eliminaron entre el paso 1 y este
            raise NotFoundError(f"Ejemplo {ejemplo_id} no existe")
        return EjemploOut.model_validate(registro)

    def eliminar(self, ejemplo_id: int) -> None:
        # Borrado lógico: el registro queda en la BD con deleted_at.
        if not self.repository.soft_delete(ejemplo_id):
            raise NotFoundError(f"Ejemplo {ejemplo_id} no existe")

    # ---------- Ayudantes privados ----------

    def _buscar(self, ejemplo_id: int) -> dict:
        registro = self.repository.get_by_id(ejemplo_id)
        if registro is None:
            raise NotFoundError(f"Ejemplo {ejemplo_id} no existe")
        return registro

    def _validar_nombre_disponible(self, nombre: str, excluir_id: int | None = None) -> None:
        if self.repository.exists_by("nombre", nombre, exclude_id=excluir_id):
            raise ConflictError(f"Ya existe un ejemplo llamado '{nombre}'")
