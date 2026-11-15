from app.core.base_seeder import BaseSeeder
from app.features.roles.repository import RolRepository

ROLES = [
    {"nombre": "admin", "descripcion": "Administrador del sistema"},
    {"nombre": "agricultor", "descripcion": "Usuario de gestión agrícola"},
]


class RolSeeder(BaseSeeder):
    def run(self) -> int:
        repository = RolRepository(self.connection)
        created = 0
        for rol in ROLES:
            if not repository.exists_by("nombre", rol["nombre"], include_deleted=True):
                repository.create(rol)
                created += 1
        return created
