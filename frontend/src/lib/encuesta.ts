/**
 * Flujo de la encuesta (diagrama "Flujo de la encuesta" en Figma).
 *
 *   1. Experiencia ─┬─ ≥ 6 meses ─> 2. Frecuencia -> 3. Estilo ─┐
 *                   └─ < 6 meses ───────────────────────────────┴─> 4. Molestias
 *   4. Molestias ─┬─ sí ─> Zona y momento ─┐
 *                 └─ no ───────────────────┴─> 5. Edad -> 6. Presupuesto -> fin
 */

export type Camino = "primera" | "cambiar";

export type Paso =
  | "experiencia"
  | "frecuencia"
  | "estilo"
  | "molestias"
  | "zona"
  | "edad"
  | "presupuesto";

export interface Respuestas {
  experiencia_meses?: number;
  frecuencia_semanal?: number;
  estilo?: "defensivo" | "polivalente" | "ofensivo";
  molestias?: boolean;
  zona_molestia?: "codo" | "hombro" | "muneca";
  momento_molestia?: "durante" | "despues";
  junior?: boolean;
  presupuesto_max?: number;
}

export interface EstadoEncuesta {
  camino: Camino;
  paso: Paso;
  respuestas: Respuestas;
}

export const PRIMER_PASO: Paso = "experiencia";
export const MESES_JUGADOR_HABITUAL = 6;

/** Devuelve el paso siguiente, o null si la encuesta ha terminado. */
export function siguientePaso(paso: Paso, r: Respuestas): Paso | null {
  switch (paso) {
    case "experiencia":
      return (r.experiencia_meses ?? 0) >= MESES_JUGADOR_HABITUAL ? "frecuencia" : "molestias";
    case "frecuencia":
      return "estilo";
    case "estilo":
      return "molestias";
    case "molestias":
      return r.molestias ? "zona" : "edad";
    case "zona":
      return "edad";
    case "edad":
      return "presupuesto";
    case "presupuesto":
      return null;
  }
}

/** Recorrido completo según las respuestas actuales (para la barra de progreso). */
export function recorrido(r: Respuestas): Paso[] {
  const pasos: Paso[] = [];
  for (let p: Paso | null = PRIMER_PASO; p; p = siguientePaso(p, r)) pasos.push(p);
  return pasos;
}

// --- Persistencia local ("¿Respuestas guardadas?" -> "Retomar encuesta") ------

const CLAVE = "encuesta:v1";

export function cargarProgreso(): EstadoEncuesta | null {
  try {
    const crudo = localStorage.getItem(CLAVE);
    return crudo ? (JSON.parse(crudo) as EstadoEncuesta) : null;
  } catch {
    return null;
  }
}

export function guardarProgreso(estado: EstadoEncuesta): void {
  try {
    localStorage.setItem(CLAVE, JSON.stringify(estado));
  } catch {
    /* modo privado o almacenamiento bloqueado: la encuesta sigue funcionando */
  }
}

export function borrarProgreso(): void {
  try {
    localStorage.removeItem(CLAVE);
  } catch {
    /* ignorar */
  }
}

/** Perfil final que se envía a POST /recomendaciones. */
export function aPerfil(estado: EstadoEncuesta) {
  return { camino: estado.camino, ...estado.respuestas };
}

const CLAVE_PERFIL = "encuesta:perfil";

export function guardarPerfilFinal(estado: EstadoEncuesta): void {
  try {
    sessionStorage.setItem(CLAVE_PERFIL, JSON.stringify(aPerfil(estado)));
  } catch {
    /* ignorar */
  }
}

export function leerPerfilFinal(): ReturnType<typeof aPerfil> | null {
  try {
    const crudo = sessionStorage.getItem(CLAVE_PERFIL);
    return crudo ? JSON.parse(crudo) : null;
  } catch {
    return null;
  }
}
