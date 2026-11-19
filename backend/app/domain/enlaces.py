"""Estado de la página de producto de una oferta (jobs.weekly.check_links)."""

from typing import Literal

# Semanas seguidas sin página para dejar de mostrar la oferta. Con una sola podría ser un fallo
# pasajero de la tienda.
FALLOS_PARA_OCULTAR = 2

EstadoEnlace = Literal["ok", "rota", "dudosa"]


def estado_enlace(codigo: int | None) -> EstadoEnlace:
    """Traduce la respuesta HTTP (None si no la hubo) a qué hacer con la oferta.

    Solo 404 y 410 dicen que el producto ya no existe. Un error de red, un bloqueo (403, 429) o un
    fallo del servidor (5xx) no prueban nada: la oferta se queda como estaba.
    """
    if codigo is None:
        return "dudosa"
    if 200 <= codigo < 400:
        return "ok"
    if codigo in (404, 410):
        return "rota"
    return "dudosa"


def visible(enlace_fallos: int) -> bool:
    return enlace_fallos < FALLOS_PARA_OCULTAR
