"""Tareas mensuales."""

import logging

log = logging.getLogger(__name__)


def data_retention() -> None:
    log.info("pendiente: aplicar política de retención de datos")


def train_ranker() -> None:
    log.info("pendiente: reentrenar el ranker de recomendaciones")
