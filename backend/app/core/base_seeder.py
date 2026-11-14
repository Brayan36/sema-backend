"""Clase base de los seeders: llenan la BD con datos de ejemplo para desarrollo.

Reglas:
- Insertan a través de los repositorios, nunca con SQL suelto.
- Son idempotentes: si el dato ya existe, no lo vuelven a crear.
"""

import sqlite3


class BaseSeeder:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def run(self) -> int:
        """Inserta los datos y devuelve cuántos registros creó."""
        raise NotImplementedError
