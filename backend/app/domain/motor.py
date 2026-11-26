"""Motor de recomendación: reglas puras y deterministas (respuestas + catálogo -> resultado).

Es el mismo algoritmo que frontend/src/lib/recomendador.ts, que calcula la recomendación en el
navegador mientras la web no use la API. tests/test_motor.py comprueba que los dos dan el mismo
resultado. Si cambian las reglas, hay que cambiarlas en los dos sitios y subir MOTOR_VERSION.

Reglas: se descartan las palas que no son de la talla (junior/adulto) o que superan el tope de
gasto; el resto se ordena por afinidad con el perfil que dibujan las respuestas (ver _encaje); a
igualdad de afinidad, va primero la de mejores materiales y, después, la más barata.
"""

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

from app.domain.modelos import (
    BALANCES,
    FORMAS,
    Alternativa,
    Balance,
    Forma,
    Motivo,
    Pala,
    Respuestas,
    Resultado,
    Salud,
)
from app.domain.textos import (
    TEXTO_BALANCE,
    euros_cortos,
    mejor_oferta,
    numero_en_palabra,
    ofertas_disponibles,
    precio_desde,
    redondear,
)

MOTOR_VERSION = "reglas-3"

NOTA_MOLESTIAS = (
    "Una pala adecuada ayuda, pero no trata una lesión. "
    "Si la molestia no se va, consulta a un fisioterapeuta."
)


def tope(r: Respuestas) -> float:
    """Tope de gasto en euros, o infinito si no hay."""
    return math.inf if not r.ppto or r.ppto == "max" else float(r.ppto)


@dataclass(frozen=True)
class _Objetivo:
    forma: Forma
    balance: Balance
    dureza: float
    peso_min: int
    peso_max: int
    nivel: int
    junior: bool
    molestias: bool
    tope: float


def _objetivo(r: Respuestas) -> _Objetivo:
    """Perfil de pala que piden las respuestas."""
    nivel = 1 if r.exp in ("nunca", "lt6") else 3 if r.exp == "gt2" else 2
    molestias = r.mol == "si"
    junior = r.edad == "junior"

    # Con menos de 6 meses ya hay estilo, pero nunca un diamante: eso queda para más de 2 años.
    forma: Forma = "lagrima"
    if r.exp == "nunca" or r.estilo == "control":
        forma = "redonda"
    elif r.estilo == "potencia" and r.exp == "gt2":
        forma = "diamante"
    if molestias and forma == "diamante":
        forma = "lagrima"
    if junior:
        forma = "redonda"

    balance: Balance = "bajo" if forma == "redonda" else "medio" if forma == "lagrima" else "alto"

    dureza: float = 4 if forma == "diamante" else 3
    peso_min, peso_max = (365, 375) if forma == "diamante" else (355, 370)
    if nivel == 1:
        dureza = 2.5
    if molestias:
        dureza = 1  # cuanto más blando, mejor
        peso_min, peso_max = 345, 360
    if junior:
        dureza = 2
        peso_min, peso_max = 300, 330

    return _Objetivo(forma, balance, dureza, peso_min, peso_max, nivel, junior, molestias, tope(r))


@dataclass(frozen=True)
class _Rasgos:
    """Lo que mira _encaje de una pala (y la pala ideal de _encaje_maximo)."""

    forma: Forma
    balance: Balance
    dureza: int
    peso: int
    nivel: tuple[int, int]
    tolerancia: int
    gama: int


# --- Afinidad -----------------------------------------------------------------
# Ordena las palas y da su afinidad de 0 a 100 (igual que en recomendador.ts). Los materiales
# cuentan según la frecuencia, con el tope de lo que da el presupuesto.

PRIORIDAD = {
    "forma": 30,
    "nucleo": 15,
    "balance": 15,
    "nivel": 15,
    "materiales": 10,
    "peso": 10,
    "perdona": 5,
}
PRIORIDAD_MOLESTIAS = {
    "nucleo": 30,
    "forma": 20,
    "peso": 15,
    "balance": 15,
    "nivel": 10,
    "materiales": 5,
    "perdona": 5,
}


def _gama_que_toca(r: Respuestas) -> int:
    """Gama que piden las respuestas: la de la frecuencia, con el tope del presupuesto."""
    por_frecuencia = 3 if r.frec == "4+" else 2 if r.frec == "2-3" else 1
    por_presupuesto = 1 if r.ppto == "100" else 2 if r.ppto == "150" else 3
    return min(por_frecuencia, por_presupuesto)


def _cerca(salto: int) -> float:
    return (1, 0.5, 0)[min(salto, 2)]


def _encaje(pala: Pala | _Rasgos, o: _Objetivo, r: Respuestas, salud: Salud | None) -> float:
    p = PRIORIDAD_MOLESTIAS if o.molestias else PRIORIDAD
    forma = _cerca(abs(FORMAS.index(pala.forma) - FORMAS.index(o.forma)))
    # Con el codo o la muñeca, menos palanca: el balance bajo vale siempre y el alto, nada.
    en_brazo = o.molestias and salud is not None and salud.zona in ("Codo", "Muñeca")
    if en_brazo and pala.balance != "medio":
        balance = 1.0 if pala.balance == "bajo" else 0.0
    else:
        balance = _cerca(abs(BALANCES.index(pala.balance) - BALANCES.index(o.balance)))
    nucleo = max(0, 1 - 0.25 * abs(pala.dureza - o.dureza))
    # Con el hombro o la espalda, más de 360 g no vale (es lo que dice su guía).
    en_espalda = o.molestias and salud is not None and salud.zona in ("Hombro", "Espalda")
    fuera_de_peso = max(o.peso_min - pala.peso, pala.peso - o.peso_max, 0)
    peso = 0 if en_espalda and pala.peso > 360 else max(0, 1 - fuera_de_peso / 25)
    nivel_min, nivel_max = pala.nivel
    nivel = _cerca(max(nivel_min - o.nivel, o.nivel - nivel_max, 0))
    materiales = _cerca(max(0, _gama_que_toca(r) - pala.gama))
    perdona = pala.tolerancia / 5 if r.camino == "primera" or o.nivel == 1 else 0
    return (
        p["forma"] * forma
        + p["balance"] * balance
        + p["nucleo"] * nucleo
        + p["peso"] * peso
        + p["nivel"] * nivel
        + p["materiales"] * materiales
        + p["perdona"] * perdona
    )


def _encaje_maximo(o: _Objetivo, r: Respuestas, salud: Salud | None) -> float:
    """Los puntos de afinidad de la pala ideal para estas respuestas."""
    return max(
        _encaje(_Rasgos(forma, balance, dureza, peso, (o.nivel, o.nivel), 5, 3), o, r, salud)
        for forma in FORMAS
        for balance in BALANCES
        for dureza in (1, 2, 3, 4, 5)
        for peso in (o.peso_min, min(o.peso_max, 360), o.peso_max)
    )


def _afinidad(puntos: float, maximo: float) -> int:
    """De 0 a 100. Redondea como Math.round de JS, no como round()."""
    return math.floor(100 * puntos / maximo + 0.5)


# --- Alternativas -------------------------------------------------------------


@dataclass(frozen=True)
class _Candidata:
    pala: Pala
    puntos: float
    precio: float


TipoAlternativa = Literal["pegada", "control", "brazo", "ahorro", "materiales", "otra"]

ETIQUETAS: dict[TipoAlternativa, str] = {
    "pegada": "Si quieres algo más de pegada",
    "control": "Si quieres algo más de control",
    "brazo": "Si quieres cuidar más el brazo",
    "ahorro": "Si quieres gastar menos",
    "materiales": "Si quieres mejores materiales",
    "otra": "También encaja contigo",
}

_MATERIALES_SENCILLOS = "Materiales más sencillos: menos salida de bola y menos duración."


def _unos_euros(diferencia: float) -> str:
    """«Unos 50 €», redondeado a múltiplos de 5 para que se lea fácil."""
    redondeado = max(5, redondear(abs(diferencia) / 5) * 5)
    return f"Unos {redondeado} €"


def _describir(
    tipo: TipoAlternativa, alt: _Candidata, ref: _Candidata, molestias: bool
) -> tuple[str, str]:
    """Qué se gana y qué se pierde con la alternativa respecto a la recomendada."""
    a, b = alt.pala, ref.pala
    mas_arriba = FORMAS.index(a.forma) > FORMAS.index(b.forma)

    def perdida_general() -> str:
        # Con molestias, lo primero que hay que avisar es de que la pala es menos cómoda.
        if molestias and a.dureza > b.dureza:
            return "Comodidad: el núcleo es más firme y llega más vibración al brazo."
        if a.tolerancia < b.tolerancia:
            return (
                "Algo de tolerancia: el punto dulce es más pequeño y está más arriba."
                if mas_arriba
                else "Algo de tolerancia: perdona menos los golpes descentrados."
            )
        if a.control < b.control:
            return "Algo de control en los golpes de colocación."
        if a.potencia < b.potencia:
            return "Algo de pegada: te costará más definir el punto."
        if a.gama < b.gama:
            return _MATERIALES_SENCILLOS
        if a.dureza > b.dureza or a.peso > b.peso + 4:
            return "Comodidad: exige algo más al brazo."
        if alt.precio > ref.precio + 4:
            return f"{_unos_euros(alt.precio - ref.precio)} más."
        return "Poco: es un cambio de matiz."

    if tipo == "pegada":
        ganas = "Más salida de bola en volea y bandeja" if mas_arriba else "Más pegada en el remate"
        ganas += ", y margen para crecer." if a.nivel[1] > b.nivel[1] else "."
        return ganas, perdida_general()

    if tipo == "control":
        ganas = (
            "Más control y un punto dulce más amplio: perdona más."
            if a.tolerancia > b.tolerancia
            else "Más precisión para colocar la bola donde quieres."
        )
        pierdes = (
            "Pegada: te costará más definir el punto arriba."
            if a.potencia < b.potencia
            else perdida_general()
        )
        return ganas, pierdes

    if tipo == "brazo":
        ganas = (
            "Un núcleo más blando: menos vibración en el brazo."
            if a.dureza < b.dureza
            else f"Unos {b.peso - a.peso} g menos: se mueve con menos esfuerzo."
        )
        pierdes = (
            "Algo de pegada y de salida de bola en los golpes fuertes."
            if a.potencia < b.potencia
            else perdida_general()
        )
        return ganas, pierdes

    if tipo == "ahorro":
        if a.forma == b.forma and a.balance == b.balance:
            misma = " con la misma forma y el mismo balance"
        elif a.forma == b.forma:
            misma = " con la misma forma"
        else:
            misma = ""
        ganas = f"{_unos_euros(ref.precio - alt.precio)} de ahorro{misma}."
        if molestias and a.dureza > b.dureza:
            pierdes = perdida_general()
        elif a.gama < b.gama:
            pierdes = _MATERIALES_SENCILLOS
        elif alt.puntos < ref.puntos and a.forma != b.forma:
            pierdes = "Encaje: la forma se ajusta algo menos a cómo juegas."
        else:
            pierdes = perdida_general()
        return ganas, pierdes

    if tipo == "materiales":
        ganas = (
            "Caras de carbono: más salida de bola y más duración."
            if a.caras == "carbono" and b.caras != "carbono"
            else "Mejores materiales: más salida de bola y más duración."
        )
        pierdes = f"{_unos_euros(alt.precio - ref.precio)} más" + (
            ", y pide algo más de técnica." if a.nivel[0] > b.nivel[0] else "."
        )
        return ganas, pierdes

    # «otra»
    if a.potencia > b.potencia:
        ganas = "Algo más de pegada."
    elif a.control > b.control:
        ganas = "Algo más de control."
    elif alt.precio < ref.precio - 4:
        ganas = f"{_unos_euros(ref.precio - alt.precio)} de ahorro."
    else:
        ganas = "Otra opción con un encaje parecido."
    return ganas, perdida_general()


# Una pala que encaja menos que esto no se enseña como alternativa: no ayuda a elegir.
AFINIDAD_MINIMA_ALTERNATIVA = 50


def _elegir_alternativas(orden: list[_Candidata], o: _Objetivo, maximo: float) -> list[Alternativa]:
    ref = orden[0]
    resto = [c for c in orden[1:] if _afinidad(c.puntos, maximo) >= AFINIDAD_MINIMA_ALTERNATIVA]
    usadas: set[int] = set()
    lista: list[Alternativa] = []

    def mejor_de(
        filtro: Callable[[_Candidata], bool],
        puntos_extra: Callable[[_Candidata], float] = lambda _: 0,
    ) -> _Candidata | None:
        opciones = [c for c in resto if c.pala.id not in usadas and filtro(c)]
        opciones.sort(key=lambda c: -(c.puntos + puntos_extra(c)))  # estable, como en JS
        return opciones[0] if opciones else None

    def anadir(tipo: TipoAlternativa, c: _Candidata | None) -> None:
        if c is None or len(lista) >= 2:
            return
        usadas.add(c.pala.id)
        ganas, pierdes = _describir(tipo, c, ref, o.molestias)
        lista.append(
            Alternativa(c.pala, ETIQUETAS[tipo], ganas, pierdes, _afinidad(c.puntos, maximo))
        )

    # 1) Una alternativa de carácter: más pegada, más control o más cuidado del brazo.
    def suave(c: _Candidata) -> bool:
        return not o.molestias or c.pala.dureza <= 3

    def mas_pegada(c: _Candidata) -> bool:
        return c.pala.potencia > ref.pala.potencia and suave(c)

    def extra_pegada(c: _Candidata) -> float:
        # Escala de _encaje: de 0 a 100. Cada punto más de potencia vale como 6 de encaje.
        return (c.pala.potencia - ref.pala.potencia) * 6

    # Más control de verdad: gana en precisión sin perdonar menos que la recomendada.
    def mas_control(c: _Candidata) -> bool:
        p, r = c.pala, ref.pala
        return (p.control > r.control and p.tolerancia >= r.tolerancia) or (
            p.control == r.control and p.tolerancia > r.tolerancia
        )

    def mas_comoda(c: _Candidata) -> bool:
        p, r = c.pala, ref.pala
        return p.dureza < r.dureza or (p.dureza == r.dureza and p.peso <= r.peso - 5)

    if o.molestias:
        anadir("brazo", mejor_de(mas_comoda))
    if not lista and ref.pala.forma != "diamante":
        pegada = mejor_de(lambda c: mas_pegada(c) and c.pala.gama >= ref.pala.gama, extra_pegada)
        anadir("pegada", pegada if pegada is not None else mejor_de(mas_pegada, extra_pegada))
    if not lista:
        anadir("control", mejor_de(mas_control))

    # 2) Una alternativa de precio: gastar menos o, si ya es la más barata, mejores materiales.
    ahorro_minimo = max(10, ref.precio * 0.12)
    anadir("ahorro", mejor_de(lambda c: c.precio <= ref.precio - ahorro_minimo))
    if len(lista) < 2:
        anadir(
            "materiales",
            mejor_de(lambda c: c.pala.gama > ref.pala.gama and c.pala.forma == ref.pala.forma),
        )

    # 3) Si aún faltan, las siguientes por puntuación.
    while len(lista) < 2:
        siguiente = mejor_de(lambda _: True)
        if siguiente is None:
            break
        anadir("otra", siguiente)

    return lista


# --- Motivos ------------------------------------------------------------------

EXPLICACION_FORMA: dict[Forma, str] = {
    "redonda": (
        "La forma redonda deja el punto dulce amplio y centrado: "
        "perdona los golpes que no salen limpios."
    ),
    "lagrima": (
        "La lágrima sube algo el punto dulce y deja el balance en el medio: "
        "defiende bien y pega cuando toca."
    ),
    "diamante": (
        "El diamante lleva el punto dulce y el peso hacia la cabeza: más pegada en el remate."
    ),
}


def _motivo_forma(pala: Pala, r: Respuestas) -> Motivo:
    if pala.junior:
        return Motivo(
            "Es para menos de 14 años",
            f"Las palas junior son más cortas y ligeras: con {pala.peso} g se mueve sin esfuerzo "
            "y cuida el brazo.",
        )
    if r.exp == "nunca":
        return Motivo("Empiezas de cero", EXPLICACION_FORMA[pala.forma])
    if r.estilo == "control":
        return Motivo(
            "Aguantas la bola y esperas el fallo",
            "La forma redonda y el balance bajo te dan precisión y una pala fácil de mover en "
            "defensa."
            if pala.forma == "redonda"
            else EXPLICACION_FORMA[pala.forma],
        )
    if r.estilo == "potencia":
        if pala.forma == "diamante":
            return Motivo(
                "Buscas el remate y llevas más de 2 años",
                "El diamante lleva el punto dulce y el peso hacia la cabeza: más pegada arriba, "
                "que ya puedes controlar.",
            )
        if pala.forma == "lagrima":
            if r.mol == "si":
                return Motivo(
                    "Buscas el remate, pero notas molestias",
                    "Una lágrima te deja pegar sin cargar el brazo tanto como un diamante.",
                )
            if r.exp == "lt6":
                return Motivo(
                    "Buscas el remate, pero llevas poco tiempo",
                    "Una lágrima te deja atacar sin la exigencia de un diamante mientras coges "
                    "técnica.",
                )
            return Motivo(
                "Buscas el remate",
                EXPLICACION_FORMA["lagrima"]
                if r.exp == "gt2"
                else "Una lágrima te da pegada sin castigar los golpes descentrados tanto como "
                "un diamante.",
            )
        return Motivo("Buscas el remate", EXPLICACION_FORMA[pala.forma])
    if r.estilo == "mixto":
        return Motivo("Haces un poco de todo", EXPLICACION_FORMA[pala.forma])
    return Motivo("Tu forma de jugar", EXPLICACION_FORMA[pala.forma])


def _motivo_uso(pala: Pala, r: Respuestas, salud: Salud | None) -> Motivo:
    balance = TEXTO_BALANCE[pala.balance].lower()

    if r.mol == "si":
        en_brazo = salud is not None and salud.zona in ("Codo", "Muñeca")
        if pala.dureza <= 2:
            explicacion = (
                "Núcleo blando y balance bajo: menos vibración y menos palanca sobre el brazo."
                if en_brazo and pala.balance == "bajo"
                else f"Núcleo blando y {pala.peso} g: transmite menos vibración al brazo."
            )
        else:
            explicacion = (
                "Es la más cómoda que cabe en tu presupuesto: "
                f"{pala.nucleo.lower()} y {pala.peso} g."
            )
        respuesta = "Tienes molestias" if r.exp == "nunca" else "Notas molestias al jugar"
        return Motivo(respuesta, explicacion)
    if pala.junior:
        return Motivo(
            "Está empezando" if r.exp in ("nunca", "lt6") else "Ya lleva un tiempo jugando",
            "La forma redonda perdona los golpes descentrados mientras coge técnica."
            if pala.forma == "redonda"
            else "La lágrima le da algo más de pegada ahora que ya tiene el golpe.",
        )
    if r.camino == "primera":
        return Motivo(
            "Es tu primera pala",
            f"Con balance {balance} y {pala.peso} g se mueve rápido y no te carga el brazo "
            "mientras coges técnica.",
        )
    if r.frec == "4+":
        return Motivo(
            "Juegas cuatro veces o más por semana",
            "Con tanto uso conviene una pala cómoda: la fibra de vidrio es más amable con el brazo."
            if pala.caras == "fibra"
            else "Las caras con carbono aguantan mejor el uso intenso y dan más salida de bola.",
        )
    return Motivo(
        "Ya tienes pala y quieres cambiarla",
        "Mejores materiales que una pala de iniciación: más salida de bola sin perder el control."
        if pala.gama >= 2
        else "Una pala sencilla que cumple: el cambio lo notarás sobre todo en la forma y el "
        "balance.",
    )


def _motivo_precio(pala: Pala, r: Respuestas) -> Motivo:
    limite = tope(r)
    disponibles = ofertas_disponibles(pala)
    total = len(disponibles)

    if limite == math.inf:
        desde = euros_cortos(precio_desde(pala))
        return Motivo(
            "No has puesto tope de gasto",
            f"Hoy la tienes desde {desde}, comparando {numero_en_palabra(total)} tiendas."
            if total > 1
            else f"Hoy la tienes por {desde}.",
        )

    dentro = sum(1 for o in disponibles if o.precio <= limite)
    if total == 1:
        donde = "en la única tienda que la tiene hoy"
    elif dentro == total:
        donde = f"en las {numero_en_palabra(total)} tiendas que la tienen hoy"
    else:
        donde = (
            f"en {numero_en_palabra(dentro)} de las {numero_en_palabra(total)} "
            "tiendas que la tienen hoy"
        )
    return Motivo(
        f"Tu tope son {euros_cortos(limite)}",
        f"Queda por debajo de tu presupuesto {donde}.",
    )


def _titular(pala: Pala) -> str:
    if pala.junior:
        return (
            "Tu pala es una junior redonda."
            if pala.forma == "redonda"
            else "Tu pala es una junior de lágrima."
        )
    return {
        "redonda": "Tu pala es una redonda de control.",
        "lagrima": "Tu pala es una lágrima polivalente.",
        "diamante": "Tu pala es un diamante de potencia.",
    }[pala.forma]


# --- Entrada ------------------------------------------------------------------


def recomendar(r: Respuestas, salud: Salud | None, catalogo: Iterable[Pala]) -> Resultado | None:
    """Calcula la recomendación. None si ninguna pala cumple la talla y el tope de gasto."""
    o = _objetivo(r)

    candidatas: list[_Candidata] = []
    for pala in catalogo:
        if pala.junior != o.junior:
            continue
        oferta = mejor_oferta(pala)
        if oferta is not None and oferta.precio <= o.tope:
            candidatas.append(_Candidata(pala, _encaje(pala, o, r, salud), oferta.precio))
    # Primero la de más afinidad (la que se ve en pantalla); a igualdad, mejores materiales y,
    # después, la más barata.
    maximo = _encaje_maximo(o, r, salud)
    candidatas.sort(key=lambda c: (-_afinidad(c.puntos, maximo), -c.pala.gama, c.precio))

    if not candidatas:
        return None

    mejor = candidatas[0].pala
    return Resultado(
        titular=_titular(mejor),
        mejor=mejor,
        afinidad=_afinidad(candidatas[0].puntos, maximo),
        motivos=(_motivo_forma(mejor, r), _motivo_uso(mejor, r, salud), _motivo_precio(mejor, r)),
        # El puesto (las medallas 2 y 3) lo da la afinidad: primero la que más encaja.
        alternativas=tuple(
            sorted(_elegir_alternativas(candidatas, o, maximo), key=lambda a: -a.afinidad)
        ),
        nota=NOTA_MOLESTIAS if r.mol == "si" else None,
    )
