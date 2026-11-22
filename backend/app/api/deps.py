"""Dependencias comunes de los endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.seguridad import hash_token
from app.db.session import get_db
from app.models import Sesion, Usuario

COOKIE_SESION = "sesion"

DB = Annotated[Session, Depends(get_db)]


def get_usuario_opcional(
    db: DB, sesion: Annotated[str | None, Cookie(alias=COOKIE_SESION)] = None
) -> Usuario | None:
    if not sesion:
        return None
    fila = db.scalar(
        select(Sesion).where(Sesion.hash == hash_token(sesion), Sesion.expira > datetime.now(UTC))
    )
    return db.get(Usuario, fila.usuario_id) if fila else None


def get_usuario_actual(
    usuario: Annotated[Usuario | None, Depends(get_usuario_opcional)],
) -> Usuario:
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión para continuar")
    return usuario


UsuarioOpcional = Annotated[Usuario | None, Depends(get_usuario_opcional)]
UsuarioActual = Annotated[Usuario, Depends(get_usuario_actual)]


def borrar_cookie_sesion(response: Response) -> None:
    """Borra la cookie con los mismos atributos con que se creó (si no, el navegador la ignora)."""
    ajustes = get_settings()
    response.delete_cookie(
        COOKIE_SESION,
        path="/",
        domain=ajustes.cookie_dominio,
        secure=not ajustes.es_local or ajustes.cookie_samesite == "none",
        samesite=ajustes.cookie_samesite,
        httponly=True,
    )
