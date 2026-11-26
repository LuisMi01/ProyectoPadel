"""Catálogo en el formato del frontend (frontend/src/lib/catalogo.ts).

Es el formato de app/semillas/catalogo_ejemplo.json (las 15 palas de ejemplo de la web) y el que
devuelve GET /internas/catalogo, para que el build de Astro pueda usarlo sin traducir campos.
"""

import json
from functools import cache
from pathlib import Path
from typing import Any

from app.domain.modelos import OfertaPala, Pala
from app.domain.valoraciones import valoraciones

RUTA_EJEMPLO = Path(__file__).resolve().parents[1] / "semillas" / "catalogo_ejemplo.json"


def pala_desde_frontend(d: dict[str, Any]) -> Pala:
    # Las valoraciones no se leen de la ficha: se calculan, igual que en la web.
    v = valoraciones(d["forma"], d["balance"], d["dureza"], d["peso"], d["caras"])
    return Pala(
        id=d["id"],
        slug=d["slug"],
        marca=d["marca"],
        nombre=d["nombre"],
        temporada=d["temporada"],
        junior=d["junior"],
        forma=d["forma"],
        balance=d["balance"],
        peso=d["peso"],
        peso_min=d["pesoMin"],
        peso_max=d["pesoMax"],
        dureza=d["dureza"],
        nucleo=d["nucleo"],
        caras=d["caras"],
        caras_texto=d["carasTexto"],
        gama=d["gama"],
        nivel=(d["nivel"][0], d["nivel"][1]),
        manejabilidad=v.manejabilidad,
        precision=v.precision,
        tolerancia=v.tolerancia,
        potencia=v.potencia,
        amortiguacion=v.amortiguacion,
        control=v.control,
        resumen=d.get("resumen", ""),
        para_ti=tuple(d.get("paraTi", ())),
        mejor_otra=tuple(d.get("mejorOtra", ())),
        ofertas=tuple(
            OfertaPala(
                id=o["id"],
                tienda=o["tienda"],
                precio=float(o["precio"]),
                disponibilidad=o["disponibilidad"],
                url=o.get("url"),
            )
            for o in d["ofertas"]
        ),
    )


@cache
def catalogo_ejemplo() -> dict[str, Any]:
    """Tiendas y palas de ejemplo, tal como están en el JSON."""
    return json.loads(RUTA_EJEMPLO.read_text(encoding="utf-8"))


def palas_ejemplo() -> list[Pala]:
    return [pala_desde_frontend(d) for d in catalogo_ejemplo()["palas"]]
