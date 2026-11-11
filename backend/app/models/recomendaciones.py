"""Recomendaciones, impresiones, clics a tienda y comisiones."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recomendacion(Base):
    __tablename__ = "recomendacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 0..1: una recomendación puede ser anónima. Al borrar la cuenta se desvincula.
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), index=True
    )
    # Respuestas de la encuesta. Nunca se guardan datos de salud.
    perfil: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # Versiones del motor, ranker y catálogo, para poder reproducir el resultado.
    versiones: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())


class RecShown(Base):
    """Modelo mostrado en una recomendación y en qué posición."""

    __tablename__ = "rec_shown"

    recomendacion_id: Mapped[int] = mapped_column(
        ForeignKey("recomendacion.id", ondelete="CASCADE"), primary_key=True
    )
    modelo_id: Mapped[int] = mapped_column(ForeignKey("modelo.id"), primary_key=True)
    posicion: Mapped[int]


class RecClick(Base):
    """Clic en "ir a la tienda" desde una recomendación."""

    __tablename__ = "rec_click"

    id: Mapped[int] = mapped_column(primary_key=True)
    recomendacion_id: Mapped[int] = mapped_column(
        ForeignKey("recomendacion.id", ondelete="CASCADE"), index=True
    )
    oferta_id: Mapped[int] = mapped_column(ForeignKey("oferta.id"), index=True)
    posicion: Mapped[int]
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())


class Comision(Base):
    __tablename__ = "comision"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 0..1: hay comisiones importadas que no se pueden atribuir a un clic.
    rec_click_id: Mapped[int | None] = mapped_column(
        ForeignKey("rec_click.id", ondelete="SET NULL"), index=True
    )
    importe: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estado: Mapped[str] = mapped_column(String(30), default="pendiente")
