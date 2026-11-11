"""Acceso sin contraseña: enlace por email -> sesión en cookie."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.seguridad import generar_token, hash_token
from app.models import Sesion, TokenAcceso, Usuario

log = logging.getLogger(__name__)


def solicitar_enlace(db: Session, email: str) -> None:
    ajustes = get_settings()
    token = generar_token()
    db.add(
        TokenAcceso(
            email=email.lower(),
            hash=hash_token(token),
            expira=datetime.now(UTC) + timedelta(minutes=ajustes.token_acceso_minutos),
        )
    )
    db.commit()
    # TODO: enviar el email con el enlace (proveedor de correo pendiente de elegir).
    if ajustes.entorno == "local":
        log.info("Enlace de acceso para %s: /acceso/verificar?token=%s", email, token)


def verificar_enlace(db: Session, token: str) -> str | None:
    """Canjea el token del enlace por una sesión. Devuelve el token de sesión o None."""
    fila = db.scalar(
        select(TokenAcceso).where(
            TokenAcceso.hash == hash_token(token), TokenAcceso.expira > datetime.now(UTC)
        )
    )
    if fila is None:
        return None

    usuario = db.scalar(select(Usuario).where(Usuario.email == fila.email))
    if usuario is None:
        usuario = Usuario(email=fila.email)
        db.add(usuario)
        db.flush()

    token_sesion = generar_token()
    db.add(
        Sesion(
            usuario_id=usuario.id,
            hash=hash_token(token_sesion),
            expira=datetime.now(UTC) + timedelta(days=get_settings().sesion_dias),
        )
    )
    db.delete(fila)  # un enlace solo sirve una vez
    db.commit()
    return token_sesion


def cerrar_sesion(db: Session, token_sesion: str) -> None:
    db.execute(delete(Sesion).where(Sesion.hash == hash_token(token_sesion)))
    db.commit()
