"""Recomendaciones calculadas en el navegador: se guardan, se explican y se valoran."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import DB, NuevaSesion, UsuarioOpcional
from app.schemas import ExplicacionOut, RecomendacionGuardadaOut, RecomendacionIn, ValoracionIn
from app.services import recomendacion as servicio

router = APIRouter(prefix="/recomendaciones", tags=["Recomendación"])

NO_ENCONTRADA = "Recomendación no encontrada"


@router.post("", response_model=RecomendacionGuardadaOut, status_code=status.HTTP_201_CREATED)
def guardar_recomendacion(datos: RecomendacionIn, db: DB, usuario: UsuarioOpcional):
    """Guarda lo que el navegador ha enseñado. Devuelve el id para la explicación y los clics."""
    try:
        return servicio.guardar(db, datos, usuario)
    except servicio.PalaDesconocida as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Alguna pala no está en el catálogo"
        ) from exc


@router.get("/{recomendacion_id}/explicacion", response_model=ExplicacionOut)
def obtener_explicacion(recomendacion_id: int, db: DB):
    try:
        texto = servicio.explicar(db, recomendacion_id)
    except servicio.NoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA) from exc
    return ExplicacionOut(recomendacion_id=recomendacion_id, texto=texto)


@router.get("/{recomendacion_id}/explicacion/flujo")
def explicacion_en_flujo(recomendacion_id: int, db: DB, nueva_sesion: NuevaSesion):
    """La explicación según la IA la va escribiendo (Server-Sent Events).

    Eventos: `texto` ({"t": trozo}) mientras se escribe y `fin` ({"texto", "origen"}) al acabar.
    `fin` trae siempre el texto definitivo: si es la plantilla, sustituye a lo ya recibido.
    """
    try:
        eventos = servicio.explicar_en_flujo(db, recomendacion_id, nueva_sesion)
    except servicio.NoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA) from exc
    return StreamingResponse(
        eventos,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{recomendacion_id}/valoracion", status_code=status.HTTP_204_NO_CONTENT)
def valorar_recomendacion(recomendacion_id: int, valoracion: ValoracionIn, db: DB):
    try:
        servicio.valorar(db, recomendacion_id, valoracion)
    except servicio.NoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA) from exc
