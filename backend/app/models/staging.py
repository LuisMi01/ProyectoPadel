"""Esquema `staging`: los feeds tal como llegan de las tiendas, antes de normalizarlos.

Una importación trae muchos productos; los dudosos acaban en la cola de revisión manual.
Los datos brutos se conservan unos 30 días (los borra jobs.daily.cleanup).
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ESQUEMA = "staging"


class Importacion(Base):
    __tablename__ = "importacion"
    __table_args__ = {"schema": ESQUEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    tienda_id: Mapped[int] = mapped_column(ForeignKey("tienda.id"), index=True)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())
    productos_recibidos: Mapped[int] = mapped_column(default=0)
    # en_curso | correcta | fallida | descartada (feed con tamaño anómalo)
    estado: Mapped[str] = mapped_column(String(20), default="en_curso")


class ProductoFeed(Base):
    __tablename__ = "producto_feed"
    __table_args__ = {"schema": ESQUEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    importacion_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA}.importacion.id", ondelete="CASCADE"), index=True
    )
    # SKU con el que se emparejó; vacío mientras no se empareja.
    sku_id: Mapped[int | None] = mapped_column(
        ForeignKey("sku.id", ondelete="SET NULL"), index=True
    )
    datos: Mapped[dict[str, Any]] = mapped_column(JSONB)


class RevisionPendiente(Base):
    __tablename__ = "revision_pendiente"
    __table_args__ = {"schema": ESQUEMA}

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_feed_id: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA}.producto_feed.id", ondelete="CASCADE"), index=True
    )
    # emparejamiento_dudoso | pala_nueva | precio_anomalo
    motivo: Mapped[str] = mapped_column(String(30))
    # pendiente | aprobado | rechazado
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    creada: Mapped[datetime] = mapped_column(server_default=func.now())
