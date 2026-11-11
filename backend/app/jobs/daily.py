"""Tareas diarias: feeds de precios y ofertas, métricas y limpieza."""

import logging
from datetime import UTC, datetime

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models import Sesion, TokenAcceso

log = logging.getLogger(__name__)


def backup_db() -> None:
    log.info("pendiente: copia de seguridad de PostgreSQL")


def import_feed() -> None:
    log.info("pendiente: importar feeds de tiendas (ofertas + precio_historico)")


def extract_specs() -> None:
    log.info("pendiente: extraer especificaciones a modelo.atributos")


def pregenerate_explanations() -> None:
    log.info("pendiente: pregenerar explicaciones con IA")


def import_commissions() -> None:
    log.info("pendiente: importar comisiones de las redes de afiliación")


def aggregate_metrics() -> None:
    log.info("pendiente: agregar métricas (impresiones, clics, comisiones)")


def cleanup() -> None:
    """Borra sesiones y enlaces de acceso caducados."""
    ahora = datetime.now(UTC)
    with SessionLocal() as db:
        sesiones = db.execute(delete(Sesion).where(Sesion.expira < ahora)).rowcount
        tokens = db.execute(delete(TokenAcceso).where(TokenAcceso.expira < ahora)).rowcount
        db.commit()
    log.info("cleanup: %s sesiones y %s tokens caducados borrados", sesiones, tokens)
