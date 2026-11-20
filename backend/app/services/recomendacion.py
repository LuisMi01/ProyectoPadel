"""Recomendaciones: se calculan en el navegador; aquí se guardan, se explican y se valoran.

El motor de Python (domain.motor) da lo mismo que el del navegador y se usa para pregenerar cada
mañana las explicaciones de los perfiles más repetidos.
"""

from collections import Counter
from collections.abc import Iterator
from dataclasses import fields
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.catalogo_sql import RepositorioCatalogoSQL
from app.domain.modelos import Pala, Respuestas
from app.domain.motor import recomendar
from app.models import Feedback, Modelo, Recomendacion, RecShown, Usuario
from app.schemas import RecomendacionIn, ValoracionIn
from app.services import explicaciones


class NoEncontrada(Exception):
    """La recomendación pedida no existe."""


class PalaDesconocida(Exception):
    """El navegador manda un modelo que no está activo en el catálogo."""


def guardar(db: Session, datos: RecomendacionIn, usuario: Usuario | None) -> Recomendacion:
    """Guarda la recomendación que ha calculado el navegador: respuestas y palas enseñadas.

    La API no la vuelve a calcular. Así las molestias no salen nunca del navegador, y lo que se
    guarda es exactamente lo que vio la persona (con molestias el resultado cambia, y aquí no se
    podría repetir).
    """
    activos = set(
        db.scalars(select(Modelo.id).where(Modelo.id.in_(datos.palas), Modelo.estado == "activo"))
    )
    if activos != set(datos.palas):
        raise PalaDesconocida

    rec = Recomendacion(
        usuario_id=usuario.id if usuario else None,
        perfil=datos.perfil(),
        versiones={"calculada_en": "navegador"},
    )
    db.add(rec)
    db.flush()
    db.add_all(
        RecShown(recomendacion_id=rec.id, modelo_id=modelo_id, posicion=posicion)
        for posicion, modelo_id in enumerate(datos.palas, start=1)
    )
    db.commit()
    db.refresh(rec)
    return rec


def _para_explicar(db: Session, recomendacion_id: int) -> tuple[dict[str, str], list[Pala]]:
    """Respuestas y palas enseñadas (con los datos de hoy) de una recomendación guardada."""
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
    return rec.perfil, palas


def explicar(db: Session, recomendacion_id: int) -> str:
    """Explicación de una recomendación guardada: con IA si se puede, si no con plantilla."""
    perfil, palas = _para_explicar(db, recomendacion_id)
    return explicaciones.obtener(db, perfil, palas)


def explicar_en_flujo(
    db: Session, recomendacion_id: int, nueva_sesion: explicaciones.FabricaSesiones
) -> Iterator[str]:
    """La misma explicación, como eventos SSE que se envían según la IA la va escribiendo."""
    perfil, palas = _para_explicar(db, recomendacion_id)
    return explicaciones.en_flujo(db, perfil, palas, nueva_sesion)


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
