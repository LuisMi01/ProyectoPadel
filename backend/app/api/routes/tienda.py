from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import DB
from app.models import OrigenClic
from app.services import tienda as servicio

router = APIRouter(prefix="/tienda", tags=["Tienda"])


@router.get("/{oferta_id}")
def ir_a_la_tienda(
    oferta_id: int,
    db: DB,
    origen: OrigenClic | None = None,
    rec: int | None = None,
    pos: int | None = Query(default=None, ge=1, le=50),
):
    """Registra el clic y redirige a la tienda con el enlace de afiliado.

    Sin `origen`: se toma recomendación si llega `rec` y ficha en caso contrario.
    """
    if origen is None:
        origen = OrigenClic.RECOMENDACION if rec is not None else OrigenClic.FICHA
    url = servicio.registrar_salida(db, oferta_id, origen, rec, pos)
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oferta no encontrada")
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
