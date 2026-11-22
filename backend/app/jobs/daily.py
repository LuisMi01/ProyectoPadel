"""Tareas diarias: feeds de precios y ofertas, métricas y limpieza."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    EstadoRevision,
    Importacion,
    ProductoFeed,
    RevisionPendiente,
    Sesion,
    TokenAcceso,
)

log = logging.getLogger(__name__)


def backup_db() -> None:
    log.info("pendiente: copia de seguridad de PostgreSQL")


def import_feed() -> None:
    # Pasos previstos (docs/BASE_DE_DATOS.md, "Cómo se normalizan los atributos"):
    # registrar importación -> guardar en bruto en staging -> comprobar tamaño ->
    # emparejar con SKU -> unificar valores (vocab_map) -> publicar oferta y
    # precio_historico -> cerrar.
    log.info("pendiente: importar feeds de tiendas (staging -> public)")


def extract_specs() -> None:
    log.info("pendiente: extraer especificaciones a modelo.atributos")


def pregenerate_explanations() -> None:
    log.info("pendiente: pregenerar explicaciones con IA")


def import_commissions() -> None:
    log.info("pendiente: importar comisiones de las redes de afiliación")


def aggregate_metrics() -> None:
    log.info("pendiente: agregar métricas (impresiones, clics, comisiones)")


DIAS_DATOS_EN_BRUTO = 30


def cleanup() -> None:
    """Borra sesiones y enlaces caducados y los catálogos en bruto de más de 30 días."""
    with SessionLocal() as db:
        borrados = limpiar(db, datetime.now(UTC))
        db.commit()
    log.info("cleanup: %s", ", ".join(f"{n} {que}" for que, n in borrados.items()))


def limpiar(db: Session, ahora: datetime) -> dict[str, int]:
    """Hace la limpieza sin confirmar la transacción (para poder probarla)."""
    sesiones = db.execute(delete(Sesion).where(Sesion.expira < ahora)).rowcount
    tokens = db.execute(delete(TokenAcceso).where(TokenAcceso.expira < ahora)).rowcount

    # Una importación antigua se conserva mientras tenga productos por revisar: si no,
    # la revisión desaparecería antes de que alguien la mire. El borrado arrastra sus
    # producto_feed y revision_pendiente (ON DELETE CASCADE).
    con_revision_abierta = (
        select(ProductoFeed.id)
        .join(RevisionPendiente)
        .where(
            ProductoFeed.importacion_id == Importacion.id,
            RevisionPendiente.estado == EstadoRevision.PENDIENTE,
        )
        .exists()
    )
    importaciones = db.execute(
        delete(Importacion).where(
            Importacion.fecha < ahora - timedelta(days=DIAS_DATOS_EN_BRUTO),
            ~con_revision_abierta,
        )
    ).rowcount
    return {
        "sesiones caducadas": sesiones,
        "tokens caducados": tokens,
        "importaciones antiguas": importaciones,
    }
