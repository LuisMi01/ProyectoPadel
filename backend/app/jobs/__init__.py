"""Tareas programadas (crons de Railway).

Uso:  python -m app.jobs daily|weekly|monthly [--solo NOMBRE]

Cada ejecución queda en la tabla job_run con su periodo (día, semana o mes). Una tarea que ya
terminó bien en su periodo no se repite: así el reintento de las 11:00 solo rehace lo que falló.
Un bloqueo de PostgreSQL impide que la misma tarea corra dos veces a la vez.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, text

from app.db.session import SessionLocal, engine
from app.jobs import daily, monthly, weekly
from app.models import JobRun

Tarea = Callable[[], dict[str, Any] | None]

GRUPOS: dict[str, list[Tarea]] = {
    "daily": [
        daily.backup_db,
        daily.import_feed,
        daily.extract_specs,
        daily.pregenerate_explanations,
        daily.aggregate_metrics,
        daily.cleanup,
    ],
    "weekly": [weekly.check_links, weekly.weekly_digest],
    "monthly": [monthly.data_retention],
}

log = logging.getLogger("app.jobs")


def periodo(grupo: str, ahora: datetime) -> str:
    """2026-11-18 (diaria), 2026-W47 (semanal) o 2026-11 (mensual)."""
    if grupo == "weekly":
        anio, semana, _ = ahora.isocalendar()
        return f"{anio}-W{semana:02d}"
    if grupo == "monthly":
        return ahora.strftime("%Y-%m")
    return ahora.strftime("%Y-%m-%d")


def _ejecutar_una(grupo: str, tarea: Tarea, clave_periodo: str) -> bool:
    """Ejecuta una tarea con registro y bloqueo. Devuelve False si ha fallado."""
    nombre = tarea.__name__
    with engine.connect() as cerrojo:
        if not cerrojo.scalar(text("SELECT pg_try_advisory_lock(hashtext(:t))"), {"t": nombre}):
            log.warning("↷ %s.%s ya se está ejecutando en otro proceso", grupo, nombre)
            return True
        try:
            with SessionLocal() as db:
                registro = db.scalar(
                    select(JobRun).where(JobRun.tarea == nombre, JobRun.periodo == clave_periodo)
                )
                if registro is not None and registro.estado == "correcta":
                    log.info("✓ %s.%s ya hecha en %s", grupo, nombre, clave_periodo)
                    return True
                if registro is None:
                    registro = JobRun(tarea=nombre, periodo=clave_periodo)
                    db.add(registro)
                registro.estado, registro.inicio, registro.fin = "en_curso", func.now(), None
                db.commit()

            log.info("▶ %s.%s", grupo, nombre)
            try:
                resumen = tarea()
                estado = "correcta"
            except Exception as exc:  # una tarea rota no debe impedir las siguientes
                log.exception("✗ %s.%s", grupo, nombre)
                resumen, estado = {"error": f"{type(exc).__name__}: {exc}"[:500]}, "fallida"

            with SessionLocal() as db:
                registro = db.scalar(
                    select(JobRun).where(JobRun.tarea == nombre, JobRun.periodo == clave_periodo)
                )
                registro.estado, registro.fin, registro.resumen = estado, func.now(), resumen
                db.commit()
            return estado == "correcta"
        finally:
            cerrojo.execute(text("SELECT pg_advisory_unlock(hashtext(:t))"), {"t": nombre})


def ejecutar(grupo: str, solo: str | None = None) -> int:
    """Ejecuta las tareas del grupo en orden. Devuelve el número de tareas fallidas."""
    clave_periodo = periodo(grupo, datetime.now(UTC))
    fallos = 0
    for tarea in GRUPOS[grupo]:
        if solo and tarea.__name__ != solo:
            continue
        if not _ejecutar_una(grupo, tarea, clave_periodo):
            fallos += 1
    return fallos
