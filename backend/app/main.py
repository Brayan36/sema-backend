"""Punto de entrada: arma la app (CORS, errores, migraciones y routers).

Ejecutar desde la carpeta backend/:
    python -m uvicorn app.main:app --reload   (en Windows: py -m uvicorn ...)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect, run_migrations
from app.core.error_handlers import register_error_handlers
from app.core.log_config import configure_logging
from app.features.usuarios.router import router as usuarios_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Al arrancar: aplicar migraciones pendientes.
    connection = connect()
    try:
        run_migrations(connection)
    finally:
        connection.close()
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    # El ORDEN importa: el último middleware registrado es el más externo.
    # Los errores se registran primero para que CORS los envuelva y las
    # respuestas de error (incluidos los 500) lleven los headers de CORS.
    register_error_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"estado": "ok"}

    # Los routers de cada feature se registran aquí:
    app.include_router(usuarios_router)

    return app


app = create_app()
