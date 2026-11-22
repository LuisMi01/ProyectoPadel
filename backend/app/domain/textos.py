"""Precios y textos del catálogo: misma salida que frontend/src/lib/catalogo.ts."""

import math

from app.domain.modelos import Balance, OfertaPala, Pala

TEXTO_BALANCE: dict[Balance, str] = {"bajo": "Bajo", "medio": "Medio", "alto": "Alto"}

_NUMEROS = ("cero", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve")
_ESPACIO_DURO = " "  # para que «129,95 €» no se parta en dos líneas


def redondear(valor: float) -> int:
    """Redondeo de JavaScript (Math.round): las mitades suben."""
    return math.floor(valor + 0.5)


def euros(valor: float) -> str:
    """129.95 -> «129,95 €»."""
    return f"{valor:.2f}".replace(".", ",") + f"{_ESPACIO_DURO}€"


def euros_cortos(valor: float) -> str:
    """150 -> «150 €», 129.95 -> «129,95 €»: sin decimales si no hacen falta."""
    if float(valor).is_integer():
        return f"{int(valor)}{_ESPACIO_DURO}€"
    return euros(valor)


def numero_en_palabra(n: int) -> str:
    """«una», «dos», «tres»… para frases; a partir de diez, la cifra."""
    return _NUMEROS[n] if 0 <= n < len(_NUMEROS) else str(n)


def _disponible(oferta: OfertaPala) -> bool:
    return oferta.disponibilidad != "agotada"


def ofertas_ordenadas(pala: Pala) -> list[OfertaPala]:
    """Primero las disponibles de más barata a más cara; al final, las agotadas."""
    return sorted(pala.ofertas, key=lambda o: (not _disponible(o), o.precio))


def ofertas_disponibles(pala: Pala) -> list[OfertaPala]:
    return [o for o in ofertas_ordenadas(pala) if _disponible(o)]


def mejor_oferta(pala: Pala) -> OfertaPala | None:
    """La oferta disponible más barata, o None si está agotada en todas las tiendas."""
    disponibles = ofertas_disponibles(pala)
    return disponibles[0] if disponibles else None


def precio_desde(pala: Pala) -> float:
    """El precio de la mejor oferta, o el más bajo aunque esté agotada."""
    oferta = mejor_oferta(pala) or ofertas_ordenadas(pala)[0]
    return oferta.precio
