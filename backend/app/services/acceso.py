"""Acceso sin contraseña: enlace por correo -> sesión en cookie (docs/ACCESO.md).

Crear cuenta e iniciar sesión son el mismo paso: si el correo no tiene cuenta, se crea al
canjear el enlace. En la base de datos solo se guardan hashes de los tokens.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core import correo
from app.core.config import get_settings
from app.core.seguridad import generar_token, hash_token
from app.models import Sesion, TokenAcceso, Usuario
from app.services.plantillas_correo import enlace_de_acceso


class DemasiadosEnlaces(Exception):
    """Se han pedido demasiados enlaces para el mismo correo en la última hora."""


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def solicitar_enlace(db: Session, email: str) -> None:
    """Crea un token de acceso y envía el enlace por correo.

    Responde igual exista o no la cuenta, para no revelar qué correos están registrados.
    Lanza DemasiadosEnlaces o correo.ErrorCorreo; en ese caso no queda ningún token nuevo.
    """
    ajustes = get_settings()
    email = normalizar_email(email)
    ahora = datetime.now(UTC)
    duracion = timedelta(minutes=ajustes.token_acceso_minutos)

    # token_acceso no guarda la fecha de creación, pero expira = creación + duración, así
    # que "creado en la última hora" equivale a "expira después de ahora - 1 h + duración".
    recientes = db.scalar(
        select(func.count())
        .select_from(TokenAcceso)
        .where(
            TokenAcceso.email == email, TokenAcceso.expira > ahora - timedelta(hours=1) + duracion
        )
    )
    if recientes >= ajustes.enlaces_por_hora:
        raise DemasiadosEnlaces

    token = generar_token()
    db.add(TokenAcceso(email=email, hash=hash_token(token), expira=ahora + duracion))
    db.flush()

    enlace = f"{ajustes.web_url.rstrip('/')}/acceso/verificar/?{urlencode({'token': token})}"
    try:
        correo.enviar(
            enlace_de_acceso(email, enlace, ajustes.nombre_web, ajustes.token_acceso_minutos)
        )
    except correo.ErrorCorreo:
        db.rollback()  # sin correo, el token no sirve a nadie
        raise
    db.commit()


def verificar_enlace(db: Session, token: str) -> str | None:
    """Canjea el token del enlace por una sesión. Devuelve el token de sesión o None."""
    ahora = datetime.now(UTC)
    fila = db.scalar(
        select(TokenAcceso).where(TokenAcceso.hash == hash_token(token), TokenAcceso.expira > ahora)
    )
    if fila is None:
        return None

    usuario = db.scalar(select(Usuario).where(Usuario.email == fila.email))
    if usuario is None:  # primera vez: se crea la cuenta
        usuario = Usuario(email=fila.email)
        db.add(usuario)
        db.flush()

    token_sesion = generar_token()
    db.add(
        Sesion(
            usuario_id=usuario.id,
            hash=hash_token(token_sesion),
            expira=ahora + timedelta(days=get_settings().sesion_dias),
        )
    )
    # Un enlace sirve una vez, y al entrar dejan de valer los demás pedidos para ese correo.
    db.execute(delete(TokenAcceso).where(TokenAcceso.email == fila.email))
    db.commit()
    return token_sesion


def cerrar_sesion(db: Session, token_sesion: str) -> None:
    db.execute(delete(Sesion).where(Sesion.hash == hash_token(token_sesion)))
    db.commit()


def cerrar_todas_las_sesiones(db: Session, usuario: Usuario) -> int:
    """Cierra la sesión en todos los dispositivos. Devuelve cuántas sesiones había."""
    cerradas = db.execute(delete(Sesion).where(Sesion.usuario_id == usuario.id)).rowcount
    db.commit()
    return cerradas
