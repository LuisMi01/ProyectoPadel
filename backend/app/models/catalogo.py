"""Catálogo: familias, modelos, SKUs, tiendas, ofertas e histórico de precios."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FamiliaModelo(Base):
    __tablename__ = "familia_modelo"

    id: Mapped[int] = mapped_column(primary_key=True)
    marca: Mapped[str] = mapped_column(String(100), index=True)
    nombre: Mapped[str] = mapped_column(String(200))

    modelos: Mapped[list["Modelo"]] = relationship(back_populates="familia")


class Modelo(Base):
    __tablename__ = "modelo"

    id: Mapped[int] = mapped_column(primary_key=True)
    familia_id: Mapped[int] = mapped_column(ForeignKey("familia_modelo.id"), index=True)
    # Nombre comercial y slug de la URL de la ficha (/palas/<slug>/).
    nombre: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True)
    anio: Mapped[int | None]
    # Ficha normalizada con los campos del catálogo del frontend (forma, balance, peso, dureza,
    # nucleo, caras, gama, nivel, control, tolerancia, potencia, junior, textos...).
    atributos: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # activo | revision (pala nueva pendiente de aprobar) | retirado
    estado: Mapped[str] = mapped_column(String(30), default="activo")

    familia: Mapped[FamiliaModelo] = relationship(back_populates="modelos")
    skus: Mapped[list["Sku"]] = relationship(back_populates="modelo")


class Sku(Base):
    __tablename__ = "sku"

    id: Mapped[int] = mapped_column(primary_key=True)
    modelo_id: Mapped[int] = mapped_column(ForeignKey("modelo.id"), index=True)
    ean: Mapped[str | None] = mapped_column(String(20), unique=True)
    variante: Mapped[str | None] = mapped_column(String(100))

    modelo: Mapped[Modelo] = relationship(back_populates="skus")
    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="sku")


class Tienda(Base):
    __tablename__ = "tienda"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    red_afiliacion: Mapped[str | None] = mapped_column(String(100))
    comision: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    dominios: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Enlace de afiliado. La plantilla usa {url} (producto, codificada), {id_afiliado} y {subid}:
    #   https://www.awin1.com/cread.php?awinmid=123&awinaffid={id_afiliado}&clickref={subid}&ued={url}
    # Sin plantilla, se enlaza directamente a la URL del producto.
    plantilla_enlace: Mapped[str | None] = mapped_column(String(2048))
    id_afiliado: Mapped[str | None] = mapped_column(String(100))

    # Feed de productos (jobs.daily.import_feed). `feed_campos` dice qué columna del feed es cada
    # dato nuestro: {"referencia": "aw_product_id", "titulo": "product_name", "precio":
    # "search_price", "url": "merchant_deep_link", "ean": "ean", "marca": "brand_name",
    # "categoria": "merchant_category", "disponible": "in_stock"}. La categoría sirve para no
    # mandar a revisión lo que no es una pala.
    feed_url: Mapped[str | None] = mapped_column(String(2048))
    feed_formato: Mapped[str | None] = mapped_column(String(10))  # csv | json
    feed_campos: Mapped[dict[str, str]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="tienda")


class Oferta(Base):
    __tablename__ = "oferta"
    __table_args__ = (
        UniqueConstraint("sku_id", "tienda_id"),
        # Referencia del producto en el feed de la tienda: así se reconoce en cada importación.
        UniqueConstraint("tienda_id", "referencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("sku.id"), index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"), index=True)
    referencia: Mapped[str | None] = mapped_column(String(200))
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # stock | ultimas | agotada (los mismos valores que muestra el frontend)
    disponibilidad: Mapped[str] = mapped_column(String(20), default="stock", server_default="stock")
    url: Mapped[str] = mapped_column(String(2048))
    # Semanas seguidas en que la página del producto no existe (jobs.weekly.check_links). Con 2 la
    # oferta deja de mostrarse; vuelve a 0 en cuanto la página responde.
    enlace_fallos: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    sku: Mapped[Sku] = relationship(back_populates="ofertas")
    tienda: Mapped[Tienda] = relationship(back_populates="ofertas")
    historico: Mapped[list["PrecioHistorico"]] = relationship(back_populates="oferta")


class PrecioHistorico(Base):
    __tablename__ = "precio_historico"

    id: Mapped[int] = mapped_column(primary_key=True)
    oferta_id: Mapped[int] = mapped_column(ForeignKey("oferta.id"), index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())

    oferta: Mapped[Oferta] = relationship(back_populates="historico")


class VocabMap(Base):
    """Traduce los términos de cada tienda a valores comunes ("Equilibrado" -> balance medio).

    Sin tienda, la traducción vale para todas.
    """

    __tablename__ = "vocab_map"
    __table_args__ = (
        UniqueConstraint(
            "tienda_id", "campo", "valor_original", postgresql_nulls_not_distinct=True
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int | None] = mapped_column(ForeignKey("tienda.id", ondelete="CASCADE"))
    campo: Mapped[str] = mapped_column(String(50))
    valor_original: Mapped[str] = mapped_column(String(200))
    valor_normalizado: Mapped[str] = mapped_column(String(200))
