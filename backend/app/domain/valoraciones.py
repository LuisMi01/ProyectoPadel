"""Control, tolerancia, potencia y amortiguación de una pala, de 1 a 5, desde su ficha.

Mismas fórmulas que valoraciones() en frontend/src/lib/catalogo.ts: son iguales para todas las palas
y no se ponen a mano. El redondeo imita a Math.round de JS (round() de Python redondea al par).
"""

import math
from typing import NamedTuple

from app.domain.modelos import Balance, Caras, Forma

PUNTO_DULCE: dict[Forma, float] = {"redonda": 1, "lagrima": 0.5, "diamante": 0}
CABEZA: dict[Balance, float] = {"bajo": 0, "medio": 0.5, "alto": 1}
RIGIDEZ: dict[Caras, float] = {"fibra": 0, "hibrida": 0.5, "carbono": 1}


class Valoraciones(NamedTuple):
    manejabilidad: float
    precision: float
    tolerancia: float
    potencia: float
    amortiguacion: float
    control: float  # control de juego: no se enseña, lo usa el motor (alternativa «más control»)


def _nota(x: float) -> float:
    """Con un decimal, para que se distingan palas de la misma forma."""
    return math.floor((1 + 4 * x) * 10 + 0.5) / 10


def valoraciones(
    forma: Forma, balance: Balance, dureza: int, peso: int, caras: Caras
) -> Valoraciones:
    punto_dulce = PUNTO_DULCE[forma]  # amplio y centrado: 1
    cabeza = CABEZA[balance]  # peso hacia la cabeza: 1
    blandura = (5 - dureza) / 4  # núcleo muy blando: 1; duro: 0
    ligereza = min(1, max(0, (375 - peso) / 30))  # 345 g o menos: 1; 375 g: 0
    rigidez = RIGIDEZ[caras]
    return Valoraciones(
        manejabilidad=_nota(0.6 * ligereza + 0.4 * (1 - cabeza)),
        # Núcleo duro y caras rígidas: la bola sale como la mandas. Un punto dulce pequeño también
        # premia a quien golpea en el centro.
        precision=_nota(0.45 * (1 - blandura) + 0.3 * rigidez + 0.25 * (1 - punto_dulce)),
        # Control de juego (no se enseña): forma, balance bajo, núcleo duro y ligereza.
        control=_nota(
            0.35 * punto_dulce + 0.25 * (1 - cabeza) + 0.25 * (1 - blandura) + 0.15 * ligereza
        ),
        tolerancia=_nota(0.6 * punto_dulce + 0.25 * blandura + 0.15 * (1 - cabeza)),
        potencia=_nota(
            0.4 * (1 - punto_dulce) + 0.3 * cabeza + 0.15 * (1 - blandura) + 0.15 * rigidez
        ),
        amortiguacion=_nota(
            0.4 * blandura + 0.25 * ligereza + 0.2 * (1 - cabeza) + 0.15 * (1 - rigidez)
        ),
    )
