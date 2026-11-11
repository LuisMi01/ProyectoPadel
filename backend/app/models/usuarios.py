"""Usuarios y acceso sin contraseña (enlace de acceso + sesión)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())


class Sesion(Base):
    __tablename__ = "sesion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira: Mapped[datetime]


class TokenAcceso(Base):
    """Enlace de acceso enviado por email; no depende de que el usuario exista aún."""

    __tablename__ = "token_acceso"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira: Mapped[datetime]


class PalaGuardada(Base):
    __tablename__ = "pala_guardada"

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    modelo_id: Mapped[int] = mapped_column(ForeignKey("modelo.id"), primary_key=True)
    fecha: Mapped[datetime] = mapped_column(server_default=func.now())


class AlertaPrecio(Base):
    __tablename__ = "alerta_precio"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    modelo_id: Mapped[int] = mapped_column(ForeignKey("modelo.id"), index=True)
    precio_objetivo: Mapped[Decimal] = mapped_column(Numeric(10, 2))
