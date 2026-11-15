"""Configuración de la app leída desde variables de entorno o el archivo .env.

Ningún otro módulo debe leer os.environ directamente: todo pasa por `settings`.
"""

from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carpeta backend/. Las rutas relativas se resuelven desde aquí, sin importar
# desde qué carpeta se ejecute la app.
BASE_DIR = Path(__file__).resolve().parents[2]

# Valor de ejemplo, solo válido en desarrollo. En producción la app no debe
# arrancar con este secreto (validación pendiente en la fase de autenticación).
INSECURE_JWT_SECRET = "change-me"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SEMA API"
    environment: Literal["development", "production"] = "development"

    # Zona horaria de nuestra ubicación, para la lógica que depende de la hora local.
    # Las fechas se guardan y se entregan en UTC; el frontend las muestra en hora local.
    timezone: str = "America/Bogota"

    db_path: Path = Path("data/sema.db")
    migrations_path: Path = Path("migrations")

    cors_origins: list[str] = ["http://localhost:5173"]

    jwt_secret: str = INSECURE_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    first_user_email: str | None = None
    first_user_password: str | None = None

    @field_validator("db_path", "migrations_path")
    @classmethod
    def resolve_from_base_dir(cls, path: Path) -> Path:
        return path if path.is_absolute() else BASE_DIR / path

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, name: str) -> str:
        # Falla al arrancar (y no a mitad de una petición) si la zona no existe.
        try:
            ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(
                f"TIMEZONE '{name}' no existe. Ejemplo válido: America/Bogota"
            ) from error
        return name

    @field_validator("jwt_expire_minutes")
    @classmethod
    def validate_jwt_expiration(cls, minutes: int) -> int:
        if minutes <= 0:
            raise ValueError("JWT_EXPIRE_MINUTES debe ser mayor que cero")
        return minutes

    @model_validator(mode="after")
    def validate_production_jwt(self):
        if self.environment == "production" and (
            self.jwt_secret == INSECURE_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET debe tener al menos 32 caracteres en producción")
        return self


settings = Settings()
