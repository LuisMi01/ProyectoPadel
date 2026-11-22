"""Esquema staging: catálogos de las tiendas tal como llegan, antes de normalizarlos.

La tarea diaria import_feed guarda aquí cada producto en bruto, lo empareja con un SKU y
publica el resultado en public.oferta. Los datos en bruto se borran a los 30 días
(jobs.daily.cleanup). Ver docs/BASE_DE_DATOS.md.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import ESQUEMA_STAGING, Base, en


class EstadoImportacion(StrEnum):
    EN_CURSO = "en_curso"
    CORRECTA = "correcta"
    FALLIDA = "fallida"
    # El catálogo trae muchos menos productos de lo normal: no se publica.
    DESCARTADA = "descartada"


class MotivoRevision(StrEnum):
    EMPAREJAMIENTO_DUDOSO = "emparejamiento_dudoso"
    PALA_NUEVA = "pala_nueva"
    PRECIO_ANOMALO = "precio_anomalo"


class EstadoRevision(StrEnum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class Importacion(Base):
    """Una fila por cada descarga del catálogo de una tienda."""

    __tablename__ = "importacion"
    __table_args__ = (
        CheckConstraint(en(EstadoImportacion, "estado"), name="estado"),
        Index("ix_importacion_tienda_fecha", "tienda_id", "fecha"),
        {"schema": ESQUEMA_STAGING},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id", ondelete="CASCADE"))
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())
    productos_recibidos: Mapped[int] = mapped_column(server_default="0")
    estado: Mapped[str] = mapped_column(String(20), server_default=EstadoImportacion.EN_CURSO)

    productos: Mapped[list["ProductoFeed"]] = relationship(
        back_populates="importacion", passive_deletes=True
    )


class ProductoFeed(Base):
    """Un producto recibido, sin normalizar. `datos` guarda el JSON tal como llega."""

    __tablename__ = "producto_feed"
    __table_args__ = {"schema": ESQUEMA_STAGING}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    importacion_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA_STAGING}.importacion.id", ondelete="CASCADE"), index=True
    )
    # 0..1: vacío mientras no se ha emparejado (o si se borra el SKU).
    sku_id: Mapped[int | None] = mapped_column(
        ForeignKey("sku.id", ondelete="SET NULL"), index=True
    )
    datos: Mapped[dict[str, Any]] = mapped_column(JSONB)

    importacion: Mapped[Importacion] = relationship(back_populates="productos")
    revisiones: Mapped[list["RevisionPendiente"]] = relationship(
        back_populates="producto_feed", passive_deletes=True
    )


class RevisionPendiente(Base):
    """Producto que el sistema no ha podido resolver solo y debe revisar una persona."""

    __tablename__ = "revision_pendiente"
    __table_args__ = (
        CheckConstraint(en(MotivoRevision, "motivo"), name="motivo"),
        CheckConstraint(en(EstadoRevision, "estado"), name="estado"),
        # La cola de trabajo: solo interesan las pendientes.
        Index(
            "ix_revision_pendiente_cola",
            "creado_en",
            postgresql_where=text("estado = 'pendiente'"),
        ),
        {"schema": ESQUEMA_STAGING},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    producto_feed_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA_STAGING}.producto_feed.id", ondelete="CASCADE"), index=True
    )
    motivo: Mapped[str] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(20), server_default=EstadoRevision.PENDIENTE)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    # Pala nueva: ficha que propone la IA (jobs.daily.extract_specs) para revisarla. Al aprobarla
    # se crea el modelo con estos datos.
    propuesta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    producto_feed: Mapped[ProductoFeed] = relationship(back_populates="revisiones")
