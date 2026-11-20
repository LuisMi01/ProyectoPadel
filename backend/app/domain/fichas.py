"""Ficha de una pala nueva a partir de lo que publica la tienda (jobs.daily.extract_specs).

La IA lee el texto del producto y propone la ficha; aquí se prepara ese texto y se descarta lo
que no es creíble antes de dejarla para revisión. Ninguna ficha entra en el catálogo sin que una
persona la apruebe.
"""

from typing import Any

# Más que esto no cabe en la ficha de una pala: se corta para acotar el coste por producto.
MAX_TEXTO = 6000

PESO_MIN, PESO_MAX = 250, 400  # gramos: fuera de aquí es un error de lectura
TEMPORADA_MIN, TEMPORADA_MAX = 2015, 2035


def texto_producto(datos: dict[str, Any]) -> str:
    """Texto que se pasa a la IA: título, marca y el resto de columnas del feed."""
    lineas = []
    for campo in ("titulo", "marca"):
        if datos.get(campo):
            lineas.append(f"{campo}: {datos[campo]}")
    for clave, valor in (datos.get("original") or {}).items():
        if isinstance(valor, str | int | float) and str(valor).strip():
            lineas.append(f"{clave}: {valor}")
    return "\n".join(lineas)[:MAX_TEXTO]


def _entero_entre(valor: Any, minimo: int, maximo: int) -> int | None:
    return valor if isinstance(valor, int) and minimo <= valor <= maximo else None


def limpiar_ficha(ficha: dict[str, Any]) -> dict[str, Any]:
    """Quita los valores imposibles (pesos, años) y ordena el rango de peso."""
    limpia = dict(ficha)
    limpia["temporada"] = _entero_entre(ficha.get("temporada"), TEMPORADA_MIN, TEMPORADA_MAX)
    minimo = _entero_entre(ficha.get("peso_min"), PESO_MIN, PESO_MAX)
    maximo = _entero_entre(ficha.get("peso_max"), PESO_MIN, PESO_MAX)
    if minimo is not None and maximo is not None and minimo > maximo:
        minimo, maximo = maximo, minimo
    limpia["peso_min"], limpia["peso_max"] = minimo, maximo
    return limpia
