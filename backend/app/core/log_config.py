"""Configuración del logging de la app.

Sin esto, los errores registrados con `logger.exception(...)` salen sin fecha ni
formato, mezclados con la salida de uvicorn.
"""

import logging

LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"


def configure_logging(level: int = logging.INFO) -> None:
    # basicConfig no hace nada si el logging ya está configurado (ej. en pytest).
    logging.basicConfig(level=level, format=LOG_FORMAT)
