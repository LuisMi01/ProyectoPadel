"""FuenteFeed por HTTP: descarga el feed de una tienda (CSV o JSON, también comprimido con gzip)
y traduce cada fila a nuestros campos con el mapeo `tienda.feed_campos`.

Sirve para los feeds de las redes de afiliación (Awin, CJ...) y para los que dan las tiendas
directamente: cambia solo el mapeo de columnas.
"""

import csv
import gzip
import io
import json
from collections.abc import Iterable
from typing import Any

import httpx

from app.domain import normalizacion
from app.domain.modelos import ProductoFeed


def _filas(contenido: bytes, formato: str) -> list[dict[str, Any]]:
    if contenido[:2] == b"\x1f\x8b":
        contenido = gzip.decompress(contenido)
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")

    if formato == "json":
        datos = json.loads(texto)
        if isinstance(datos, dict):  # {"products": [...]} o similar
            datos = next((v for v in datos.values() if isinstance(v, list)), [])
        return [fila for fila in datos if isinstance(fila, dict)]

    muestra = texto[:5000]
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;|\t")
    except csv.Error:
        dialecto = csv.excel
    return list(csv.DictReader(io.StringIO(texto), dialect=dialecto))


def leer_feed(contenido: bytes, formato: str, campos: dict[str, str]) -> list[ProductoFeed]:
    """Filas del feed como ProductoFeed. Se descartan las que no traen referencia ni título."""
    productos: list[ProductoFeed] = []
    for fila in _filas(contenido, formato):

        def valor(campo: str, fila: dict[str, Any] = fila) -> Any:
            columna = campos.get(campo)
            dato = fila.get(columna) if columna else None
            return dato.strip() if isinstance(dato, str) else dato

        referencia, titulo = valor("referencia"), valor("titulo")
        if not referencia or not titulo:
            continue
        productos.append(
            ProductoFeed(
                referencia=str(referencia),
                titulo=str(titulo),
                precio=normalizacion.precio(valor("precio")),
                url=str(valor("url")) if valor("url") else None,
                disponible=normalizacion.disponible(valor("disponible")),
                ean=normalizacion.ean(valor("ean")),
                marca=str(valor("marca")) if valor("marca") else None,
                datos=dict(fila),
            )
        )
    return productos


class FuenteFeedHTTP:
    def __init__(self, url: str, formato: str, campos: dict[str, str]) -> None:
        self.url = url
        self.formato = formato
        self.campos = campos

    def productos(self) -> Iterable[ProductoFeed]:
        respuesta = httpx.get(self.url, timeout=120.0, follow_redirects=True)
        respuesta.raise_for_status()
        return leer_feed(respuesta.content, self.formato, self.campos)
