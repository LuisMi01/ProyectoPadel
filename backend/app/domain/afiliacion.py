"""Enlace de afiliado de una oferta."""

from urllib.parse import quote


def enlace_afiliado(
    url_producto: str, plantilla: str | None, id_afiliado: str | None, subid: str
) -> str:
    """Rellena la plantilla de la tienda; sin plantilla, devuelve la URL del producto.

    Marcadores: {url} (URL del producto codificada), {id_afiliado} y {subid}, que identifica el
    clic para atribuir después la comisión. Se sustituyen uno a uno para que las llaves que pueda
    traer una URL no se interpreten como marcadores.
    """
    if not plantilla:
        return url_producto
    return (
        plantilla.replace("{url}", quote(url_producto, safe=""))
        .replace("{id_afiliado}", quote(id_afiliado or "", safe=""))
        .replace("{subid}", quote(subid, safe=""))
    )
