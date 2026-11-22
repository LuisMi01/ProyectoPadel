"""Enlace de afiliado de una oferta."""

from urllib.parse import quote


def enlace_afiliado(
    url_producto: str,
    plantilla: str | None,
    id_afiliado: str | None,
    subid: str,
    parametro_subid: str | None = None,
) -> str:
    """Rellena la plantilla de la tienda; sin plantilla, devuelve la URL del producto.

    Marcadores: {url} (URL del producto codificada), {id_afiliado} y {subid}, que identifica el
    clic para atribuir después la comisión. Se sustituyen uno a uno para que las llaves que pueda
    traer una URL no se interpreten como marcadores. Sin plantilla, si la tienda define
    `parametro_subid`, se añade a la URL del producto como ?<parametro_subid>=<subid>.
    """
    if not plantilla:
        if not parametro_subid:
            return url_producto
        separador = "&" if "?" in url_producto else "?"
        return f"{url_producto}{separador}{quote(parametro_subid)}={quote(subid, safe='')}"
    return (
        plantilla.replace("{url}", quote(url_producto, safe=""))
        .replace("{id_afiliado}", quote(id_afiliado or "", safe=""))
        .replace("{subid}", quote(subid, safe=""))
    )
