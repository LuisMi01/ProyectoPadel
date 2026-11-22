"""Fichas propuestas por la IA para las palas nuevas que llegan de los feeds.

Cada producto que import_feed no reconoce queda en staging.revision_pendiente (motivo
«pala_nueva»). Aquí la IA lee lo que publica la tienda y deja la ficha en `propuesta`; quien
revisa la cola la comprueba y, al aprobarla, se crea el modelo. Si la IA falla, la revisión sigue
sin propuesta y se reintenta al día siguiente.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.fichas import limpiar_ficha, texto_producto
from app.domain.puertos import ExtractorFichas
from app.models import ProductoFeed, RevisionPendiente


def proponer_fichas(db: Session, extractor: ExtractorFichas, maximo: int) -> dict[str, int]:
    pendientes = db.execute(
        select(RevisionPendiente, ProductoFeed.datos)
        .join(ProductoFeed, RevisionPendiente.producto_feed_id == ProductoFeed.id)
        .where(
            RevisionPendiente.motivo == "pala_nueva",
            RevisionPendiente.estado == "pendiente",
            RevisionPendiente.propuesta.is_(None),
        )
        .order_by(RevisionPendiente.id)
        .limit(maximo)
    ).all()

    propuestas = fallidas = 0
    for revision, datos in pendientes:
        ficha = extractor.extraer(texto_producto(datos))
        if ficha is None:
            fallidas += 1
            continue
        revision.propuesta = {
            "ficha": limpiar_ficha(ficha),
            "origen": "ia",
            "fecha": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        propuestas += 1
        db.commit()  # una a una: si la tarea se corta, no se pierde lo ya hecho
    return {"pendientes": len(pendientes), "propuestas": propuestas, "fallidas": fallidas}
