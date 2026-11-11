import logging

from fastapi import APIRouter, status

from app.schemas import EventoIn

router = APIRouter(prefix="/eventos", tags=["Analítica"])
log = logging.getLogger(__name__)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def registrar_evento(evento: EventoIn) -> None:
    # TODO: persistir eventos (tabla o servicio de analítica pendiente de decidir).
    log.info("evento %s %s", evento.tipo, evento.datos)
