from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.deps import DB
from app.services import tienda as servicio

router = APIRouter(prefix="/tienda", tags=["Tienda"])


@router.get("/{oferta_id}")
def ir_a_la_tienda(oferta_id: int, db: DB, rec: int | None = None, pos: int | None = None):
    url = servicio.registrar_salida(db, oferta_id, rec, pos)
    if url is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Oferta no encontrada")
    return RedirectResponse(url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
