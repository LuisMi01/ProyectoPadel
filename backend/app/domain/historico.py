"""Histórico del precio más bajo entre tiendas, en el formato de la ficha del frontend."""

from collections.abc import Iterable
from datetime import datetime


def serie_minimos(
    cambios: Iterable[tuple[datetime, int, float]],
    ahora: datetime,
    dias: int = 90,
) -> list[dict[str, float | int]]:
    """Precio mínimo entre ofertas en los últimos `dias`, como escalones {hace, precio}.

    `cambios` son (fecha, oferta_id, precio) de precio_historico. Devuelve los puntos del más
    antiguo al más reciente: el primero con `hace = dias` y sin repetir precios seguidos. Si hay
    varios cambios el mismo día, vale el último. Lista vacía si no hay ningún precio.
    """
    vigentes: dict[int, float] = {}
    por_dia: dict[int, float] = {}  # hace -> mínimo al final de ese día

    for fecha, oferta_id, precio in sorted(cambios, key=lambda c: c[0]):
        vigentes[oferta_id] = precio
        hace = min(dias, max(0, (ahora - fecha).days))
        por_dia[hace] = min(vigentes.values())

    serie: list[dict[str, float | int]] = []
    for hace in sorted(por_dia, reverse=True):
        if not serie or serie[-1]["precio"] != por_dia[hace]:
            serie.append({"hace": hace, "precio": por_dia[hace]})
    if serie:
        serie[0]["hace"] = dias
    return serie
