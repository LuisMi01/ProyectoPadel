"""Perfil, palas guardadas, alertas de precio e historial del usuario."""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import AlertaPrecio, PalaGuardada, Recomendacion, Usuario


def borrar_cuenta(db: Session, usuario: Usuario) -> None:
    # Sesiones, palas y alertas caen por ON DELETE CASCADE; las recomendaciones
    # se conservan anónimas (ON DELETE SET NULL) para las métricas.
    db.delete(usuario)
    db.commit()


def listar_palas(db: Session, usuario: Usuario) -> Sequence[PalaGuardada]:
    return db.scalars(
        select(PalaGuardada)
        .where(PalaGuardada.usuario_id == usuario.id)
        .order_by(PalaGuardada.fecha.desc())
    ).all()


def guardar_pala(db: Session, usuario: Usuario, modelo_id: int) -> PalaGuardada:
    pala = db.get(PalaGuardada, (usuario.id, modelo_id))
    if pala is None:
        pala = PalaGuardada(usuario_id=usuario.id, modelo_id=modelo_id)
        db.add(pala)
        db.commit()
        db.refresh(pala)
    return pala


def quitar_pala(db: Session, usuario: Usuario, modelo_id: int) -> None:
    db.execute(
        delete(PalaGuardada).where(
            PalaGuardada.usuario_id == usuario.id, PalaGuardada.modelo_id == modelo_id
        )
    )
    db.commit()


def listar_alertas(db: Session, usuario: Usuario) -> Sequence[AlertaPrecio]:
    return db.scalars(select(AlertaPrecio).where(AlertaPrecio.usuario_id == usuario.id)).all()


def crear_alerta(
    db: Session, usuario: Usuario, modelo_id: int, precio_objetivo: Decimal
) -> AlertaPrecio:
    alerta = AlertaPrecio(
        usuario_id=usuario.id, modelo_id=modelo_id, precio_objetivo=precio_objetivo
    )
    db.add(alerta)
    db.commit()
    db.refresh(alerta)
    return alerta


def eliminar_alerta(db: Session, usuario: Usuario, alerta_id: int) -> None:
    db.execute(
        delete(AlertaPrecio).where(
            AlertaPrecio.id == alerta_id, AlertaPrecio.usuario_id == usuario.id
        )
    )
    db.commit()


def historial(db: Session, usuario: Usuario) -> Sequence[Recomendacion]:
    return db.scalars(
        select(Recomendacion)
        .where(Recomendacion.usuario_id == usuario.id)
        .order_by(Recomendacion.fecha.desc())
    ).all()
