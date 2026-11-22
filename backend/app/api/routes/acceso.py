from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status

from app.api.deps import COOKIE_SESION, DB, UsuarioActual, borrar_cookie_sesion
from app.core.config import get_settings
from app.core.correo import ErrorCorreo
from app.schemas import SolicitudEnlace, VerificarEnlace
from app.services import acceso as servicio

router = APIRouter(prefix="/acceso", tags=["Acceso"])


@router.post("/enlace", status_code=status.HTTP_202_ACCEPTED)
def solicitar_enlace(datos: SolicitudEnlace, db: DB, request: Request) -> None:
    """Crear cuenta e iniciar sesión son el mismo paso: se envía un enlace al correo.

    Responde 202 exista o no la cuenta, para no revelar qué correos están registrados.
    La IP sale de request.client: detrás de un proxy, uvicorn debe arrancar con
    --proxy-headers --forwarded-allow-ips (docs/ACCESO.md, "Despliegue").
    """
    ip = request.client.host if request.client else None
    try:
        servicio.solicitar_enlace(db, datos.email, ip)
    except servicio.DemasiadosEnlaces:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Has pedido varios enlaces seguidos. Espera unos minutos y vuelve a intentarlo.",
        ) from None
    except ErrorCorreo:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No hemos podido enviar el correo. Inténtalo de nuevo en unos minutos.",
        ) from None


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
        # SameSite=None exige Secure; fuera de local, siempre HTTPS.
        secure=not ajustes.es_local or ajustes.cookie_samesite == "none",
        samesite=ajustes.cookie_samesite,
        domain=ajustes.cookie_dominio,
        path="/",
    )


@router.post("/cerrar", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(
    db: DB, response: Response, sesion: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None
) -> None:
    if sesion:
        servicio.cerrar_sesion(db, sesion)
    borrar_cookie_sesion(response)


@router.post("/cerrar-todas", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_todas_las_sesiones(usuario: UsuarioActual, db: DB, response: Response) -> None:
    """Cierra la sesión en todos los dispositivos (p. ej. tras perder el móvil)."""
    servicio.cerrar_todas_las_sesiones(db, usuario)
    borrar_cookie_sesion(response)
