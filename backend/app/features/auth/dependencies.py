from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.database import DbConnection
from app.core.security import decode_access_token
from app.features.usuarios.repository import UsuarioRepository
from app.features.usuarios.schemas import UsuarioOut

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(connection: DbConnection, token: str = Depends(oauth2_scheme)) -> UsuarioOut:
    try:
        subject = decode_access_token(token)
        usuario_id = int(subject)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    registro = UsuarioRepository(connection).get_by_id(usuario_id)
    if registro is None or not registro["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UsuarioOut.model_validate(registro)
