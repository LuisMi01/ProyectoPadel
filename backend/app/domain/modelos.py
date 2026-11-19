"""Tipos del dominio, independientes de la API y de la base de datos.

Las respuestas usan los mismos valores que el cuestionario del frontend (lib/encuesta.ts), y las
palas, los mismos campos que su catálogo (lib/catalogo.ts), para que la web pueda pasar de calcular
la recomendación en el navegador a pedirla a la API sin traducir nada.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

Camino = Literal["primera", "cambio"]
Experiencia = Literal["nunca", "lt6", "m6a2", "gt2"]
Frecuencia = Literal["1", "2-3", "4+"]
Estilo = Literal["control", "mixto", "potencia"]
RespuestaMolestias = Literal["no", "si", "nc"]
Edad = Literal["adulto", "junior"]
Presupuesto = Literal["80", "150", "250", "max"]

Zona = Literal["Codo", "Hombro", "Muñeca", "Espalda"]
Momento = Literal["Mientras juego", "Al día siguiente", "Casi siempre"]

Forma = Literal["redonda", "lagrima", "diamante"]
Balance = Literal["bajo", "medio", "alto"]
Caras = Literal["fibra", "hibrida", "carbono"]
Disponibilidad = Literal["stock", "ultimas", "agotada"]

FORMAS: tuple[Forma, ...] = ("redonda", "lagrima", "diamante")
BALANCES: tuple[Balance, ...] = ("bajo", "medio", "alto")


@dataclass(frozen=True)
class Respuestas:
    """Respuestas del cuestionario. `mol` es un dato de salud: solo se usa en memoria."""

    camino: Camino | None = None
    exp: Experiencia | None = None
    frec: Frecuencia | None = None
    estilo: Estilo | None = None
    mol: RespuestaMolestias | None = None
    edad: Edad | None = None
    ppto: Presupuesto | None = None


@dataclass(frozen=True)
class Salud:
    """Detalle de la molestia. Nunca se guarda ni se registra en los logs."""

    zona: Zona | None = None
    momento: Momento | None = None


@dataclass(frozen=True)
class OfertaPala:
    id: int
    tienda: str
    precio: float
    disponibilidad: Disponibilidad
    url: str | None = None


@dataclass(frozen=True)
class Pala:
    """Modelo del catálogo con lo que necesitan el motor y la ficha."""

    id: int
    slug: str
    marca: str
    nombre: str
    temporada: int
    junior: bool
    forma: Forma
    balance: Balance
    peso: int
    peso_min: int
    peso_max: int
    dureza: int  # 1 muy blando … 5 duro
    nucleo: str
    caras: Caras
    caras_texto: str
    gama: int  # 1 básica · 2 media · 3 alta
    nivel: tuple[int, int]  # 1 iniciación · 2 medio · 3 avanzado
    control: int
    tolerancia: int
    potencia: int
    ofertas: tuple[OfertaPala, ...] = ()
    resumen: str = ""
    para_ti: tuple[str, ...] = ()
    mejor_otra: tuple[str, ...] = ()


@dataclass(frozen=True)
class Motivo:
    respuesta: str
    explicacion: str


@dataclass(frozen=True)
class Alternativa:
    pala: Pala
    etiqueta: str
    ganas: str
    pierdes: str


@dataclass(frozen=True)
class Resultado:
    titular: str
    mejor: Pala
    motivos: tuple[Motivo, ...]
    alternativas: tuple[Alternativa, ...]
    nota: str | None = None


@dataclass(frozen=True)
class ProductoFeed:
    """Producto de un feed ya traducido a nuestros campos, antes de emparejarlo con su SKU."""

    referencia: str  # identificador del producto en la tienda
    titulo: str
    precio: Decimal | None
    url: str | None
    disponible: bool
    ean: str | None = None
    marca: str | None = None
    datos: dict[str, object] = field(default_factory=dict)  # fila original del feed
