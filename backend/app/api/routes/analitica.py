from fastapi import APIRouter, status

from app.api.deps import DB
from app.models import Evento
from app.schemas import EventoIn

router = APIRouter(prefix="/eventos", tags=["Analítica"])

# Claves que nunca se guardan aunque lleguen: son datos de salud.
CLAVES_DE_SALUD = {"mol", "molestias", "salud", "zona", "momento", "zona_molestia"}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def registrar_evento(evento: EventoIn, db: DB) -> None:
    datos = {k: v for k, v in evento.datos.items() if k.lower() not in CLAVES_DE_SALUD}
    db.add(Evento(tipo=evento.tipo, datos=datos))
    db.commit()
