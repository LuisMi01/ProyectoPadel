from fastapi import APIRouter, status

from app.api.deps import DB, UsuarioOpcional
from app.schemas import ExplicacionOut, PerfilEncuesta, RecomendacionOut, ValoracionIn
from app.services import recomendacion as servicio

router = APIRouter(prefix="/recomendaciones", tags=["Recomendación"])


@router.post("", response_model=RecomendacionOut, status_code=status.HTTP_201_CREATED)
def obtener_recomendacion(perfil: PerfilEncuesta, db: DB, usuario: UsuarioOpcional):
    return servicio.obtener(db, perfil, usuario)


@router.get("/{recomendacion_id}/explicacion", response_model=ExplicacionOut)
def obtener_explicacion(recomendacion_id: int, db: DB):
    texto = servicio.explicar(db, recomendacion_id)
    return ExplicacionOut(recomendacion_id=recomendacion_id, texto=texto)


@router.post("/{recomendacion_id}/valoracion", status_code=status.HTTP_204_NO_CONTENT)
def valorar_recomendacion(recomendacion_id: int, valoracion: ValoracionIn, db: DB):
    servicio.valorar(db, recomendacion_id, valoracion)
