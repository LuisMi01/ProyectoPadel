"""Salida a tienda: registra el clic (si viene de una recomendación) y redirige."""

from sqlalchemy.orm import Session

from app.models import Oferta, RecClick


def registrar_salida(
    db: Session, oferta_id: int, recomendacion_id: int | None, posicion: int | None
) -> str | None:
    """Devuelve la URL de la tienda o None si la oferta no existe."""
    oferta = db.get(Oferta, oferta_id)
    if oferta is None:
        return None
    if recomendacion_id is not None and posicion is not None:
        db.add(RecClick(recomendacion_id=recomendacion_id, oferta_id=oferta.id, posicion=posicion))
        db.commit()
    return oferta.url
