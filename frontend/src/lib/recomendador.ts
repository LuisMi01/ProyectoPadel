/**
 * Recomendador de palas (función pura: respuestas + catálogo -> recomendación).
 *
 * Se ejecuta en el navegador para que la web funcione sin depender del backend,
 * donde el motor (POST /recomendaciones) sigue pendiente. Cuando exista, este
 * módulo es el que se sustituye por la llamada a la API.
 *
 * Reglas: se descartan las palas que no son de la talla (junior/adulto) o que
 * superan el tope de gasto; el resto se ordena por afinidad con el perfil que
 * dibujan las respuestas (ver encaje()); a igualdad de afinidad, va primero la de
 * mejores materiales y, después, la más barata.
 */
import {
  BALANCES,
  FORMAS,
  type Balance,
  type Forma,
  type Nivel,
  type Pala,
  eurosCortos,
  mejorOferta,
  numeroEnPalabra,
  ofertasDisponibles,
  precioDesde,
  textoBalance,
} from "@/lib/catalogo";
import { type Respuestas, type Salud, tope } from "@/lib/encuesta";

export interface Motivo {
  /** La respuesta del usuario que lo decide. */
  respuesta: string;
  explicacion: string;
}

export interface Alternativa {
  pala: Pala;
  /** «Si quieres algo más de pegada», «Si quieres gastar menos»… */
  etiqueta: string;
  ganas: string;
  pierdes: string;
  /** Encaje con las respuestas, de 0 a 100 (ver encaje()). */
  afinidad: number;
}

export interface Recomendacion {
  /** «Tu pala es una redonda de control.» */
  titular: string;
  mejor: Pala;
  /** Encaje de la mejor con las respuestas, de 0 a 100. */
  afinidad: number;
  motivos: Motivo[];
  alternativas: Alternativa[];
  /** Aviso que acompaña a la recomendación cuando hay molestias. */
  nota: string | null;
}

interface Objetivo {
  forma: Forma;
  balance: Balance;
  dureza: number;
  pesoMin: number;
  pesoMax: number;
  nivel: Nivel;
  junior: boolean;
  molestias: boolean;
  tope: number;
}

/** Perfil de pala que piden las respuestas. */
function objetivo(r: Respuestas): Objetivo {
  const nivel: Nivel = r.exp === "nunca" || r.exp === "lt6" ? 1 : r.exp === "gt2" ? 3 : 2;
  const molestias = r.mol === "si";
  const junior = r.edad === "junior";

  // Con menos de 6 meses ya hay estilo, pero nunca un diamante: eso queda para más de 2 años.
  let forma: Forma = "lagrima";
  if (r.exp === "nunca" || r.estilo === "control") forma = "redonda";
  else if (r.estilo === "potencia" && r.exp === "gt2") forma = "diamante";
  if (molestias && forma === "diamante") forma = "lagrima";
  if (junior) forma = "redonda";

  const balance: Balance = forma === "redonda" ? "bajo" : forma === "lagrima" ? "medio" : "alto";

  let dureza = forma === "diamante" ? 4 : 3;
  let [pesoMin, pesoMax] = forma === "diamante" ? [365, 375] : [355, 370];
  if (nivel === 1) dureza = 2.5;
  if (molestias) {
    dureza = 1; // cuanto más blando, mejor
    [pesoMin, pesoMax] = [345, 360];
  }
  if (junior) {
    dureza = 2;
    [pesoMin, pesoMax] = [300, 330];
  }

  return { forma, balance, dureza, pesoMin, pesoMax, nivel, junior, molestias, tope: tope(r) };
}

/** Lo que mira encaje() de una pala. */
type Rasgos = Pick<Pala, "forma" | "balance" | "dureza" | "peso" | "nivel" | "tolerancia" | "gama">;

// --- Afinidad -----------------------------------------------------------------
// Ordena las palas y da su afinidad de 0 a 100: la primera es siempre la que más encaja. Más peso
// en lo que más importa. Los
// materiales cuentan según lo que pide la frecuencia, pero nunca por encima de lo que da el
// presupuesto: una pala barata que encaja no puede salir con poca afinidad por no ser de carbono si
// el tope no llega para carbono. Lo que se acerca suma: una lágrima cuando tocaba diamante se lleva
// la mitad de los puntos de la forma.

/** Puntos de cada cosa (suman 100). Con molestias manda el núcleo, y después el peso. */
const PRIORIDAD = { forma: 30, nucleo: 15, balance: 15, nivel: 15, materiales: 10, peso: 10, perdona: 5 };
const PRIORIDAD_MOLESTIAS = { nucleo: 30, forma: 20, peso: 15, balance: 15, nivel: 10, materiales: 5, perdona: 5 };

/** Gama de materiales que piden las respuestas: la de la frecuencia, con el tope del presupuesto. */
function gamaQueToca(r: Respuestas): number {
  const porFrecuencia = r.frec === "4+" ? 3 : r.frec === "2-3" ? 2 : 1;
  const porPresupuesto = r.ppto === "100" ? 1 : r.ppto === "150" ? 2 : 3;
  return Math.min(porFrecuencia, porPresupuesto);
}

/** Puntos de afinidad, sin pasar a porcentaje (afinidad() los divide entre los de la pala ideal). */
function encaje(pala: Rasgos, o: Objetivo, r: Respuestas, salud: Salud | null): number {
  const p = o.molestias ? PRIORIDAD_MOLESTIAS : PRIORIDAD;
  const cerca = (salto: number) => [1, 0.5, 0][Math.min(salto, 2)];

  const forma = cerca(Math.abs(FORMAS.indexOf(pala.forma) - FORMAS.indexOf(o.forma)));
  // Con el codo o la muñeca, menos palanca: el balance bajo vale siempre y el alto, nada.
  const enBrazo = o.molestias && (salud?.zona === "Codo" || salud?.zona === "Muñeca");
  const balance =
    enBrazo && pala.balance !== "medio"
      ? Number(pala.balance === "bajo")
      : cerca(Math.abs(BALANCES.indexOf(pala.balance) - BALANCES.indexOf(o.balance)));
  const nucleo = Math.max(0, 1 - 0.25 * Math.abs(pala.dureza - o.dureza));
  // Con el hombro o la espalda, más de 360 g no vale (es lo que dice su guía).
  const enEspalda = o.molestias && (salud?.zona === "Hombro" || salud?.zona === "Espalda");
  const fueraDePeso = Math.max(o.pesoMin - pala.peso, pala.peso - o.pesoMax, 0);
  const peso = enEspalda && pala.peso > 360 ? 0 : Math.max(0, 1 - fueraDePeso / 25);
  const [nivelMin, nivelMax] = pala.nivel;
  const nivel = cerca(Math.max(nivelMin - o.nivel, o.nivel - nivelMax, 0));
  // Materiales iguales o mejores que los que tocan: todos los puntos.
  const materiales = cerca(Math.max(0, gamaQueToca(r) - pala.gama));
  // Que perdone solo cuenta para quien empieza.
  const perdona = r.camino === "primera" || o.nivel === 1 ? pala.tolerancia / 5 : 0;

  return (
    p.forma * forma +
    p.balance * balance +
    p.nucleo * nucleo +
    p.peso * peso +
    p.nivel * nivel +
    p.materiales * materiales +
    p.perdona * perdona
  );
}

/**
 * Los puntos de afinidad de la pala ideal para estas respuestas. Se buscan probando todas las
 * combinaciones, para que siga siendo cierto aunque cambien las prioridades de encaje().
 * De peso se prueban los extremos del rango que toca y 360 g.
 */
function encajeMaximo(o: Objetivo, r: Respuestas, salud: Salud | null): number {
  let maximo = 0;
  for (const forma of FORMAS) {
    for (const balance of BALANCES) {
      for (const dureza of [1, 2, 3, 4, 5] as const) {
        for (const peso of [o.pesoMin, Math.min(o.pesoMax, 360), o.pesoMax]) {
          const ideal: Rasgos = { forma, balance, dureza, peso, nivel: [o.nivel, o.nivel], tolerancia: 5, gama: 3 };
          maximo = Math.max(maximo, encaje(ideal, o, r, salud));
        }
      }
    }
  }
  return maximo;
}

/** Afinidad de 0 a 100: 100 es la pala ideal para esas respuestas y ese presupuesto. */
function afinidad(puntos: number, maximo: number): number {
  return Math.round((100 * puntos) / maximo);
}

// --- Alternativas -------------------------------------------------------------

interface Candidata {
  pala: Pala;
  puntos: number;
  precio: number;
}

type TipoAlternativa = "pegada" | "control" | "brazo" | "ahorro" | "materiales" | "otra";

const ETIQUETAS: Record<TipoAlternativa, string> = {
  pegada: "Si quieres algo más de pegada",
  control: "Si quieres algo más de control",
  brazo: "Si quieres cuidar más el brazo",
  ahorro: "Si quieres gastar menos",
  materiales: "Si quieres mejores materiales",
  otra: "También encaja contigo",
};

/** «Unos 50 €», redondeado a múltiplos de 5 para que se lea fácil. */
function unosEuros(diferencia: number): string {
  const redondeado = Math.max(5, Math.round(Math.abs(diferencia) / 5) * 5);
  return `Unos ${redondeado} €`;
}

function describir(
  tipo: TipoAlternativa,
  alt: Candidata,
  ref: Candidata,
  molestias: boolean,
): { ganas: string; pierdes: string } {
  const a = alt.pala;
  const b = ref.pala;
  const masArriba = FORMAS.indexOf(a.forma) > FORMAS.indexOf(b.forma);

  const perdidaGeneral = (): string => {
    // Con molestias, lo primero que hay que avisar es de que la pala es menos cómoda.
    if (molestias && a.dureza > b.dureza) {
      return "Comodidad: el núcleo es más firme y llega más vibración al brazo.";
    }
    if (a.tolerancia < b.tolerancia) {
      return masArriba
        ? "Algo de tolerancia: el punto dulce es más pequeño y está más arriba."
        : "Algo de tolerancia: perdona menos los golpes descentrados.";
    }
    if (a.control < b.control) return "Algo de control en los golpes de colocación.";
    if (a.potencia < b.potencia) return "Algo de pegada: te costará más definir el punto.";
    if (a.gama < b.gama) return "Materiales más sencillos: menos salida de bola y menos duración.";
    if (a.dureza > b.dureza || a.peso > b.peso + 4) return "Comodidad: exige algo más al brazo.";
    if (alt.precio > ref.precio + 4) return `${unosEuros(alt.precio - ref.precio)} más.`;
    return "Poco: es un cambio de matiz.";
  };

  switch (tipo) {
    case "pegada":
      return {
        ganas:
          (masArriba ? "Más salida de bola en volea y bandeja" : "Más pegada en el remate") +
          (a.nivel[1] > b.nivel[1] ? ", y margen para crecer." : "."),
        pierdes: perdidaGeneral(),
      };
    case "control":
      return {
        ganas:
          a.tolerancia > b.tolerancia
            ? "Más control y un punto dulce más amplio: perdona más."
            : "Más precisión para colocar la bola donde quieres.",
        pierdes:
          a.potencia < b.potencia ? "Pegada: te costará más definir el punto arriba." : perdidaGeneral(),
      };
    case "brazo":
      return {
        ganas:
          a.dureza < b.dureza
            ? "Un núcleo más blando: menos vibración en el brazo."
            : `Unos ${b.peso - a.peso} g menos: se mueve con menos esfuerzo.`,
        pierdes:
          a.potencia < b.potencia
            ? "Algo de pegada y de salida de bola en los golpes fuertes."
            : perdidaGeneral(),
      };
    case "ahorro": {
      const misma =
        a.forma === b.forma && a.balance === b.balance
          ? " con la misma forma y el mismo balance"
          : a.forma === b.forma
            ? " con la misma forma"
            : "";
      return {
        ganas: `${unosEuros(ref.precio - alt.precio)} de ahorro${misma}.`,
        pierdes:
          molestias && a.dureza > b.dureza
            ? perdidaGeneral()
            : a.gama < b.gama
              ? "Materiales más sencillos: menos salida de bola y menos duración."
            : alt.puntos < ref.puntos && a.forma !== b.forma
              ? "Encaje: la forma se ajusta algo menos a cómo juegas."
              : perdidaGeneral(),
      };
    }
    case "materiales":
      return {
        ganas:
          a.caras === "carbono" && b.caras !== "carbono"
            ? "Caras de carbono: más salida de bola y más duración."
            : "Mejores materiales: más salida de bola y más duración.",
        pierdes:
          `${unosEuros(alt.precio - ref.precio)} más` +
          (a.nivel[0] > b.nivel[0] ? ", y pide algo más de técnica." : "."),
      };
    case "otra":
      return {
        ganas:
          a.potencia > b.potencia
            ? "Algo más de pegada."
            : a.control > b.control
              ? "Algo más de control."
              : alt.precio < ref.precio - 4
                ? `${unosEuros(ref.precio - alt.precio)} de ahorro.`
                : "Otra opción con un encaje parecido.",
        pierdes: perdidaGeneral(),
      };
  }
}

/** Una pala que encaja menos que esto no se enseña como alternativa: no ayuda a elegir. */
const AFINIDAD_MINIMA_ALTERNATIVA = 50;

function elegirAlternativas(orden: Candidata[], o: Objetivo, maximo: number): Alternativa[] {
  const [ref, ...todas] = orden;
  const resto = todas.filter((c) => afinidad(c.puntos, maximo) >= AFINIDAD_MINIMA_ALTERNATIVA);
  const usadas = new Set<number>();
  const lista: Alternativa[] = [];

  const mejorDe = (filtro: (c: Candidata) => boolean, puntosExtra: (c: Candidata) => number = () => 0) =>
    resto
      .filter((c) => !usadas.has(c.pala.id) && filtro(c))
      .sort((x, y) => y.puntos + puntosExtra(y) - (x.puntos + puntosExtra(x)))[0];

  const anadir = (tipo: TipoAlternativa, c: Candidata | undefined) => {
    if (!c || lista.length >= 2) return;
    usadas.add(c.pala.id);
    lista.push({
      pala: c.pala,
      etiqueta: ETIQUETAS[tipo],
      ...describir(tipo, c, ref, o.molestias),
      afinidad: afinidad(c.puntos, maximo),
    });
  };

  // 1) Una alternativa de carácter: más pegada, más control o más cuidado del brazo.
  const suave = (c: Candidata) => !o.molestias || c.pala.dureza <= 3;
  const masPegada = (c: Candidata) => c.pala.potencia > ref.pala.potencia && suave(c);
  // Escala de encaje(): de 0 a 100. Cada punto más de potencia vale como 6 de encaje.
  const extraPegada = (c: Candidata) => (c.pala.potencia - ref.pala.potencia) * 6;
  // Más control de verdad: gana en precisión sin perdonar menos que la recomendada.
  const masControl = (c: Candidata) =>
    (c.pala.control > ref.pala.control && c.pala.tolerancia >= ref.pala.tolerancia) ||
    (c.pala.control === ref.pala.control && c.pala.tolerancia > ref.pala.tolerancia);
  const masComoda = (c: Candidata) =>
    c.pala.dureza < ref.pala.dureza || (c.pala.dureza === ref.pala.dureza && c.pala.peso <= ref.pala.peso - 5);

  if (o.molestias) {
    anadir("brazo", mejorDe(masComoda));
  }
  if (lista.length === 0 && ref.pala.forma !== "diamante") {
    anadir(
      "pegada",
      mejorDe((c) => masPegada(c) && c.pala.gama >= ref.pala.gama, extraPegada) ?? mejorDe(masPegada, extraPegada),
    );
  }
  if (lista.length === 0) {
    anadir("control", mejorDe(masControl));
  }

  // 2) Una alternativa de precio: gastar menos o, si ya es la más barata, mejores materiales.
  const ahorroMinimo = Math.max(10, ref.precio * 0.12);
  anadir(
    "ahorro",
    mejorDe((c) => c.precio <= ref.precio - ahorroMinimo),
  );
  if (lista.length < 2) {
    anadir(
      "materiales",
      mejorDe((c) => c.pala.gama > ref.pala.gama && c.pala.forma === ref.pala.forma),
    );
  }

  // 3) Si aún faltan, las siguientes por puntuación.
  while (lista.length < 2) {
    const siguiente = mejorDe(() => true);
    if (!siguiente) break;
    anadir("otra", siguiente);
  }

  return lista;
}

// --- Motivos ------------------------------------------------------------------

const EXPLICACION_FORMA: Record<Forma, string> = {
  redonda:
    "La forma redonda deja el punto dulce amplio y centrado: perdona los golpes que no salen limpios.",
  lagrima:
    "La lágrima sube algo el punto dulce y deja el balance en el medio: defiende bien y pega cuando toca.",
  diamante: "El diamante lleva el punto dulce y el peso hacia la cabeza: más pegada en el remate.",
};

function motivoForma(pala: Pala, r: Respuestas): Motivo {
  if (pala.junior) {
    return {
      respuesta: "Es para menos de 14 años",
      explicacion: `Las palas junior son más cortas y ligeras: con ${pala.peso} g se mueve sin esfuerzo y cuida el brazo.`,
    };
  }
  if (r.exp === "nunca") {
    return { respuesta: "Empiezas de cero", explicacion: EXPLICACION_FORMA[pala.forma] };
  }
  if (r.estilo === "control") {
    return {
      respuesta: "Aguantas la bola y esperas el fallo",
      explicacion:
        pala.forma === "redonda"
          ? "La forma redonda y el balance bajo te dan precisión y una pala fácil de mover en defensa."
          : EXPLICACION_FORMA[pala.forma],
    };
  }
  if (r.estilo === "potencia") {
    if (pala.forma === "diamante") {
      return {
        respuesta: "Buscas el remate y llevas más de 2 años",
        explicacion:
          "El diamante lleva el punto dulce y el peso hacia la cabeza: más pegada arriba, que ya puedes controlar.",
      };
    }
    if (pala.forma === "lagrima") {
      if (r.mol === "si") {
        return {
          respuesta: "Buscas el remate, pero notas molestias",
          explicacion: "Una lágrima te deja pegar sin cargar el brazo tanto como un diamante.",
        };
      }
      if (r.exp === "lt6") {
        return {
          respuesta: "Buscas el remate, pero llevas poco tiempo",
          explicacion: "Una lágrima te deja atacar sin la exigencia de un diamante mientras coges técnica.",
        };
      }
      return {
        respuesta: "Buscas el remate",
        explicacion:
          r.exp === "gt2"
            ? EXPLICACION_FORMA.lagrima
            : "Una lágrima te da pegada sin castigar los golpes descentrados tanto como un diamante.",
      };
    }
    return { respuesta: "Buscas el remate", explicacion: EXPLICACION_FORMA[pala.forma] };
  }
  if (r.estilo === "mixto") {
    return { respuesta: "Haces un poco de todo", explicacion: EXPLICACION_FORMA[pala.forma] };
  }
  return { respuesta: "Tu forma de jugar", explicacion: EXPLICACION_FORMA[pala.forma] };
}

function motivoUso(pala: Pala, r: Respuestas, salud: Salud | null): Motivo {
  const balance = textoBalance[pala.balance].toLowerCase();

  if (r.mol === "si") {
    const enBrazo = salud?.zona === "Codo" || salud?.zona === "Muñeca";
    return {
      respuesta: r.exp === "nunca" ? "Tienes molestias" : "Notas molestias al jugar",
      explicacion:
        pala.dureza <= 2
          ? enBrazo && pala.balance === "bajo"
            ? "Núcleo blando y balance bajo: menos vibración y menos palanca sobre el brazo."
            : `Núcleo blando y ${pala.peso} g: transmite menos vibración al brazo.`
          : `Es la más cómoda que cabe en tu presupuesto: ${pala.nucleo.toLowerCase()} y ${pala.peso} g.`,
    };
  }
  if (pala.junior) {
    return {
      respuesta: r.exp === "nunca" || r.exp === "lt6" ? "Está empezando" : "Ya lleva un tiempo jugando",
      explicacion:
        pala.forma === "redonda"
          ? "La forma redonda perdona los golpes descentrados mientras coge técnica."
          : "La lágrima le da algo más de pegada ahora que ya tiene el golpe.",
    };
  }
  if (r.camino === "primera") {
    return {
      respuesta: "Es tu primera pala",
      explicacion: `Con balance ${balance} y ${pala.peso} g se mueve rápido y no te carga el brazo mientras coges técnica.`,
    };
  }
  if (r.frec === "4+") {
    return {
      respuesta: "Juegas cuatro veces o más por semana",
      explicacion:
        pala.caras === "fibra"
          ? "Con tanto uso conviene una pala cómoda: la fibra de vidrio es más amable con el brazo."
          : "Las caras con carbono aguantan mejor el uso intenso y dan más salida de bola.",
    };
  }
  return {
    respuesta: "Ya tienes pala y quieres cambiarla",
    explicacion:
      pala.gama >= 2
        ? "Mejores materiales que una pala de iniciación: más salida de bola sin perder el control."
        : "Una pala sencilla que cumple: el cambio lo notarás sobre todo en la forma y el balance.",
  };
}

function motivoPrecio(pala: Pala, r: Respuestas): Motivo {
  const limite = tope(r);
  const disponibles = ofertasDisponibles(pala);
  const total = disponibles.length;

  if (limite === Infinity) {
    return {
      respuesta: "No has puesto tope de gasto",
      explicacion:
        total > 1
          ? `Hoy la tienes desde ${eurosCortos(precioDesde(pala))}, comparando ${numeroEnPalabra(total)} tiendas.`
          : `Hoy la tienes por ${eurosCortos(precioDesde(pala))}.`,
    };
  }

  const dentro = disponibles.filter((o) => o.precio <= limite).length;
  let donde: string;
  if (total === 1) donde = "en la única tienda que la tiene hoy";
  else if (dentro === total) donde = `en las ${numeroEnPalabra(total)} tiendas que la tienen hoy`;
  else donde = `en ${numeroEnPalabra(dentro)} de las ${numeroEnPalabra(total)} tiendas que la tienen hoy`;

  return {
    respuesta: `Tu tope son ${eurosCortos(limite)}`,
    explicacion: `Queda por debajo de tu presupuesto ${donde}.`,
  };
}

function titular(pala: Pala): string {
  if (pala.junior) {
    return pala.forma === "redonda" ? "Tu pala es una junior redonda." : "Tu pala es una junior de lágrima.";
  }
  switch (pala.forma) {
    case "redonda":
      return "Tu pala es una redonda de control.";
    case "lagrima":
      return "Tu pala es una lágrima polivalente.";
    case "diamante":
      return "Tu pala es un diamante de potencia.";
  }
}

// --- Entrada ------------------------------------------------------------------

/**
 * Calcula la recomendación. Devuelve null si ninguna pala del catálogo cumple
 * los filtros (talla y tope de gasto).
 */
export function recomendar(r: Respuestas, salud: Salud | null, catalogo: Pala[]): Recomendacion | null {
  const o = objetivo(r);
  const maximo = encajeMaximo(o, r, salud);

  // Primero la de más afinidad (la que se ve en pantalla); a igualdad, mejores materiales y,
  // después, la más barata.
  const candidatas: Candidata[] = catalogo
    .filter((pala) => pala.junior === o.junior)
    .flatMap((pala) => {
      const oferta = mejorOferta(pala);
      return oferta && oferta.precio <= o.tope ? [{ pala, precio: oferta.precio, puntos: encaje(pala, o, r, salud) }] : [];
    })
    .sort(
      (a, b) =>
        afinidad(b.puntos, maximo) - afinidad(a.puntos, maximo) || b.pala.gama - a.pala.gama || a.precio - b.precio,
    );

  if (candidatas.length === 0) return null;

  const mejor = candidatas[0].pala;
  return {
    titular: titular(mejor),
    mejor,
    afinidad: afinidad(candidatas[0].puntos, maximo),
    motivos: [motivoForma(mejor, r), motivoUso(mejor, r, salud), motivoPrecio(mejor, r)],
    // El puesto (las medallas 2 y 3) lo da la afinidad: primero la que más encaja.
    alternativas: elegirAlternativas(candidatas, o, maximo).sort((a, b) => b.afinidad - a.afinidad),
    nota:
      r.mol === "si"
        ? "Una pala adecuada ayuda, pero no trata una lesión. Si la molestia no se va, consulta a un fisioterapeuta."
        : null,
  };
}

/** Diferencia en pocas palabras entre una pala y otra de referencia (para «Palas parecidas»). */
export function diferenciaCorta(pala: Pala, ref: Pala): string {
  const precio = precioDesde(pala) - precioDesde(ref);
  const masBarata = precio <= -10;
  const masCara = precio >= 10;
  const masBlanda = pala.dureza < ref.dureza;
  const masLigera = pala.peso < ref.peso;

  // Entre formas distintas manda el carácter de juego.
  if (pala.forma !== ref.forma) {
    if (pala.potencia > ref.potencia) {
      return pala.tolerancia < ref.tolerancia ? "Más pegada, menos tolerancia" : "Más pegada";
    }
    if (pala.control > ref.control || pala.tolerancia > ref.tolerancia) {
      return pala.potencia < ref.potencia ? "Más control, menos pegada" : "Más control y tolerancia";
    }
    return "Otra forma, sensaciones parecidas";
  }

  // Con la misma forma, primero el salto de gama y de precio; después, el tacto.
  if (masBarata && pala.gama < ref.gama) {
    return masBlanda && masLigera ? "Más barata, más blanda y ligera" : "Más barata, materiales más sencillos";
  }
  if (masCara && pala.gama > ref.gama) return "Mejores materiales, más cara";
  if (masBlanda && masLigera) return ref.dureza <= 2 ? "Aún más blanda y ligera" : "Más blanda y ligera";
  if (masBlanda) return "Núcleo más blando, más cómoda";
  if (pala.dureza > ref.dureza) {
    if (pala.dureza >= 4) return "Núcleo más firme, más exigente";
    return pala.potencia > ref.potencia ? "Algo más firme, con más pegada" : "Núcleo algo más firme";
  }
  if (pala.potencia > ref.potencia) return "Algo más de pegada";
  if (pala.tolerancia > ref.tolerancia) return "Perdona más los fallos";
  if (masBarata) return "Parecida y más barata";
  if (masCara) return "Parecida, con mejores acabados";
  return "Muy parecida en forma y balance";
}

/** Hasta tres palas parecidas a una dada: dos de su forma y una de la forma vecina. */
export function palasParecidas(pala: Pala, catalogo: Pala[]): Pala[] {
  const otras = catalogo.filter((p) => p.id !== pala.id && p.junior === pala.junior);
  const distancia = (p: Pala) =>
    Math.abs(p.gama - pala.gama) * 2 +
    Math.abs(p.dureza - pala.dureza) +
    Math.abs(precioDesde(p) - precioDesde(pala)) / 50;

  const mismaForma = otras
    .filter((p) => p.forma === pala.forma)
    .sort((a, b) => distancia(a) - distancia(b))
    .slice(0, 2);

  // De la forma vecina: hacia más pegada si la pala ya tira a potencia; si no, hacia más control.
  const i = FORMAS.indexOf(pala.forma);
  const haciaPotencia = pala.forma === "redonda" || (pala.forma === "lagrima" && pala.potencia > pala.control);
  const vecinaForma = FORMAS[haciaPotencia ? i + 1 : i - 1];
  const vecina = otras
    .filter((p) => p.forma === vecinaForma)
    .sort(
      (a, b) =>
        Math.abs(a.gama - pala.gama) - Math.abs(b.gama - pala.gama) ||
        (haciaPotencia ? b.potencia - a.potencia : b.control - a.control) ||
        distancia(a) - distancia(b),
    )[0];

  const elegidas = vecina ? [...mismaForma, vecina] : mismaForma;
  // Si faltan (p. ej. en junior), se completa con las más cercanas que queden.
  for (const p of [...otras].sort((a, b) => distancia(a) - distancia(b))) {
    if (elegidas.length >= 3) break;
    if (!elegidas.includes(p)) elegidas.push(p);
  }
  return elegidas.sort((a, b) => precioDesde(a) - precioDesde(b));
}
