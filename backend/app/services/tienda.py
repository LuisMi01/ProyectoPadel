"""Salida a tienda: registra el clic y devuelve el enlace de afiliado con el clic como SubID."""

from sqlalchemy.orm import Session

from app.domain.afiliacion import enlace_afiliado
from app.models import Oferta, OrigenClic, RecClick, Recomendacion


def registrar_salida(
    db: Session,
    oferta_id: int,
    origen: OrigenClic,
    recomendacion_id: int | None = None,
    posicion: int | None = None,
) -> str | None:
    """Guarda el clic y devuelve la URL de destino, o None si la oferta no existe."""
    oferta = db.get(Oferta, oferta_id)
    if oferta is None:
        return None
    # Una recomendación que no existe no invalida la salida: se registra como clic suelto.
    if recomendacion_id is not None and db.get(Recomendacion, recomendacion_id) is None:
        recomendacion_id = None
    clic = RecClick(
        recomendacion_id=recomendacion_id,
        oferta_id=oferta.id,
        origen=origen,
        posicion=posicion,
    )
    db.add(clic)
    db.flush()  # necesitamos clic.id como subid del enlace
    tienda = oferta.tienda
    url = enlace_afiliado(
        oferta.url,
        tienda.plantilla_enlace,
        tienda.id_afiliado,
        str(clic.id),
        tienda.parametro_subid,
    )
    db.commit()
    return url
