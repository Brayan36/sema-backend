"""Registro de seeders, en el orden en que se ejecutan.

Para agregar uno nuevo: crear `<entidad>_seeder.py` en esta carpeta y sumarlo a SEEDERS.
Si un seeder depende de otro (ej. registros que pertenecen a un usuario), va después en la lista.
"""

from app.seeders.asignacion_seeder import AsignacionSeeder
from app.seeders.usuario_seeder import UsuarioSeeder

SEEDERS = [
    UsuarioSeeder,
    AsignacionSeeder,
]
