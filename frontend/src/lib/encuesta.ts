/**
 * Flujo del cuestionario (máquina de estados pura, sin DOM).
 *
 *   Antes de empezar ─> 1. Experiencia ─┬─ ya juega ──────> 2. Frecuencia -> 3. Estilo ─┐
 *                                       └─ nunca o casi nunca ─────────────────────────┴─> Molestias
 *   Molestias ─┬─ sí ─> Zona y momento (con consentimiento) ─┐
 *              └─ no / prefiero no contestar ────────────────┴─> Edad -> Presupuesto -> fin
 *
 * Las molestias son un dato de salud: sirven para calcular la recomendación y
 * no se guardan con el progreso ni en el historial (ver SALUD más abajo).
 */
import type { Caras, Forma } from "@/lib/catalogo";

export type Pregunta = "camino" | "exp" | "frec" | "estilo" | "mol" | "edad" | "ppto";
export type Paso = Pregunta | "zona" | "fin";

export interface Respuestas {
  camino?: "primera" | "cambio";
  exp?: "nunca" | "lt6" | "m6a2" | "gt2";
  frec?: "1" | "2-3" | "4+";
  estilo?: "control" | "mixto" | "potencia";
  mol?: "no" | "si" | "nc";
  edad?: "adulto" | "junior";
  ppto?: "100" | "150" | "250" | "max";
}

export const ZONAS = ["Codo", "Hombro", "Muñeca", "Espalda"] as const;
export const MOMENTOS = ["Mientras juego", "Al día siguiente", "Casi siempre"] as const;
export type Zona = (typeof ZONAS)[number];
export type Momento = (typeof MOMENTOS)[number];

/** Detalle de la molestia. Solo existe mientras dura la pestaña. */
export interface Salud {
  zona: Zona | null;
  momento: Momento | null;
  consentimiento: boolean;
}

export const SIN_SALUD: Salud = { zona: null, momento: null, consentimiento: false };

export interface Opcion {
  id: string;
  /** Texto de la opción en el cuestionario. */
  titulo: string;
  detalle?: string;
  /** Texto corto para el resumen de respuestas en la recomendación. */
  chip?: string;
}

export interface DefPregunta {
  /** Nombre corto: «Experiencia», «Estilo»… */
  nombre: string;
  pregunta: string;
  ayuda: string;
  opciones: Opcion[];
}

export const PREGUNTAS: Record<Pregunta, DefPregunta> = {
  camino: {
    nombre: "Punto de partida",
    pregunta: "¿Qué te trae por aquí?",
    ayuda: "Así sabemos si partimos de cero o de la pala que ya tienes.",
    opciones: [
      {
        id: "primera",
        titulo: "Es mi primera pala",
        detalle: "Empiezo a jugar o voy con una prestada.",
        chip: "Primera pala",
      },
      {
        id: "cambio",
        titulo: "Quiero cambiar la mía",
        detalle: "Ya tengo pala y busco una que me vaya mejor.",
        chip: "Cambio de pala",
      },
    ],
  },
  exp: {
    nombre: "Experiencia",
    pregunta: "¿Cuánto tiempo llevas jugando?",
    ayuda: "Cuenta desde que juegas con cierta regularidad.",
    opciones: [
      {
        id: "nunca",
        titulo: "Nunca, o solo unas pocas veces",
        detalle: "Nos saltamos frecuencia y estilo: todavía no hay.",
        chip: "Empiezo de cero",
      },
      { id: "lt6", titulo: "Menos de 6 meses", detalle: "Jugando con cierta regularidad." },
      { id: "m6a2", titulo: "Entre 6 meses y 2 años" },
      { id: "gt2", titulo: "Más de 2 años" },
    ],
  },
  frec: {
    nombre: "Frecuencia",
    pregunta: "¿Cuántas veces juegas a la semana?",
    ayuda: "Haz la media de los últimos meses.",
    opciones: [
      { id: "1", titulo: "Una o menos", chip: "1 vez por semana o menos" },
      { id: "2-3", titulo: "Dos o tres", chip: "2–3 veces por semana" },
      { id: "4+", titulo: "Cuatro o más", chip: "4 veces por semana o más" },
    ],
  },
  estilo: {
    nombre: "Estilo",
    pregunta: "¿Cómo sueles jugar un punto?",
    ayuda: "Elige lo que haces de verdad, no lo que te gustaría hacer.",
    opciones: [
      {
        id: "control",
        titulo: "Aguanto la bola y espero el fallo",
        detalle: "Globos, colocación y pocas prisas.",
        chip: "Juego de control",
      },
      {
        id: "mixto",
        titulo: "Un poco de todo",
        detalle: "Defiendo cuando toca y ataco cuando puedo.",
        chip: "Un poco de todo",
      },
      {
        id: "potencia",
        titulo: "Busco el remate en cuanto puedo",
        detalle: "Me gusta definir el punto en la red.",
        chip: "Juego de remate",
      },
    ],
  },
  mol: {
    nombre: "Molestias",
    pregunta: "¿Notas alguna molestia al jugar?",
    ayuda: "En codo, hombro, muñeca o espalda. Si la hay, ajustamos el peso y la dureza de la pala.",
    opciones: [
      { id: "no", titulo: "No, ninguna", chip: "Sin molestias" },
      { id: "si", titulo: "Sí, alguna", detalle: "Te preguntamos dónde y cuándo.", chip: "Con molestias" },
      { id: "nc", titulo: "Prefiero no contestar", detalle: "Seguimos sin ese dato." },
    ],
  },
  edad: {
    nombre: "Edad",
    pregunta: "¿Qué edad tiene quien va a usar la pala?",
    ayuda: "Solo necesitamos saber si hace falta una pala junior.",
    opciones: [
      { id: "adulto", titulo: "14 años o más" },
      {
        id: "junior",
        titulo: "Menos de 14 años",
        detalle: "Te enseñamos palas junior, más cortas y ligeras.",
      },
    ],
  },
  ppto: {
    nombre: "Presupuesto",
    pregunta: "¿Cuánto quieres gastar como máximo?",
    ayuda: "No te enseñaremos nada por encima de ese precio.",
    opciones: [
      { id: "100", titulo: "Hasta 100 €" },
      { id: "150", titulo: "Hasta 150 €" },
      { id: "250", titulo: "Hasta 250 €" },
      { id: "max", titulo: "Sin tope" },
    ],
  },
};

/**
 * Quien no ha jugado no puede notar molestias «al jugar», pero sí traer el brazo
 * tocado de otro deporte o del trabajo: misma pregunta, otros textos.
 */
const MOLESTIAS_SIN_HABER_JUGADO: Pick<DefPregunta, "pregunta" | "ayuda"> = {
  pregunta: "¿Tienes alguna molestia o lesión en codo, hombro, muñeca o espalda?",
  ayuda: "Aunque no hayas jugado: si ya te molesta, conviene empezar con una pala más blanda y ligera.",
};

const MOMENTOS_SIN_HABER_JUGADO: Partial<Record<Momento, string>> = {
  "Mientras juego": "Al hacer deporte o esfuerzo",
};

/** Textos de la pregunta según lo ya contestado. */
export function definicion(pregunta: Pregunta, r: Respuestas): DefPregunta {
  const base = PREGUNTAS[pregunta];
  return pregunta === "mol" && r.exp === "nunca" ? { ...base, ...MOLESTIAS_SIN_HABER_JUGADO } : base;
}

/** Texto de cada «cuándo aparece». El valor guardado no cambia; solo lo que se lee. */
export function textoMomento(momento: Momento, r: Respuestas): string {
  return (r.exp === "nunca" && MOMENTOS_SIN_HABER_JUGADO[momento]) || momento;
}

export const PRIMER_PASO: Paso = "camino";

/** Preguntas numeradas según las respuestas actuales, en orden (sin «camino»). */
export function recorrido(r: Respuestas): Paso[] {
  const pasos: Paso[] = ["exp"];
  if (r.exp !== "nunca") pasos.push("frec", "estilo");
  pasos.push("mol");
  if (r.mol === "si") pasos.push("zona");
  pasos.push("edad", "ppto");
  return pasos;
}

/** Paso que sigue a `paso` con las respuestas dadas. Tras el último, «fin». */
export function siguientePaso(paso: Paso, r: Respuestas): Paso {
  if (paso === "camino") return "exp";
  const pasos = recorrido(r);
  const i = pasos.indexOf(paso);
  return i >= 0 && i < pasos.length - 1 ? pasos[i + 1] : "fin";
}

/** Aplica una respuesta y limpia las que dejan de tener sentido. */
export function responder<P extends Pregunta>(r: Respuestas, pregunta: P, valor: Respuestas[P]): Respuestas {
  const nuevas: Respuestas = { ...r, [pregunta]: valor };
  if (pregunta === "exp" && valor === "nunca") {
    delete nuevas.frec;
    delete nuevas.estilo;
  }
  return nuevas;
}

export interface Progreso {
  /** Número de la pregunta actual (0 antes de empezar). */
  numero: number;
  total: number;
  porcentaje: number;
  /** «Antes de empezar», «Pregunta 2 de 6» o «Completado». */
  rotulo: string;
}

export function progreso(paso: Paso, r: Respuestas): Progreso {
  const numeradas = recorrido(r).filter((p) => p !== "zona");
  const total = numeradas.length;
  if (paso === "camino") return { numero: 0, total, porcentaje: 4, rotulo: "Antes de empezar" };
  if (paso === "fin") return { numero: total, total, porcentaje: 100, rotulo: "Completado" };
  const numero = numeradas.indexOf(paso === "zona" ? "mol" : paso) + 1;
  return {
    numero,
    total,
    porcentaje: Math.round((numero / total) * 100),
    rotulo: `Pregunta ${numero} de ${total}`,
  };
}

export function opcionElegida(pregunta: Pregunta, r: Respuestas): Opcion | undefined {
  return PREGUNTAS[pregunta].opciones.find((o) => o.id === r[pregunta]);
}

/** ¿Están contestadas todas las preguntas del recorrido? */
export function completo(r: Respuestas): boolean {
  if (!r.camino) return false;
  return recorrido(r).every((p) => p === "zona" || p === "fin" || r[p as Pregunta] !== undefined);
}

/** Resumen para la pantalla final del cuestionario. */
export function resumen(r: Respuestas): { clave: string; valor: string }[] {
  const filas: { clave: string; valor: string }[] = [];
  for (const p of ["camino", "exp", "frec", "estilo", "edad", "ppto"] as Pregunta[]) {
    const opcion = opcionElegida(p, r);
    if (opcion) filas.push({ clave: PREGUNTAS[p].nombre, valor: opcion.titulo });
  }
  if (r.mol) {
    filas.push({
      clave: "Molestias",
      valor: r.mol === "si" ? "Sí · no se guarda" : r.mol === "no" ? "Ninguna" : "Sin contestar",
    });
  }
  return filas;
}

/** Etiquetas cortas de las respuestas, para la cabecera de la recomendación. */
export function etiquetas(r: Respuestas): string[] {
  const lista: string[] = [];
  for (const p of ["camino", "exp", "frec", "estilo", "mol", "edad", "ppto"] as Pregunta[]) {
    const opcion = opcionElegida(p, r);
    if (!opcion) continue;
    if (p === "mol" && !opcion.chip) continue; // «prefiero no contestar» no se muestra
    lista.push(opcion.chip ?? opcion.titulo);
  }
  return lista;
}

/** Tope de gasto en euros, o Infinity si no hay. */
export function tope(r: Respuestas): number {
  return !r.ppto || r.ppto === "max" ? Infinity : Number(r.ppto);
}

// --- Perfil orientativo («Tu pala, tomando forma») ----------------------------
// Se afina con cada respuesta. Es orientativo: la recomendación final la calcula
// lib/recomendador.ts con el catálogo, con reglas parecidas pero más finas.

/** Balance en cinco niveles: 0 bajo · 1 medio-bajo · 2 medio · 3 medio-alto · 4 alto. */
export type BalanceFino = 0 | 1 | 2 | 3 | 4;
export type PuntoDulce = "grande" | "medio" | "pequeño";

export const TEXTO_BALANCE_FINO: Record<BalanceFino, string> = {
  0: "Bajo",
  1: "Medio-bajo",
  2: "Medio",
  3: "Medio-alto",
  4: "Alto",
};

export const TEXTO_CARAS: Record<Caras, string> = {
  fibra: "Fibra",
  hibrida: "Híbrida",
  carbono: "Carbono",
};

export const TEXTO_PUNTO_DULCE: Record<PuntoDulce, string> = {
  grande: "Grande",
  medio: "Medio",
  pequeño: "Pequeño",
};

export interface PerfilPala {
  forma: Forma | null;
  balance: BalanceFino | null;
  puntoDulce: PuntoDulce | null;
  peso: string | null;
  nucleo: string | null;
  caras: Caras | null;
}

const PUNTO_DE: Record<Forma, PuntoDulce> = { redonda: "grande", lagrima: "medio", diamante: "pequeño" };

/**
 * Respuestas de las preguntas ya recorridas. Al volver atrás se conservan las de después
 * (para no tener que repetirlas), pero el dibujo no las tiene en cuenta hasta volver a pasar.
 */
export function respuestasRecorridas(r: Respuestas, historial: Paso[]): Respuestas {
  const recorridas: Respuestas = {};
  for (const paso of historial) {
    if (paso !== "zona" && paso !== "fin" && r[paso] !== undefined) {
      Object.assign(recorridas, { [paso]: r[paso] });
    }
  }
  return recorridas;
}

/** Lo que se va sabiendo de la pala a medida que se contesta (`salud` solo vive en esta pestaña). */
export function perfilOrientativo(r: Respuestas, salud: Salud = SIN_SALUD): PerfilPala {
  let forma: Forma | null = null;
  let balance: BalanceFino | null = null;
  let peso: string | null = null;
  let nucleo: string | null = null;
  let caras: Caras | null = null;

  // 0. Punto de partida: quien cambia de pala suele buscar mejores materiales que la que tiene.
  if (r.camino === "primera") caras = "fibra";
  else if (r.camino === "cambio") caras = "hibrida";

  // 1. Experiencia: quien no ha jugado nunca necesita la pala que más perdona.
  if (r.exp === "nunca") {
    forma = "redonda";
    balance = 0;
    nucleo = "Blando-medio";
    peso = "355–370 g";
    caras = "fibra";
  }

  // 2. Frecuencia: cuánto uso tiene que aguantar (material de las caras).
  if (r.frec === "1") caras = "fibra";
  else if (r.frec === "2-3") caras = "hibrida";
  else if (r.frec === "4+") caras = "carbono";

  // 3. Estilo: forma y balance según la experiencia y, con ellos, núcleo y peso.
  //    Con menos de 6 meses nunca un diamante: la técnica todavía se está formando.
  const novato = r.exp === "lt6";
  const avanzado = r.exp === "gt2";
  if (r.estilo === "control") {
    forma = "redonda";
    balance = avanzado ? 1 : 0;
  } else if (r.estilo === "mixto") {
    forma = "lagrima";
    balance = novato ? 1 : 2;
  } else if (r.estilo === "potencia") {
    forma = avanzado ? "diamante" : "lagrima";
    balance = avanzado ? 4 : novato ? 2 : 3;
  }
  if (r.estilo) {
    nucleo = forma === "diamante" ? "Medio-duro" : novato ? "Blando-medio" : "Medio";
    peso = forma === "diamante" ? "365–375 g" : "355–370 g";
  }

  // 4. Molestias: más blanda, más ligera, nunca un diamante y como mucho caras híbridas
  //    (el carbono es más rígido y transmite más vibración). El detalle afina más.
  if (r.mol === "si") {
    nucleo = "Blando";
    peso = "345–360 g";
    if (caras === "carbono") caras = "hibrida";
    if (forma === "diamante") forma = "lagrima";
    if (balance !== null) balance = Math.min(balance, 2) as BalanceFino;
    if ((salud.zona === "Codo" || salud.zona === "Muñeca") && balance !== null) {
      balance = Math.max(0, balance - 1) as BalanceFino; // menos palanca sobre el brazo
    }
    if (salud.zona === "Hombro" || salud.zona === "Espalda") peso = "340–355 g";
    if (salud.momento === "Casi siempre") nucleo = "Muy blando";
  }

  // 5. Edad: una junior manda sobre todo lo anterior.
  if (r.edad === "junior") {
    forma = "redonda";
    balance = 0;
    peso = "300–330 g";
    if (nucleo !== "Muy blando") nucleo = "Blando";
    caras = "fibra";
  }

  // 6. Presupuesto: limita los materiales.
  if (r.ppto === "100") caras = "fibra";
  else if (r.ppto === "150" && caras === "carbono") caras = "hibrida";

  return { forma, balance, puntoDulce: forma ? PUNTO_DE[forma] : null, peso, nucleo, caras };
}

// --- Persistencia -------------------------------------------------------------
// SALUD: la respuesta de molestias y su detalle no salen de sessionStorage.
// El progreso guardado (localStorage) y el historial no los incluyen nunca.

const CLAVE_PROGRESO = "palaideal:encuesta";
const CLAVE_FINAL = "palaideal:respuestas";

/** Quita el dato de salud de unas respuestas. */
export function sinSalud(r: Respuestas): Respuestas {
  const copia = { ...r };
  delete copia.mol;
  return copia;
}

export interface Reanudacion {
  respuestas: Respuestas;
  paso: Paso;
  /** Pasos ya recorridos, para el botón «Atrás». */
  historial: Paso[];
}

/** Guarda lo contestado hasta ahora (sin molestias) para poder retomarlo. */
export function guardarProgreso(r: Respuestas): void {
  try {
    localStorage.setItem(CLAVE_PROGRESO, JSON.stringify(sinSalud(r)));
  } catch {
    /* modo privado o almacenamiento bloqueado: el cuestionario sigue funcionando */
  }
}

export function borrarProgreso(): void {
  try {
    localStorage.removeItem(CLAVE_PROGRESO);
  } catch {
    /* ignorar */
  }
}

/** Reconstruye el punto en el que seguir a partir de unas respuestas guardadas. */
export function reanudar(r: Respuestas): Reanudacion {
  const orden: Paso[] = ["camino", ...recorrido(r)];
  const pendiente = orden.findIndex((p) => p === "zona" || r[p as Pregunta] === undefined);
  const i = pendiente === -1 ? orden.length - 1 : pendiente;
  return { respuestas: r, paso: orden[i], historial: orden.slice(0, i) };
}

/** Cuestionario a medias guardado en este navegador, si lo hay. */
export function cargarProgreso(): Reanudacion | null {
  try {
    const crudo = localStorage.getItem(CLAVE_PROGRESO);
    if (!crudo) return null;
    const r = sinSalud(JSON.parse(crudo) as Respuestas);
    // Solo merece la pena retomar si ya se contestó algo más que el punto de partida.
    return r.camino && r.exp ? reanudar(r) : null;
  } catch {
    return null;
  }
}

/** Respuestas del último cuestionario terminado en esta pestaña. */
export interface RespuestasFinales {
  /** Identificador de la recomendación (también en el historial). */
  id: string;
  fecha: string;
  respuestas: Respuestas;
  salud: Salud;
}

export function guardarFinal(r: Respuestas, salud: Salud): RespuestasFinales {
  const final: RespuestasFinales = {
    id: Date.now().toString(36),
    fecha: new Date().toISOString(),
    respuestas: r,
    salud: r.mol === "si" ? salud : SIN_SALUD,
  };
  try {
    sessionStorage.setItem(CLAVE_FINAL, JSON.stringify(final));
  } catch {
    /* ignorar */
  }
  return final;
}

export function leerFinal(): RespuestasFinales | null {
  try {
    const crudo = sessionStorage.getItem(CLAVE_FINAL);
    return crudo ? (JSON.parse(crudo) as RespuestasFinales) : null;
  } catch {
    return null;
  }
}
