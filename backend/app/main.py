"""Punto de entrada: arma la app (CORS, errores, migraciones y routers).

Ejecutar desde la carpeta backend/:
    python -m uvicorn app.main:app --reload   (en Windows: py -m uvicorn ...)
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import connect, run_migrations
from app.core.error_handlers import register_error_handlers
from app.core.log_config import configure_logging
from app.features.asignaciones.router import router as asignaciones_router
from app.features.auth.authorization import admin_required
from app.features.auth.dependencies import get_current_user
from app.features.auth.router import router as auth_router
from app.features.auth.service import bootstrap_first_user
from app.features.permisos.router import router as permisos_router
from app.features.roles.router import router as roles_router
from app.features.usuarios.router import router as usuarios_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Al arrancar: aplicar migraciones pendientes.
    connection = connect()
    try:
        run_migrations(connection)
        bootstrap_first_user(connection)
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
    protected = {"dependencies": [Depends(get_current_user)]}
    app.include_router(auth_router)
    app.include_router(roles_router, dependencies=[Depends(admin_required)])
    app.include_router(permisos_router, dependencies=[Depends(admin_required)])
    app.include_router(asignaciones_router, dependencies=[Depends(admin_required)])
    app.include_router(usuarios_router, **protected)

    return app


app = create_app()
