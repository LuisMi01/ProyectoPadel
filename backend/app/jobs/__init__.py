"""Tareas programadas (crons de Railway).

Uso:  python -m app.jobs daily|weekly|monthly [--solo NOMBRE]
"""

import logging
from collections.abc import Callable

from app.jobs import daily, monthly, weekly

Tarea = Callable[[], None]

GRUPOS: dict[str, list[Tarea]] = {
    "daily": [
        daily.backup_db,
        daily.import_feed,
        daily.extract_specs,
        daily.pregenerate_explanations,
        daily.import_commissions,
        daily.aggregate_metrics,
        daily.cleanup,
    ],
    "weekly": [weekly.check_links, weekly.evaluate_recommender, weekly.weekly_digest],
    "monthly": [monthly.data_retention, monthly.train_ranker],
}

log = logging.getLogger("app.jobs")


def ejecutar(grupo: str, solo: str | None = None) -> int:
    """Ejecuta las tareas del grupo en orden. Devuelve el número de tareas fallidas."""
    fallos = 0
    for tarea in GRUPOS[grupo]:
        if solo and tarea.__name__ != solo:
            continue
        log.info("▶ %s.%s", grupo, tarea.__name__)
        try:
            tarea()
        except Exception:  # una tarea rota no debe impedir las siguientes
            fallos += 1
            log.exception("✗ %s.%s", grupo, tarea.__name__)
    return fallos
