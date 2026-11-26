"""Explicación de una recomendación: con IA (cacheada y con tope diario) o con plantilla."""

import hashlib
import json
import math
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from datetime import UTC, datetime, time

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.llm import ProveedorExplicacionesClaude
from app.core.config import get_settings
from app.domain.modelos import Pala
from app.domain.puertos import ExplicacionFallida, ProveedorExplicaciones
from app.domain.textos import TEXTO_BALANCE, euros_cortos, precio_desde
from app.models import ExplicacionCache

# Abre una sesión de base de datos propia (en la API, SessionLocal).
FabricaSesiones = Callable[[], AbstractContextManager[Session]]

# Súbela al cambiar el prompt o los hechos: invalida la caché.
VERSION_PROMPT = "1"

_RESPUESTAS = {
    "camino": {"primera": "Es su primera pala", "cambio": "Quiere cambiar la pala que tiene"},
    "exp": {
        "nunca": "No ha jugado nunca, o solo unas pocas veces",
        "lt6": "Lleva menos de 6 meses jugando",
        "m6a2": "Lleva entre 6 meses y 2 años jugando",
        "gt2": "Lleva más de 2 años jugando",
    },
    "frec": {
        "1": "Juega una vez por semana o menos",
        "2-3": "Juega dos o tres veces por semana",
        "4+": "Juega cuatro veces por semana o más",
    },
    "estilo": {
        "control": "Aguanta la bola y espera el fallo (juego de control)",
        "mixto": "Hace un poco de todo",
        "potencia": "Busca el remate en cuanto puede",
    },
    "edad": {"adulto": "Tiene 14 años o más", "junior": "Tiene menos de 14 años"},
    "ppto": {
        "100": "Presupuesto máximo: 100 €",
        "150": "Presupuesto máximo: 150 €",
        "250": "Presupuesto máximo: 250 €",
        "max": "Sin tope de presupuesto",
    },
}
_FORMA = {"redonda": "redonda", "lagrima": "de lágrima", "diamante": "de diamante"}
_NIVEL = {1: "iniciación", 2: "medio", 3: "avanzado"}
_DUREZA = {1: "muy blando", 2: "blando", 3: "medio", 4: "medio-duro", 5: "duro"}


def _entero(nota: float) -> int:
    """Las valoraciones sin decimales, como en la web (Math.round: medio hacia arriba)."""
    return math.floor(nota + 0.5)


def hechos(perfil: dict[str, str], palas: list[Pala]) -> str:
    """Texto con las respuestas (sin salud) y los datos de las palas que se envía a la IA."""
    lineas = ["Respuestas de la persona:"]
    for campo, textos in _RESPUESTAS.items():
        if campo in perfil:
            lineas.append(f"- {textos.get(perfil[campo], perfil[campo])}")
    lineas.append("")
    lineas.append("Palas recomendadas, en orden:")
    for i, p in enumerate(palas, start=1):
        nivel = " a ".join(dict.fromkeys(_NIVEL[n] for n in p.nivel))
        lineas.append(
            f"{i}. {p.nombre} ({p.marca}): forma {_FORMA[p.forma]}, balance "
            f"{TEXTO_BALANCE[p.balance].lower()}, {p.peso} g, núcleo {_DUREZA[p.dureza]} "
            f"({p.nucleo}), caras de {p.caras_texto.lower()}, nivel {nivel}, "
            f"manejabilidad {_entero(p.manejabilidad)}/5, precisión {_entero(p.precision)}/5, "
            f"tolerancia {_entero(p.tolerancia)}/5, potencia {_entero(p.potencia)}/5, "
            f"amortiguación {_entero(p.amortiguacion)}/5, "
            f"desde {euros_cortos(precio_desde(p))}."
        )
    return "\n".join(lineas)


def plantilla(palas: list[Pala]) -> str:
    """Explicación sin IA, a partir de los datos de las palas."""
    mejor, otras = palas[0], palas[1:]
    texto = (
        f"{mejor.nombre} es una pala {_FORMA[mejor.forma]} de balance "
        f"{TEXTO_BALANCE[mejor.balance].lower()}, {mejor.peso} g y núcleo "
        f"{_DUREZA[mejor.dureza]}, pensada para nivel "
        f"{' a '.join(dict.fromkeys(_NIVEL[n] for n in mejor.nivel))}. "
        f"Hoy la tienes desde {euros_cortos(precio_desde(mejor))}."
    )
    if otras:
        nombres = " y ".join(p.nombre for p in otras)
        texto += f" También te encajan {nombres}."
    return texto


def _clave(texto_hechos: str, modelo: str) -> str:
    return hashlib.sha256(f"{VERSION_PROMPT}|{modelo}|{texto_hechos}".encode()).hexdigest()


def _proveedor() -> ProveedorExplicaciones | None:
    ajustes = get_settings()
    if ajustes.anthropic_api_key is None:
        return None
    return ProveedorExplicacionesClaude(
        ajustes.anthropic_api_key.get_secret_value(), ajustes.ia_modelo
    )


def _llamadas_de_hoy(db: Session, modelo: str) -> int:
    inicio = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    consulta = select(func.count()).where(
        ExplicacionCache.modelo == modelo, ExplicacionCache.creada >= inicio
    )
    return db.scalar(consulta) or 0


def _valida(texto: str, palas: list[Pala]) -> bool:
    """La IA tiene que nombrar la pala recomendada y no pasarse de largo."""
    return palas[0].nombre.lower() in texto.lower() and len(texto) <= 1500


def generar(db: Session, perfil: dict[str, str], palas: list[Pala]) -> tuple[str, str]:
    """Devuelve el texto y de dónde sale: cache, ia, sin_ia, tope (diario) o plantilla (la IA
    falló o dio un texto no válido)."""
    ajustes = get_settings()
    texto_hechos = hechos(perfil, palas)
    clave = _clave(texto_hechos, ajustes.ia_modelo)

    guardada = db.scalar(select(ExplicacionCache.texto).where(ExplicacionCache.clave == clave))
    if guardada:
        return guardada, "cache"

    proveedor = _proveedor()
    if proveedor is None:
        return plantilla(palas), "sin_ia"
    if _llamadas_de_hoy(db, ajustes.ia_modelo) >= ajustes.ia_llamadas_diarias_max:
        return plantilla(palas), "tope"

    texto = proveedor.explicar(texto_hechos)
    if not texto or not _valida(texto, palas):
        return plantilla(palas), "plantilla"

    db.add(ExplicacionCache(clave=clave, texto=texto, modelo=ajustes.ia_modelo))
    db.commit()
    return texto, "ia"


def obtener(db: Session, perfil: dict[str, str], palas: list[Pala]) -> str:
    return generar(db, perfil, palas)[0]


# --- En flujo (Server-Sent Events) ------------------------------------------------------------


def _sse(evento: str, datos: dict[str, str]) -> str:
    return f"event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


def en_flujo(
    db: Session, perfil: dict[str, str], palas: list[Pala], nueva_sesion: FabricaSesiones
) -> Iterator[str]:
    """Eventos SSE para la web: «texto» con cada trozo según lo escribe la IA y «fin» con el texto
    definitivo y de dónde sale (cache, ia, sin_ia, tope o plantilla).

    Si al terminar el texto de la IA no vale, «fin» trae la plantilla y la web la pone en su lugar.
    La caché y el tope se miran aquí, con la sesión de la petición; el texto nuevo se guarda al
    acabar con una sesión propia, porque el flujo sigue cuando la petición ya ha devuelto la
    respuesta.
    """
    ajustes = get_settings()
    texto_hechos = hechos(perfil, palas)
    clave = _clave(texto_hechos, ajustes.ia_modelo)

    guardada = db.scalar(select(ExplicacionCache.texto).where(ExplicacionCache.clave == clave))
    if guardada:
        return iter([_sse("fin", {"texto": guardada, "origen": "cache"})])
    proveedor = _proveedor()
    if proveedor is None:
        return iter([_sse("fin", {"texto": plantilla(palas), "origen": "sin_ia"})])
    if _llamadas_de_hoy(db, ajustes.ia_modelo) >= ajustes.ia_llamadas_diarias_max:
        return iter([_sse("fin", {"texto": plantilla(palas), "origen": "tope"})])
    return _redactar(proveedor, texto_hechos, clave, palas, nueva_sesion)


def _redactar(
    proveedor: ProveedorExplicaciones,
    texto_hechos: str,
    clave: str,
    palas: list[Pala],
    nueva_sesion: FabricaSesiones,
) -> Iterator[str]:
    partes: list[str] = []
    try:
        for trozo in proveedor.redactar(texto_hechos):
            partes.append(trozo)
            yield _sse("texto", {"t": trozo})
    except ExplicacionFallida:
        partes = []

    texto = "".join(partes).strip()
    if not texto or not _valida(texto, palas):
        yield _sse("fin", {"texto": plantilla(palas), "origen": "plantilla"})
        return

    with nueva_sesion() as sesion:
        sesion.add(ExplicacionCache(clave=clave, texto=texto, modelo=get_settings().ia_modelo))
        try:
            sesion.commit()
        except IntegrityError:
            sesion.rollback()  # otra petición la guardó a la vez: vale cualquiera de las dos
    yield _sse("fin", {"texto": texto, "origen": "ia"})
