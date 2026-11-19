"""Caso de uso de la recomendación: coordina el catálogo, el motor del dominio y el guardado."""

import hashlib
from collections import Counter
from dataclasses import fields
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.catalogo_sql import RepositorioCatalogoSQL
from app.domain.modelos import Pala, Respuestas, Resultado, Salud
from app.domain.motor import MOTOR_VERSION, recomendar
from app.models import Feedback, Recomendacion, RecShown, Usuario
from app.schemas import (
    AlternativaOut,
    MotivoOut,
    PalaOut,
    PerfilEncuesta,
    RecomendacionOut,
    ValoracionIn,
)
from app.services import explicaciones


class SinResultados(Exception):
    """Ninguna pala del catálogo cumple la talla y el tope de gasto."""


class NoEncontrada(Exception):
    """La recomendación pedida no existe."""


def version_catalogo(palas: list[Pala]) -> str:
    """Huella del catálogo usado (modelos y precios), para poder reproducir el resultado."""
    huella = "|".join(
        f"{p.id}:{min(o.precio for o in p.ofertas):.2f}" for p in sorted(palas, key=lambda p: p.id)
    )
    return hashlib.sha256(huella.encode()).hexdigest()[:12]


def _pala_out(pala: Pala) -> PalaOut:
    return PalaOut(modelo_id=pala.id, slug=pala.slug, nombre=pala.nombre)


def _salida(rec: Recomendacion, res: Resultado) -> RecomendacionOut:
    return RecomendacionOut(
        id=rec.id,
        fecha=rec.fecha,
        titular=res.titular,
        mejor=_pala_out(res.mejor),
        motivos=[MotivoOut(respuesta=m.respuesta, explicacion=m.explicacion) for m in res.motivos],
        alternativas=[
            AlternativaOut(
                **_pala_out(a.pala).model_dump(),
                etiqueta=a.etiqueta,
                ganas=a.ganas,
                pierdes=a.pierdes,
            )
            for a in res.alternativas
        ],
        nota=res.nota,
    )


def obtener(db: Session, perfil: PerfilEncuesta, usuario: Usuario | None) -> RecomendacionOut:
    """Calcula la recomendación, la guarda (sin datos de salud) y la devuelve."""
    palas = RepositorioCatalogoSQL(db).palas()
    respuestas = Respuestas(**perfil.model_dump(exclude={"salud"}))
    salud = Salud(perfil.salud.zona, perfil.salud.momento) if perfil.salud else None

    resultado = recomendar(respuestas, salud, palas)
    if resultado is None:
        raise SinResultados

    rec = Recomendacion(
        usuario_id=usuario.id if usuario else None,
        perfil=perfil.sin_salud(),
        versiones={"motor": MOTOR_VERSION, "catalogo": version_catalogo(palas)},
    )
    db.add(rec)
    db.flush()
    elegidas = [resultado.mejor, *(a.pala for a in resultado.alternativas)]
    db.add_all(
        RecShown(recomendacion_id=rec.id, modelo_id=pala.id, posicion=posicion)
        for posicion, pala in enumerate(elegidas, start=1)
    )
    db.commit()
    db.refresh(rec)
    return _salida(rec, resultado)


def explicar(db: Session, recomendacion_id: int) -> str:
    """Explicación de una recomendación guardada: con IA si se puede, si no con plantilla."""
    rec = db.get(Recomendacion, recomendacion_id)
    if rec is None:
        raise NoEncontrada
    ids = list(
        db.scalars(
            select(RecShown.modelo_id)
            .where(RecShown.recomendacion_id == rec.id)
            .order_by(RecShown.posicion)
        )
    )
    por_id = {p.id: p for p in RepositorioCatalogoSQL(db).palas()}
    palas = [por_id[i] for i in ids if i in por_id]
    if not palas:
        raise NoEncontrada  # las palas ya no están en el catálogo
    return explicaciones.obtener(db, rec.perfil, palas)


def pregenerar_explicaciones(db: Session, dias: int, maximo: int) -> dict[str, int | str]:
    """Deja en caché la explicación de los perfiles más repetidos de los últimos `dias` días.

    Se calcula con el catálogo y los precios de hoy, igual que al pedirla: quien haga hoy la
    encuesta con uno de esos perfiles (sin molestias) la recibe al momento y sin otra llamada a la
    IA. `maximo` deja sitio en el tope diario para las explicaciones que se piden en el momento.
    """
    desde = datetime.now(UTC) - timedelta(days=dias)
    perfiles = db.scalars(
        select(Recomendacion.perfil)
        .where(Recomendacion.fecha >= desde)
        .group_by(Recomendacion.perfil)
        .order_by(func.count().desc())
        .limit(maximo)
    ).all()
    palas = RepositorioCatalogoSQL(db).palas()
    campos = {f.name for f in fields(Respuestas)}

    cuenta = Counter[str]()
    for perfil in perfiles:
        resultado = recomendar(
            Respuestas(**{k: v for k, v in perfil.items() if k in campos}), None, palas
        )
        if resultado is None:
            continue
        elegidas = [resultado.mejor, *(a.pala for a in resultado.alternativas)]
        origen = explicaciones.generar(db, perfil, elegidas)[1]
        if origen == "sin_ia":
            return {"omitida": "sin clave de IA"}
        cuenta[origen] += 1
        if origen == "tope":
            break
    return {
        "perfiles": len(perfiles),
        "ya_en_cache": cuenta["cache"],
        "generadas": cuenta["ia"],
        "fallidas": cuenta["plantilla"],
        "tope_alcanzado": "si" if cuenta["tope"] else "no",
    }


def valorar(db: Session, recomendacion_id: int, valoracion: ValoracionIn) -> None:
    if db.get(Recomendacion, recomendacion_id) is None:
        raise NoEncontrada
    db.add(
        Feedback(
            recomendacion_id=recomendacion_id,
            puntuacion=valoracion.puntuacion,
            comentario=valoracion.comentario,
        )
    )
    db.commit()
