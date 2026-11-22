"""Carga el catálogo de ejemplo (app/semillas/catalogo_ejemplo.json) en la base de datos.

Uso:  python -m app.semillas

Es el mismo catálogo que usa la web mientras no hay tiendas conectadas, con los mismos ids de
pala y de oferta, para que frontend y API coincidan. Se puede ejecutar varias veces: actualiza lo
que ya existe. Solo para desarrollo y demostraciones: las tiendas y los precios son ficticios.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.adapters.catalogo_json import catalogo_ejemplo
from app.models import FamiliaModelo, Modelo, Oferta, PrecioHistorico, Sku, Tienda

# Campos de la ficha que van en modelo.atributos (el resto tiene columna propia).
FUERA_DE_ATRIBUTOS = {"id", "slug", "marca", "nombre", "temporada", "ofertas", "historico"}


def cargar(db: Session) -> dict[str, int]:
    datos = catalogo_ejemplo()
    ahora = datetime.now(UTC)

    tiendas: dict[str, Tienda] = {}
    for t in datos["tiendas"]:
        tienda = db.scalar(select(Tienda).where(Tienda.nombre == t["nombre"]))
        if tienda is None:
            tienda = Tienda(nombre=t["nombre"], dominios=[])
            db.add(tienda)
            db.flush()
        tiendas[t["id"]] = tienda

    for p in datos["palas"]:
        familia = db.scalar(
            select(FamiliaModelo).where(
                FamiliaModelo.marca == p["marca"], FamiliaModelo.nombre == p["nombre"]
            )
        )
        if familia is None:
            familia = FamiliaModelo(marca=p["marca"], nombre=p["nombre"])
            db.add(familia)
            db.flush()

        modelo = db.get(Modelo, p["id"]) or Modelo(id=p["id"])
        modelo.familia_id = familia.id
        modelo.nombre = p["nombre"]
        modelo.slug = p["slug"]
        modelo.anio = p["temporada"]
        modelo.estado = "activo"
        modelo.atributos = {k: v for k, v in p.items() if k not in FUERA_DE_ATRIBUTOS}
        db.add(modelo)
        db.flush()

        sku = db.scalar(select(Sku).where(Sku.modelo_id == modelo.id)) or Sku(modelo_id=modelo.id)
        db.add(sku)
        db.flush()

        mejor_id = min(
            (o for o in p["ofertas"] if o["disponibilidad"] != "agotada"),
            key=lambda o: o["precio"],
            default=p["ofertas"][0],
        )["id"]
        for o in p["ofertas"]:
            oferta = db.get(Oferta, o["id"]) or Oferta(id=o["id"])
            oferta.sku_id = sku.id
            oferta.tienda_id = tiendas[o["tienda"]].id
            oferta.precio = Decimal(str(o["precio"]))
            oferta.disponibilidad = o["disponibilidad"]
            # El catálogo de ejemplo no tiene URLs reales: se enlaza a la propia ficha.
            oferta.url = o["url"] or f"https://palaideal.example/palas/{p['slug']}/"
            db.add(oferta)
            db.flush()

            db.execute(delete(PrecioHistorico).where(PrecioHistorico.oferta_id == oferta.id))
            # El histórico del ejemplo es el mínimo entre tiendas: se asigna a la oferta más
            # barata de hoy; las demás solo tienen su precio actual.
            puntos = p["historico"] if oferta.id == mejor_id else []
            for punto in puntos:
                db.add(
                    PrecioHistorico(
                        oferta_id=oferta.id,
                        precio=Decimal(str(punto["precio"])),
                        fecha=ahora - timedelta(days=punto["hace"]),
                    )
                )
            if not puntos or puntos[-1]["precio"] != o["precio"]:
                db.add(PrecioHistorico(oferta_id=oferta.id, precio=oferta.precio, fecha=ahora))

    # Los ids se han puesto a mano: las secuencias tienen que seguir desde el mayor.
    for tabla in ("modelo", "oferta"):
        secuencia = f"pg_get_serial_sequence('{tabla}', 'id')"
        db.execute(text(f"SELECT setval({secuencia}, (SELECT max(id) FROM {tabla}))"))
    db.commit()
    return {"tiendas": len(tiendas), "palas": len(datos["palas"])}
