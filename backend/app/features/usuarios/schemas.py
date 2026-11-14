"""Schemas de usuarios: el CONTRATO con el frontend.

Definen qué JSON se recibe (entrada) y qué JSON se devuelve (salida). Pydantic
valida automáticamente: si algo no cumple, FastAPI responde 422 sin que el
router ni el service tengan que hacer nada.

Regla: los schemas de entrada y de salida son SEPARADOS. La entrada recibe
`password`; la salida nunca incluye la contraseña ni su hash.
"""

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    StringConstraints,
    model_validator,
)

from app.core.base_schema import AuditSchema

# ---------- Tipos reutilizables ----------


def normalizar_email(email):
    """'  Admin@SEMA.example ' y 'admin@sema.example' deben ser el mismo usuario."""
    return email.strip().lower() if isinstance(email, str) else email


# BeforeValidator: se normaliza ANTES de validar el formato del email.
EmailNormalizado = Annotated[EmailStr, BeforeValidator(normalizar_email)]

# strip_whitespace: "   " queda vacío y no pasa el mínimo de 2 caracteres.
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]

# La contraseña NO se recorta: los espacios pueden ser parte de ella.
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]

# Columnas por las que se puede ordenar el listado. Debe coincidir con
# `UsuarioRepository.sortable` (un test lo verifica). Swagger las muestra como lista.
OrdenUsuario = Literal["id", "nombre", "email", "created_at"]


# ---------- Entrada ----------


class UsuarioCreate(BaseModel):
    # extra="forbid": un campo desconocido (ej. "deleted_at") responde 422 en vez
    # de ignorarse en silencio.
    model_config = ConfigDict(extra="forbid")

    nombre: Nombre
    email: EmailNormalizado
    password: Password


class UsuarioUpdate(BaseModel):
    """PATCH: todos los campos son opcionales; solo se cambian los que llegan."""

    model_config = ConfigDict(extra="forbid")

    nombre: Nombre | None = None
    email: EmailNormalizado | None = None
    password: Password | None = None

    @model_validator(mode="after")
    def rechazar_nulos(self):
        # Un campo omitido significa "no cambiar". Un campo enviado como null
        # intentaría guardar NULL en una columna NOT NULL (y daría un 500).
        nulos = sorted(campo for campo in self.model_fields_set if getattr(self, campo) is None)
        if nulos:
            raise ValueError(f"Estos campos no pueden ser null: {', '.join(nulos)}")
        return self


# ---------- Salida ----------


class UsuarioOut(AuditSchema):
    """Lo que ve el frontend. Sin password_hash ni deleted_at.

    `email` es `str` y no `EmailStr`: el email ya se validó al entrar, y validar
    otra vez al salir solo podría convertir un dato viejo en un error 500.
    """

    nombre: str
    email: str
