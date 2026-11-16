/**
 * Flujo del cuestionario (máquina de estados pura, sin DOM).
 *
 *   Antes de empezar ─> 1. Experiencia ─┬─ ≥ 6 meses ─> 2. Frecuencia -> 3. Estilo ─┐
 *                                       └─ < 6 meses ───────────────────────────────┴─> Molestias
 *   Molestias ─┬─ sí ─> Zona y momento (con consentimiento) ─┐
 *              └─ no / prefiero no contestar ────────────────┴─> Edad -> Presupuesto -> fin
 *
 * Las molestias son un dato de salud: sirven para calcular la recomendación y
 * no se guardan con el progreso ni en el historial (ver SALUD más abajo).
 */
import type { Balance, Forma } from "@/lib/catalogo";

export type Pregunta = "camino" | "exp" | "frec" | "estilo" | "mol" | "edad" | "ppto";
export type Paso = Pregunta | "zona" | "fin";

export interface Respuestas {
  camino?: "primera" | "cambio";
  exp?: "lt6" | "m6a2" | "gt2";
  frec?: "1" | "2-3" | "4+";
  estilo?: "control" | "mixto" | "potencia";
  mol?: "no" | "si" | "nc";
  edad?: "adulto" | "junior";
  ppto?: "80" | "150" | "250" | "max";
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
        id: "lt6",
        titulo: "Menos de 6 meses",
        detalle: "Nos saltamos frecuencia y estilo: todavía se están formando.",
      },
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
      { id: "80", titulo: "Hasta 80 €" },
      { id: "150", titulo: "Hasta 150 €" },
      { id: "250", titulo: "Hasta 250 €" },
      { id: "max", titulo: "Sin tope" },
    ],
  },
};

export const PRIMER_PASO: Paso = "camino";

/** Preguntas numeradas según las respuestas actuales, en orden (sin «camino»). */
export function recorrido(r: Respuestas): Paso[] {
  const pasos: Paso[] = ["exp"];
  if (r.exp !== "lt6") pasos.push("frec", "estilo");
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
  if (pregunta === "exp" && valor === "lt6") {
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

export interface PerfilPala {
  forma: Forma | null;
  balance: Balance | null;
  peso: string | null;
  nucleo: string | null;
}

/** Lo que se va sabiendo de la pala a medida que se contesta. */
export function perfilOrientativo(r: Respuestas): PerfilPala {
  let forma: Forma | null = null;
  let balance: Balance | null = null;
  let peso: string | null = null;
  let nucleo: string | null = null;

  if (r.exp === "lt6" || r.estilo === "control") {
    forma = "redonda";
    balance = "bajo";
  } else if (r.estilo === "mixto") {
    forma = "lagrima";
    balance = "medio";
  } else if (r.estilo === "potencia") {
    const avanzado = r.exp === "gt2";
    forma = avanzado ? "diamante" : "lagrima";
    balance = avanzado ? "alto" : "medio";
  }

  if (r.mol === "si") {
    nucleo = "Blando";
    peso = "345–360 g";
    if (forma === "diamante") {
      forma = "lagrima";
      balance = "medio";
    }
  } else if (r.mol) {
    nucleo = forma === "diamante" ? "Medio-duro" : "Medio";
    peso = forma === "diamante" ? "365–375 g" : "355–370 g";
  }

  if (r.edad === "junior") {
    forma = "redonda";
    balance = "bajo";
    peso = "300–330 g";
  }

  return { forma, balance, peso, nucleo };
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
