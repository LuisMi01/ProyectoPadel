from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status

from app.api.deps import COOKIE_SESION, DB
from app.core.config import get_settings
from app.schemas import SolicitudEnlace, VerificarEnlace
from app.services import acceso as servicio

router = APIRouter(prefix="/acceso", tags=["Acceso"])


@router.post("/enlace", status_code=status.HTTP_202_ACCEPTED)
def solicitar_enlace(datos: SolicitudEnlace, db: DB) -> None:
    """Registro e inicio de sesión son el mismo paso: se envía un enlace al email."""
    servicio.solicitar_enlace(db, datos.email)


@router.post("/verificar", status_code=status.HTTP_204_NO_CONTENT)
def verificar_enlace(datos: VerificarEnlace, db: DB, response: Response) -> None:
    token_sesion = servicio.verificar_enlace(db, datos.token)
    if token_sesion is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Enlace no válido o caducado")
    ajustes = get_settings()
    response.set_cookie(
        COOKIE_SESION,
        token_sesion,
        max_age=ajustes.sesion_dias * 86400,
        httponly=True,
        secure=ajustes.entorno != "local",
        samesite="lax",
    )


@router.post("/cerrar", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(
    db: DB, response: Response, sesion: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None
) -> None:
    if sesion:
        servicio.cerrar_sesion(db, sesion)
    response.delete_cookie(COOKIE_SESION)
