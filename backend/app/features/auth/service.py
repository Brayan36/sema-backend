from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.database import DbConnection
from app.core.security import create_access_token, hash_password, verify_password
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import UsuarioOut


class AuthService:
    def __init__(self, connection: DbConnection):
        self.repository = UsuarioRepository(connection)

    def login(self, form: OAuth2PasswordRequestForm) -> dict[str, str]:
        usuario = self.repository.get_by("correo", form.username.strip().lower())
        if (
            usuario is None
            or not usuario["is_active"]
            or not verify_password(form.password, usuario["password_hash"])
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"access_token": create_access_token(str(usuario["id"])), "token_type": "bearer"}


def bootstrap_first_user(connection) -> bool:
    repository = UsuarioRepository(connection)
    if repository.count() or not settings.first_user_email or not settings.first_user_password:
        return False
    if repository.get_by("correo", settings.first_user_email, include_deleted=True):
        return False
    repository.create(
        {
            "nombre": "Administrador inicial",
            "correo": settings.first_user_email.strip().lower(),
            "password_hash": hash_password(settings.first_user_password),
            "genero": None,
            "telefono": None,
            "is_active": True,
        }
    )
    connection.commit()
    return True


def usuario_out(registro: dict) -> UsuarioOut:
    return UsuarioOut.model_validate(registro)
