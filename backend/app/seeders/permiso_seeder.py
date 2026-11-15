from app.core.base_seeder import BaseSeeder
from app.features.permisos.repository import PermisoRepository

PERMISOS = [
    {"nombre": "usuarios.crear", "descripcion": "Registrar usuarios"},
    {"nombre": "usuarios.consultar", "descripcion": "Consultar usuarios"},
    {"nombre": "usuarios.actualizar", "descripcion": "Actualizar usuarios"},
    {"nombre": "usuarios.eliminar", "descripcion": "Desactivar usuarios"},
    {"nombre": "historicos.consultar", "descripcion": "Consultar históricos"},
]


class PermisoSeeder(BaseSeeder):
    def run(self) -> int:
        repository = PermisoRepository(self.connection)
        created = 0
        for permiso in PERMISOS:
            if not repository.exists_by("nombre", permiso["nombre"], include_deleted=True):
                repository.create(permiso)
                created += 1
        return created
