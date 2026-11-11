"""Tareas semanales."""

import logging

log = logging.getLogger(__name__)


def check_links() -> None:
    log.info("pendiente: comprobar que las URLs de oferta siguen vivas")


def evaluate_recommender() -> None:
    log.info("pendiente: evaluar el recomendador con los clics de la semana")


def weekly_digest() -> None:
    log.info("pendiente: resumen semanal (alertas de precio alcanzadas)")
