"""Errores propios de la app.

Los services lanzan estas excepciones sin saber nada de HTTP.
`error_handlers.py` las traduce a respuestas JSON con el código correcto.
"""


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    default_message: str = "Error interno"
    headers: dict[str, str] | None = None

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidFieldError(AppError):
    status_code = 400
    code = "INVALID_FIELD"
    default_message = "Campo no permitido"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    default_message = "No autenticado"
    headers = {"WWW-Authenticate": "Bearer"}


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "Recurso no encontrado"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    default_message = "El recurso ya existe"
