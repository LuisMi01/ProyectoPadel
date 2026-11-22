"""Exportación del catálogo para el build del frontend (GET /internas/catalogo)."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.catalogo_sql import modelo_a_frontend, modelos_activos
from app.domain.historico import serie_minimos
from app.models import PrecioHistorico, Tienda

DIAS_HISTORICO = 90


def exportar(db: Session) -> dict[str, Any]:
    """Tiendas y palas activas en el formato de frontend/src/data/catalogo.ts."""
    ahora = datetime.now(UTC)
    modelos = modelos_activos(db)
    palas = [modelo_a_frontend(m) for m in modelos]

    ofertas_de = {p["id"]: [o["id"] for o in p["ofertas"]] for p in palas}
    todas = [oferta_id for ids in ofertas_de.values() for oferta_id in ids]
    cambios: dict[int, list[tuple[datetime, int, float]]] = defaultdict(list)
    if todas:
        # Se lee algo más que la ventana para saber qué precio tenía cada oferta al empezarla.
        desde = ahora - timedelta(days=DIAS_HISTORICO * 4)
        filas = db.execute(
            select(PrecioHistorico.oferta_id, PrecioHistorico.fecha, PrecioHistorico.precio).where(
                PrecioHistorico.oferta_id.in_(todas), PrecioHistorico.fecha >= desde
            )
        )
        for oferta_id, fecha, precio in filas:
            cambios[oferta_id].append((fecha, oferta_id, float(precio)))

    for pala in palas:
        serie = serie_minimos(
            (c for oferta_id in ofertas_de[pala["id"]] for c in cambios[oferta_id]),
            ahora,
            DIAS_HISTORICO,
        )
        if not serie and pala["ofertas"]:
            precio = min(o["precio"] for o in pala["ofertas"])
            serie = [{"hace": DIAS_HISTORICO, "precio": precio}]
        pala["historico"] = serie

    tiendas = db.scalars(select(Tienda).order_by(Tienda.id))
    return {
        "tiendas": [{"id": str(t.id), "nombre": t.nombre} for t in tiendas],
        "palas": [p for p in palas if p["ofertas"]],
    }
