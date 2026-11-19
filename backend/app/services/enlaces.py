"""Comprobación semanal de las páginas de producto de las ofertas.

Se comprueba la URL del producto, nunca el enlace de afiliado: así no se cuentan clics falsos en
la red de afiliación. Una oferta cuya página no existe dos semanas seguidas deja de mostrarse
(domain.enlaces.FALLOS_PARA_OCULTAR); en cuanto vuelve a responder, reaparece.
"""

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enlaces import FALLOS_PARA_OCULTAR, estado_enlace
from app.domain.puertos import ComprobadorEnlaces
from app.models import Oferta

# Peticiones a la vez: pocas, para no cargar a las tiendas ni que nos bloqueen.
HILOS = 4


def comprobar_ofertas(db: Session, comprobador: ComprobadorEnlaces) -> dict[str, int]:
    ofertas = list(db.scalars(select(Oferta).where(Oferta.url != "").order_by(Oferta.id)))
    with ThreadPoolExecutor(max_workers=HILOS) as hilos:
        codigos = list(hilos.map(comprobador.codigo, (o.url for o in ofertas)))

    resumen = {"comprobadas": len(ofertas), "ok": 0, "rotas": 0, "dudosas": 0, "ocultadas": 0,
               "recuperadas": 0}  # fmt: skip
    for oferta, codigo in zip(ofertas, codigos, strict=True):
        estado = estado_enlace(codigo)
        if estado == "ok":
            resumen["ok"] += 1
            if oferta.enlace_fallos >= FALLOS_PARA_OCULTAR:
                resumen["recuperadas"] += 1
            oferta.enlace_fallos = 0
        elif estado == "rota":
            resumen["rotas"] += 1
            oferta.enlace_fallos += 1
            if oferta.enlace_fallos == FALLOS_PARA_OCULTAR:
                resumen["ocultadas"] += 1
        else:
            resumen["dudosas"] += 1
    db.commit()
    return resumen
