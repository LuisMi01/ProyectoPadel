"""RepositorioCatalogo sobre PostgreSQL: modelos activos con su ficha y sus ofertas."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.catalogo_json import pala_desde_frontend
from app.domain.enlaces import visible
from app.domain.modelos import Pala
from app.models import Modelo, Sku

log = logging.getLogger(__name__)


def modelo_a_frontend(modelo: Modelo) -> dict[str, Any]:
    """Modelo de la BD en el formato del catálogo del frontend (sin histórico)."""
    ofertas = [
        {
            "id": oferta.id,
            "tienda": str(oferta.tienda_id),
            "precio": float(oferta.precio),
            "disponibilidad": oferta.disponibilidad,
            "url": oferta.url,
        }
        for sku in modelo.skus
        for oferta in sku.ofertas
        if visible(oferta.enlace_fallos)  # sin página en la tienda: no se enseña
    ]
    return {
        **modelo.atributos,
        "id": modelo.id,
        "slug": modelo.slug,
        "marca": modelo.familia.marca,
        "nombre": modelo.nombre,
        "temporada": modelo.anio,
        "ofertas": ofertas,
    }


def modelos_activos(db: Session) -> list[Modelo]:
    consulta = (
        select(Modelo)
        .where(Modelo.estado == "activo")
        .options(
            selectinload(Modelo.familia),
            selectinload(Modelo.skus).selectinload(Sku.ofertas),
        )
        .order_by(Modelo.id)
    )
    return list(db.scalars(consulta))


class RepositorioCatalogoSQL:
    def __init__(self, db: Session) -> None:
        self._db = db

    def palas(self) -> list[Pala]:
        palas: list[Pala] = []
        for modelo in modelos_activos(self._db):
            datos = modelo_a_frontend(modelo)
            if not datos["ofertas"]:
                continue  # sin tienda que la venda no se puede recomendar
            try:
                palas.append(pala_desde_frontend(datos))
            except (KeyError, TypeError, IndexError):
                # Ficha incompleta (p. ej. pala nueva sin revisar): no entra en el motor.
                log.warning("modelo %s con ficha incompleta, se ignora", modelo.id)
        return palas
