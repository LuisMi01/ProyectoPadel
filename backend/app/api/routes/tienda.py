from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import DB
from app.services import tienda as servicio

router = APIRouter(prefix="/tienda", tags=["Tienda"])

Origen = Literal["recomendacion", "ficha", "catalogo", "cuenta"]


@router.get("/{oferta_id}")
def ir_a_la_tienda(
    oferta_id: int,
    db: DB,
    rec: int | None = None,
    pos: int | None = Query(default=None, ge=1, le=50),
    origen: Origen | None = None,
):
    """Registra el clic y redirige a la tienda con el enlace de afiliado."""
    url = servicio.registrar_salida(
        db, oferta_id, rec, pos, origen or ("recomendacion" if rec else "ficha")
    )
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oferta no encontrada")
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
