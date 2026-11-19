from fastapi import APIRouter, HTTPException, status

from app.api.deps import DB, UsuarioOpcional
from app.schemas import ExplicacionOut, PerfilEncuesta, RecomendacionOut, ValoracionIn
from app.services import recomendacion as servicio

router = APIRouter(prefix="/recomendaciones", tags=["Recomendación"])

NO_ENCONTRADA = "Recomendación no encontrada"


@router.post("", response_model=RecomendacionOut, status_code=status.HTTP_201_CREATED)
def obtener_recomendacion(perfil: PerfilEncuesta, db: DB, usuario: UsuarioOpcional):
    try:
        return servicio.obtener(db, perfil, usuario)
    except servicio.SinResultados as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Ninguna pala del catálogo cumple la talla y el presupuesto",
        ) from exc


@router.get("/{recomendacion_id}/explicacion", response_model=ExplicacionOut)
def obtener_explicacion(recomendacion_id: int, db: DB):
    try:
        texto = servicio.explicar(db, recomendacion_id)
    except servicio.NoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA) from exc
    return ExplicacionOut(recomendacion_id=recomendacion_id, texto=texto)


@router.post("/{recomendacion_id}/valoracion", status_code=status.HTTP_204_NO_CONTENT)
def valorar_recomendacion(recomendacion_id: int, valoracion: ValoracionIn, db: DB):
    try:
        servicio.valorar(db, recomendacion_id, valoracion)
    except servicio.NoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA) from exc
