"""Importación del feed de una tienda: staging -> emparejar -> normalizar -> publicar.

1. Se registra la importación y se guarda cada producto tal como llega (esquema staging).
2. Si el feed trae muchos menos productos que el anterior, se descarta: la web sigue con lo de ayer.
3. Cada producto se empareja con su SKU: por la referencia de la tienda (ofertas ya conocidas),
   por EAN o, si no, va a revisión manual (nombre parecido a una pala del catálogo: emparejamiento
   dudoso; si no se parece a ninguna: pala nueva). Lo que no es una pala (zapatillas, pelotas,
   paleteros) no va a revisión, y una pala nueva que ya espera revisión porque llegó por otra
   tienda tampoco: se revisa una sola vez.
4. Los emparejados actualizan su oferta y, si cambia el precio, el histórico. Un cambio de precio
   extremo no se publica: va a revisión.
5. Las ofertas de la tienda que ya no vienen en el feed pasan a agotadas.
"""

import logging
from dataclasses import asdict, dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.domain import normalizacion
from app.domain.modelos import ProductoFeed as Producto
from app.models import (
    Importacion,
    Modelo,
    Oferta,
    PrecioHistorico,
    ProductoFeed,
    RevisionPendiente,
    Sku,
    Tienda,
)

log = logging.getLogger(__name__)

PARECIDO_MINIMO = 0.82  # a partir de aquí, el nombre se considera un emparejamiento dudoso


@dataclass
class Resumen:
    tienda: str
    estado: str
    recibidos: int = 0
    actualizados: int = 0
    nuevos: int = 0
    a_revision: int = 0
    precio_anomalo: int = 0
    incompletos: int = 0
    agotados: int = 0
    no_pala: int = 0  # zapatillas, pelotas, paleteros…: no van a revisión
    ya_en_revision: int = 0  # pala nueva que ya espera revisión (llegó por otra tienda)

    def como_dict(self) -> dict[str, int | str]:
        return asdict(self)


def _datos(producto: Producto) -> dict[str, object]:
    return {
        "referencia": producto.referencia,
        "titulo": producto.titulo,
        "precio": str(producto.precio) if producto.precio is not None else None,
        "url": producto.url,
        "ean": producto.ean,
        "marca": producto.marca,
        "categoria": producto.categoria,
        "disponible": producto.disponible,
        "original": producto.datos,
    }


def _hay_revision_pendiente(db: Session, tienda_id: int, referencia: str, motivo: str) -> bool:
    consulta = (
        select(RevisionPendiente.id)
        .join(ProductoFeed, RevisionPendiente.producto_feed_id == ProductoFeed.id)
        .join(Importacion, ProductoFeed.importacion_id == Importacion.id)
        .where(
            Importacion.tienda_id == tienda_id,
            RevisionPendiente.estado == "pendiente",
            RevisionPendiente.motivo == motivo,
            ProductoFeed.datos["referencia"].astext == referencia,
        )
        .limit(1)
    )
    return db.scalar(consulta) is not None


def _a_revision(db: Session, tienda: Tienda, fila: ProductoFeed, motivo: str) -> None:
    referencia = str(fila.datos["referencia"])
    if not _hay_revision_pendiente(db, tienda.id, referencia, motivo):
        db.add(RevisionPendiente(producto_feed_id=fila.id, motivo=motivo))


def _nombre(marca: object, titulo: object) -> str:
    return normalizacion.texto_comparable(f"{marca or ''} {titulo or ''}")


def _palas_nuevas_en_revision(db: Session) -> tuple[set[str], set[str]]:
    """EAN y nombres de las palas nuevas que ya esperan revisión, de cualquier tienda."""
    eans: set[str] = set()
    nombres: set[str] = set()
    filas = db.scalars(
        select(ProductoFeed.datos)
        .join(RevisionPendiente, RevisionPendiente.producto_feed_id == ProductoFeed.id)
        .where(RevisionPendiente.motivo == "pala_nueva", RevisionPendiente.estado == "pendiente")
    )
    for datos in filas:
        if datos.get("ean"):
            eans.add(datos["ean"])
        nombres.add(_nombre(datos.get("marca"), datos.get("titulo")))
    return eans, nombres


def importar_tienda(db: Session, tienda: Tienda, productos: list[Producto]) -> Resumen:
    """Importa los productos de una tienda en una transacción. Devuelve el resumen."""
    ajustes = get_settings()
    resumen = Resumen(tienda=tienda.nombre, estado="en_curso", recibidos=len(productos))

    importacion = Importacion(tienda_id=tienda.id, productos_recibidos=len(productos))
    db.add(importacion)
    db.flush()

    anterior = db.scalar(
        select(Importacion.productos_recibidos)
        .where(
            Importacion.tienda_id == tienda.id,
            Importacion.estado == "correcta",
            Importacion.id != importacion.id,
        )
        .order_by(Importacion.fecha.desc())
        .limit(1)
    )
    if not productos or (
        anterior and len(productos) < anterior * ajustes.feed_minimo_respecto_anterior
    ):
        importacion.estado = resumen.estado = "descartada"
        db.commit()
        log.warning(
            "feed de %s descartado: %s productos (antes %s)",
            tienda.nombre,
            len(productos),
            anterior,
        )
        return resumen

    ofertas = {
        o.referencia: o
        for o in db.scalars(
            select(Oferta).where(Oferta.tienda_id == tienda.id).options(selectinload(Oferta.sku))
        )
        if o.referencia
    }
    eans = {p.ean for p in productos if p.ean}
    skus_por_ean = (
        {s.ean: s for s in db.scalars(select(Sku).where(Sku.ean.in_(eans)))} if eans else {}
    )
    # Se cargan solo si hace falta comparar nombres (hay algún producto sin emparejar).
    catalogo: list[tuple[str, Modelo]] | None = None
    en_revision: tuple[set[str], set[str]] = (set(), set())
    vistos: set[str] = set()

    for producto in productos:
        vistos.add(producto.referencia)
        fila = ProductoFeed(importacion_id=importacion.id, datos=_datos(producto))
        db.add(fila)
        db.flush()

        if producto.precio is None or not producto.url:
            resumen.incompletos += 1
            continue

        oferta = ofertas.get(producto.referencia)
        sku = oferta.sku if oferta else skus_por_ean.get(producto.ean or "")
        if sku is None:
            if not normalizacion.parece_pala(producto.titulo, producto.categoria):
                resumen.no_pala += 1
                continue
            if catalogo is None:
                modelos = db.scalars(select(Modelo).options(selectinload(Modelo.familia)))
                catalogo = [(f"{m.familia.marca} {m.nombre}", m) for m in modelos]
                en_revision = _palas_nuevas_en_revision(db)
            nombre = f"{producto.marca or ''} {producto.titulo}"
            parecido = max((normalizacion.parecido(nombre, n) for n, _ in catalogo), default=0.0)
            motivo = "emparejamiento_dudoso" if parecido >= PARECIDO_MINIMO else "pala_nueva"
            if motivo == "pala_nueva":
                # La misma pala desde otra tienda: una sola ficha. Cuando se apruebe, las demás
                # tiendas se emparejan solas por EAN (o van a revisión como emparejamiento dudoso).
                eans, nombres = en_revision
                clave = _nombre(producto.marca, producto.titulo)
                if (producto.ean and producto.ean in eans) or clave in nombres:
                    resumen.ya_en_revision += 1
                    continue
                if producto.ean:
                    eans.add(producto.ean)
                nombres.add(clave)
            _a_revision(db, tienda, fila, motivo)
            resumen.a_revision += 1
            continue

        fila.sku_id = sku.id
        if oferta is None:
            # Puede haber ya una oferta de esa pala en la tienda sin referencia (la semilla).
            oferta = db.scalar(
                select(Oferta).where(Oferta.sku_id == sku.id, Oferta.tienda_id == tienda.id)
            )
            if oferta is not None:
                oferta.referencia = producto.referencia
                ofertas[producto.referencia] = oferta

        precio: Decimal = producto.precio
        if oferta is not None and oferta.precio > 0:
            cambio = abs(precio - oferta.precio) / oferta.precio
            if cambio > Decimal(str(ajustes.precio_cambio_maximo)):
                _a_revision(db, tienda, fila, "precio_anomalo")
                resumen.precio_anomalo += 1
                continue

        disponibilidad = "stock" if producto.disponible else "agotada"
        if oferta is None:
            oferta = Oferta(
                sku_id=sku.id,
                tienda_id=tienda.id,
                referencia=producto.referencia,
                precio=precio,
                disponibilidad=disponibilidad,
                url=producto.url,
            )
            db.add(oferta)
            db.flush()
            ofertas[producto.referencia] = oferta
            db.add(PrecioHistorico(oferta_id=oferta.id, precio=precio))
            resumen.nuevos += 1
            continue

        if oferta.precio != precio:
            db.add(PrecioHistorico(oferta_id=oferta.id, precio=precio))
        oferta.precio = precio
        oferta.url = producto.url
        if not (disponibilidad == "stock" and oferta.disponibilidad == "ultimas"):
            oferta.disponibilidad = disponibilidad
        resumen.actualizados += 1

    for referencia, oferta in ofertas.items():
        if referencia not in vistos and oferta.disponibilidad != "agotada":
            oferta.disponibilidad = "agotada"
            resumen.agotados += 1

    importacion.estado = resumen.estado = "correcta"
    db.commit()
    return resumen
