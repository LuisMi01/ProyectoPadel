"""Catálogo: familias, modelos, SKUs, tiendas, ofertas e histórico de precios."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, func
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
    anio: Mapped[int | None]
    atributos: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
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

    ofertas: Mapped[list["Oferta"]] = relationship(back_populates="tienda")


class Oferta(Base):
    __tablename__ = "oferta"
    __table_args__ = (UniqueConstraint("sku_id", "tienda_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey("sku.id"), index=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"), index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    disponible: Mapped[bool] = mapped_column(default=True)
    url: Mapped[str] = mapped_column(String(2048))

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
