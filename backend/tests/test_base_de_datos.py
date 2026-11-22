"""Tests del modelo de datos contra PostgreSQL real (docs/BASE_DE_DATOS.md)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.jobs.daily import limpiar
from app.models import (
    EstadoRevision,
    FamiliaModelo,
    Importacion,
    Modelo,
    MotivoRevision,
    Oferta,
    OrigenClic,
    ProductoFeed,
    RecClick,
    RevisionPendiente,
    Sku,
    Tienda,
    VocabMap,
)
from app.services.tienda import registrar_salida


@pytest.fixture
def catalogo(db):
    """Una pala con un SKU y una tienda."""
    familia = FamiliaModelo(marca="Bullpadel", nombre="Vertex")
    modelo = Modelo(familia=familia, anio=2025, atributos={"forma": "diamante"})
    sku = Sku(modelo=modelo, ean="8435000000001")
    tienda = Tienda(nombre="Tienda A", dominios=["tienda-a.example"])
    db.add_all([familia, modelo, sku, tienda])
    db.flush()
    return sku, tienda


def importar(db, tienda, *datos, fecha=None):
    imp = Importacion(tienda_id=tienda.id, productos_recibidos=len(datos))
    if fecha:
        imp.fecha = fecha
    db.add(imp)
    db.flush()
    productos = [ProductoFeed(importacion_id=imp.id, datos=d) for d in datos]
    db.add_all(productos)
    db.flush()
    return imp, productos


def test_esquemas_y_tablas(db):
    insp = inspect(db.connection())
    assert {"importacion", "producto_feed", "revision_pendiente"} <= set(
        insp.get_table_names(schema="staging")
    )
    assert "vocab_map" in insp.get_table_names(schema="public")
    # staging no debe aparecer en public
    assert "importacion" not in insp.get_table_names(schema="public")


def test_borrar_importacion_borra_productos_y_revisiones(db, catalogo):
    _, tienda = catalogo
    imp, (producto,) = importar(db, tienda, {"titulo": "Vertex 04"})
    db.add(RevisionPendiente(producto_feed_id=producto.id, motivo=MotivoRevision.PALA_NUEVA))
    db.flush()

    db.execute(text("DELETE FROM staging.importacion WHERE id = :id"), {"id": imp.id})

    assert db.scalar(select(ProductoFeed).where(ProductoFeed.id == producto.id)) is None
    assert db.scalar(select(RevisionPendiente)) is None


def test_borrar_sku_conserva_producto_sin_emparejar(db, catalogo):
    sku, tienda = catalogo
    _, (producto,) = importar(db, tienda, {"ean": sku.ean})
    producto.sku_id = sku.id
    db.flush()

    db.execute(text("DELETE FROM sku WHERE id = :id"), {"id": sku.id})
    db.expire_all()

    assert db.get(ProductoFeed, producto.id).sku_id is None


def test_estado_de_importacion_invalido(db, catalogo):
    _, tienda = catalogo
    db.add(Importacion(tienda_id=tienda.id, estado="terminada"))
    with pytest.raises(IntegrityError, match="ck_importacion_estado"):
        db.flush()


def test_vocab_map_una_traduccion_generica_por_valor(db, catalogo):
    _, tienda = catalogo
    db.add(VocabMap(campo="forma", valor_origen="round", valor="redonda"))
    db.add(VocabMap(campo="forma", valor_origen="round", valor="redonda", tienda_id=tienda.id))
    db.flush()  # una genérica y una específica de tienda: válido

    db.add(VocabMap(campo="forma", valor_origen="round", valor="lagrima"))
    with pytest.raises(IntegrityError, match="uq_vocab_map_campo_valor_tienda"):
        db.flush()  # segunda genérica: NULLS NOT DISTINCT la rechaza


def test_consulta_de_publicacion_del_documento(db, catalogo):
    """La consulta de docs/BASE_DE_DATOS.md publica y luego actualiza la oferta."""
    sku, tienda = catalogo
    publicar = text("""
        INSERT INTO public.oferta (sku_id, tienda_id, precio, disponible, url)
        SELECT pf.sku_id, i.tienda_id,
               replace(replace(pf.datos->>'precio', ' €', ''), ',', '.')::numeric,
               (pf.datos->>'stock')::int > 0,
               pf.datos->>'url'
        FROM staging.producto_feed pf
        JOIN staging.importacion i ON i.id = pf.importacion_id
        WHERE pf.importacion_id = :importacion AND pf.sku_id IS NOT NULL
        ON CONFLICT (sku_id, tienda_id)
        DO UPDATE SET precio = EXCLUDED.precio, disponible = EXCLUDED.disponible,
                      url = EXCLUDED.url
    """)

    for precio, stock in [("279,95 €", 3), ("259,00 €", 0)]:
        imp, (producto,) = importar(
            db, tienda, {"precio": precio, "stock": stock, "url": "https://tienda-a.example/v04"}
        )
        producto.sku_id = sku.id
        db.flush()
        db.execute(publicar, {"importacion": imp.id})

    ofertas = db.scalars(select(Oferta).where(Oferta.sku_id == sku.id)).all()
    db.refresh(ofertas[0])
    assert len(ofertas) == 1  # ON CONFLICT actualiza en lugar de duplicar
    assert ofertas[0].precio == Decimal("259.00")
    assert ofertas[0].disponible is False


def test_salida_a_tienda_desde_ficha_con_enlace_de_afiliado(db, catalogo):
    sku, tienda = catalogo
    tienda.plantilla_enlace = "https://red.example/c?id={id_afiliado}&sub={subid}&u={url}"
    tienda.id_afiliado = "padel42"
    oferta = Oferta(
        sku_id=sku.id,
        tienda_id=tienda.id,
        precio=Decimal("279.95"),
        url="https://tienda-a.example/v04?c=1",
    )
    db.add(oferta)
    db.flush()

    url = registrar_salida(db, oferta.id, OrigenClic.FICHA)

    clic = db.scalar(select(RecClick).where(RecClick.oferta_id == oferta.id))
    assert clic.origen == "ficha" and clic.recomendacion_id is None
    assert url == (
        f"https://red.example/c?id=padel42&sub={clic.id}"
        "&u=https%3A%2F%2Ftienda-a.example%2Fv04%3Fc%3D1"
    )


def test_limpieza_conserva_importaciones_con_revision_pendiente(db, catalogo):
    _, tienda = catalogo
    ahora = datetime.now(UTC)
    antigua = ahora - timedelta(days=31)
    vieja_limpia, _ = importar(db, tienda, {"a": 1}, fecha=antigua)
    vieja_revisando, (producto,) = importar(db, tienda, {"b": 2}, fecha=antigua)
    reciente, _ = importar(db, tienda, {"c": 3})
    db.add(RevisionPendiente(producto_feed_id=producto.id, motivo=MotivoRevision.PRECIO_ANOMALO))
    db.flush()

    borrados = limpiar(db, ahora)

    ids = set(db.scalars(select(Importacion.id)))
    assert vieja_limpia.id not in ids
    assert {vieja_revisando.id, reciente.id} <= ids
    assert borrados["importaciones antiguas"] >= 1

    # Resuelta la revisión, la siguiente limpieza ya la borra.
    db.execute(
        text("UPDATE staging.revision_pendiente SET estado = :e"), {"e": EstadoRevision.APROBADO}
    )
    limpiar(db, ahora)
    assert vieja_revisando.id not in set(db.scalars(select(Importacion.id)))
