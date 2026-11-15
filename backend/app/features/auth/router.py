from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import DbConnection
from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import TokenOut
from app.features.auth.service import AuthService
from app.features.usuarios.schemas import UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(connection: DbConnection, form: OAuth2PasswordRequestForm = Depends()) -> TokenOut:
    return AuthService(connection).login(form)


@router.get("/me", response_model=UsuarioOut)
def me(current_user: UsuarioOut = Depends(get_current_user)) -> UsuarioOut:
    return current_user
