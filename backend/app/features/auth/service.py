from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.database import DbConnection
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.features.asignaciones.repository import AsignacionRepository
from app.features.roles.repository import RolRepository
from app.features.usuarios.repository import ADMIN_ROLE, UsuarioRepository


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
            raise UnauthorizedError("Credenciales inválidas")
        return {"access_token": create_access_token(str(usuario["id"])), "token_type": "bearer"}


def bootstrap_first_user(connection) -> bool:
    repository = UsuarioRepository(connection)
    if repository.count() or not settings.first_user_email or not settings.first_user_password:
        return False
    if repository.get_by("correo", settings.first_user_email, include_deleted=True):
        return False
    usuario = repository.create(
        {
            "nombre": "Administrador inicial",
            "correo": settings.first_user_email.strip().lower(),
            "password_hash": hash_password(settings.first_user_password),
            "genero": None,
            "telefono": None,
            "is_active": True,
        }
    )
    # El primer usuario administra todo: la migración 007 ya creó el rol `admin`.
    rol = RolRepository(connection).get_by("nombre", ADMIN_ROLE)
    if rol is not None:
        AsignacionRepository(connection).asignar_rol(usuario["id"], rol["id"])
    connection.commit()
    return True
