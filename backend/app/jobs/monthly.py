"""Tareas mensuales (día 1)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models import Evento

# Propuesta pendiente de revisión legal (ver la arquitectura).
MESES_EVENTOS = 13


def data_retention() -> dict[str, Any]:
    """Aplica los plazos de conservación. Hoy, los eventos de uso; las cuentas, con los usuarios."""
    limite = datetime.now(UTC) - timedelta(days=MESES_EVENTOS * 30)
    with SessionLocal() as db:
        eventos = db.execute(delete(Evento).where(Evento.fecha < limite)).rowcount
        db.commit()
    return {"eventos_borrados": eventos}
