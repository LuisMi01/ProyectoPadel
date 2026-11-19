"""Analítica propia, métricas diarias y registro de las tareas programadas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Evento(Base):
    """Evento de uso (POST /eventos). Nunca datos de salud ni texto libre."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(50), index=True)
    datos: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class MetricaDiaria(Base):
    """Resumen diario (jobs.daily.aggregate_metrics): embudo, clics y comisiones."""

    __tablename__ = "metrica_diaria"
    __table_args__ = (UniqueConstraint("fecha", "metrica", "dimension"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date]
    metrica: Mapped[str] = mapped_column(String(50))
    # Desglose opcional (tienda, posición...). Vacío = total del día.
    dimension: Mapped[str] = mapped_column(String(100), default="", server_default="")
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 4))


class JobRun(Base):
    """Cada ejecución de una tarea programada. UNIQUE(tarea, periodo) evita repetirla."""

    __tablename__ = "job_run"
    __table_args__ = (UniqueConstraint("tarea", "periodo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tarea: Mapped[str] = mapped_column(String(50))
    periodo: Mapped[str] = mapped_column(String(20))
    inicio: Mapped[datetime] = mapped_column(server_default=func.now())
    fin: Mapped[datetime | None]
    estado: Mapped[str] = mapped_column(String(20), default="en_curso")
    resumen: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
