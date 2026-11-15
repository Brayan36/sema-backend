"""Convierte cualquier error en el mismo formato JSON:

    {"error": {"code": "NOT_FOUND", "message": "Usuario 7 no existe"}}

Así el frontend maneja todos los errores con una sola función.

Errores 500 (no controlados): el cliente recibe solo un mensaje genérico y un
`error_id`. El detalle completo (traza) va al log del servidor con ese mismo
`error_id`, para poder encontrarlo cuando el frontend reporte el problema.
"""

import logging
import sqlite3
import uuid
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}

# Traducción de los mensajes por defecto del framework (vienen en inglés).
HTTP_ERROR_MESSAGES = {
    401: "No autenticado",
    403: "Acceso denegado",
    404: "Ruta no encontrada",
    405: "Método no permitido",
}

# Mensajes específicos que FastAPI genera en inglés.
FRAMEWORK_MESSAGES = {
    # OAuth2PasswordBearer cuando falta el header Authorization.
    "Not authenticated": "No autenticado",
    # El body no se pudo decodificar (ej. texto que no está en UTF-8).
    "There was an error parsing the body": (
        "No se pudo leer el cuerpo de la petición: debe ser JSON en UTF-8"
    ),
}


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list | None = None,
    headers: dict[str, str] | None = None,
    error_id: str | None = None,
) -> JSONResponse:
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    if error_id:
        error["error_id"] = error_id
    return JSONResponse(status_code=status_code, content={"error": error}, headers=headers)


def internal_error_response(request: Request, exc: Exception) -> JSONResponse:
    """Registra el error con su traza y responde 500 sin filtrar detalles internos."""
    error_id = uuid.uuid4().hex[:12]
    logger.error(
        "Error no controlado [error_id=%s] en %s %s",
        error_id,
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return error_response(500, "INTERNAL_ERROR", "Error interno", error_id=error_id)


# ---------- Handlers ----------


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, headers=exc.headers)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return error_response(422, "VALIDATION_ERROR", "Datos de entrada inválidos", details)


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Errores que genera el propio framework, por ejemplo una ruta que no existe.
    code = HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail)
    if message == HTTPStatus(exc.status_code).phrase:  # mensaje por defecto, en inglés
        message = HTTP_ERROR_MESSAGES.get(exc.status_code, message)
    message = FRAMEWORK_MESSAGES.get(message, message)
    return error_response(exc.status_code, code, message, headers=exc.headers)


async def handle_integrity_error(request: Request, exc: sqlite3.IntegrityError) -> JSONResponse:
    # Red de seguridad: el service debería validar antes (ej. exists_by), pero si
    # un valor único se repite (o llegan dos peticiones a la vez), es un 409.
    if "UNIQUE constraint failed" in str(exc):
        logger.warning("Restricción UNIQUE en %s %s: %s", request.method, request.url.path, exc)
        return error_response(409, "CONFLICT", "Ya existe un registro con esos datos")
    # NOT NULL, FOREIGN KEY, CHECK...: son errores del código, no del cliente.
    return internal_error_response(request, exc)


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return internal_error_response(request, exc)


async def catch_unexpected_errors(request: Request, call_next):
    """Middleware que atrapa los errores no controlados de las rutas.

    Debe quedar DENTRO de CORS (registrarse antes que CORSMiddleware): así la
    respuesta 500 lleva los headers de CORS y el navegador muestra el error real
    en lugar de un falso "error de CORS".
    """
    try:
        return await call_next(request)
    except Exception as exc:
        return internal_error_response(request, exc)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(sqlite3.IntegrityError, handle_integrity_error)
    # Última red de seguridad, por si algo falla fuera de las rutas (ej. en un middleware).
    app.add_exception_handler(Exception, handle_unexpected_error)
    app.middleware("http")(catch_unexpected_errors)
