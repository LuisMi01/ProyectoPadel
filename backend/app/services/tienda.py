"""Salida a tienda: registra el clic y redirige al enlace de afiliado."""

from urllib.parse import quote

from sqlalchemy.orm import Session

from app.models import Oferta, OrigenClic, RecClick, Tienda


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

    clic = RecClick(
        oferta_id=oferta.id,
        origen=origen,
        recomendacion_id=recomendacion_id,
        posicion=posicion,
    )
    db.add(clic)
    db.flush()  # necesitamos clic.id como subid del enlace
    url = enlace_afiliado(oferta.tienda, oferta.url, clic.id)
    db.commit()
    return url


def enlace_afiliado(tienda: Tienda, url: str, subid: int) -> str:
    """Construye el enlace de afiliado con la plantilla de la tienda.

    La plantilla admite {url} (URL del producto, codificada), {id_afiliado} y {subid}.
    Sin plantilla se usa la URL directa y, si la tienda define parametro_subid, se le añade.
    """
    if tienda.plantilla_enlace:
        return tienda.plantilla_enlace.format(
            url=quote(url, safe=""), id_afiliado=tienda.id_afiliado or "", subid=subid
        )
    if tienda.parametro_subid:
        separador = "&" if "?" in url else "?"
        return f"{url}{separador}{tienda.parametro_subid}={subid}"
    return url
