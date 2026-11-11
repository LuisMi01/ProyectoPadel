"""Perfil, palas guardadas, historial y alertas de precio (requieren sesión)."""

from fastapi import APIRouter, Response, status

from app.api.deps import COOKIE_SESION, DB, UsuarioActual
from app.schemas import (
    AlertaIn,
    AlertaOut,
    HistorialItem,
    PalaGuardadaIn,
    PalaGuardadaOut,
    PerfilOut,
)
from app.services import cuenta as servicio

perfil = APIRouter(prefix="/perfil", tags=["Perfil"])
palas = APIRouter(prefix="/palas-guardadas", tags=["Palas guardadas"])
historial = APIRouter(prefix="/historial", tags=["Historial"])
alertas = APIRouter(prefix="/alertas", tags=["Alertas de precio"])


@perfil.get("", response_model=PerfilOut)
def consultar_perfil(usuario: UsuarioActual):
    return usuario


@perfil.delete("", status_code=status.HTTP_204_NO_CONTENT)
def borrar_cuenta(usuario: UsuarioActual, db: DB, response: Response) -> None:
    servicio.borrar_cuenta(db, usuario)
    response.delete_cookie(COOKIE_SESION)


@palas.get("", response_model=list[PalaGuardadaOut])
def listar_palas(usuario: UsuarioActual, db: DB):
    return servicio.listar_palas(db, usuario)


@palas.post("", response_model=PalaGuardadaOut, status_code=status.HTTP_201_CREATED)
def guardar_pala(datos: PalaGuardadaIn, usuario: UsuarioActual, db: DB):
    return servicio.guardar_pala(db, usuario, datos.modelo_id)


@palas.delete("/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_pala(modelo_id: int, usuario: UsuarioActual, db: DB) -> None:
    servicio.quitar_pala(db, usuario, modelo_id)


@historial.get("", response_model=list[HistorialItem])
def consultar_historial(usuario: UsuarioActual, db: DB):
    return servicio.historial(db, usuario)


@alertas.get("", response_model=list[AlertaOut])
def listar_alertas(usuario: UsuarioActual, db: DB):
    return servicio.listar_alertas(db, usuario)


@alertas.post("", response_model=AlertaOut, status_code=status.HTTP_201_CREATED)
def crear_alerta(datos: AlertaIn, usuario: UsuarioActual, db: DB):
    return servicio.crear_alerta(db, usuario, datos.modelo_id, datos.precio_objetivo)


@alertas.delete("/{alerta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_alerta(alerta_id: int, usuario: UsuarioActual, db: DB) -> None:
    servicio.eliminar_alerta(db, usuario, alerta_id)
