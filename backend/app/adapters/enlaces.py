"""ComprobadorEnlaces por HTTP: pregunta a la tienda si la página del producto sigue existiendo."""

import httpx

# Algunas tiendas no aceptan HEAD: entonces se repite con GET (sin descargar la página).
_SIN_HEAD = {403, 405, 501}


class ComprobadorEnlacesHTTP:
    def __init__(self, espera: float = 15.0) -> None:
        self._cliente = httpx.Client(
            follow_redirects=True,
            timeout=espera,
            headers={"User-Agent": "palaideal-check-links/1.0"},
        )

    def codigo(self, url: str) -> int | None:
        try:
            respuesta = self._cliente.head(url)
            if respuesta.status_code in _SIN_HEAD:
                with self._cliente.stream("GET", url) as completa:
                    return completa.status_code
            return respuesta.status_code
        except httpx.HTTPError:
            return None

    def cerrar(self) -> None:
        self._cliente.close()
