/**
 * Lo que la página de recomendación hace con la API, si la hay:
 *
 * 1. Registrar la recomendación que se acaba de enseñar (POST /recomendaciones): las respuestas
 *    SIN el dato de molestias y los ids de las palas, en orden. La API no la recalcula.
 * 2. Pedir la explicación según la IA la escribe (GET /recomendaciones/{id}/explicacion/flujo).
 *
 * Si la API no está o falla, la página sigue igual que sin ella.
 */
import { API_URL, hayApi, post } from "@/lib/api";
import type { Respuestas } from "@/lib/encuesta";

// sessionStorage: id de la API de cada recomendación ya registrada en esta pestaña, para no
// registrarla otra vez al recargar la página.
const CLAVE = "palaideal:rec-servidor";

function registradas(): Record<string, number> {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE) ?? "{}");
  } catch {
    return {};
  }
}

/** Devuelve el id de la recomendación en la API, o null si no hay API o ha fallado. */
export async function registrarEnServidor(
  idLocal: string,
  respuestas: Respuestas,
  palas: number[],
): Promise<number | null> {
  if (!hayApi) return null;
  const ya = registradas()[idLocal];
  if (ya) return ya;

  // SALUD: se copian una a una las respuestas que se envían; `mol` no sale nunca del navegador.
  const { camino, exp, frec, estilo, edad, ppto } = respuestas;
  try {
    const { id } = await post<{ id: number }>("/recomendaciones", {
      camino,
      exp,
      frec,
      estilo,
      edad,
      ppto,
      palas,
    });
    try {
      sessionStorage.setItem(CLAVE, JSON.stringify({ ...registradas(), [idLocal]: id }));
    } catch {
      // Sin sessionStorage solo se pierde evitar el duplicado al recargar.
    }
    return id;
  } catch {
    return null;
  }
}

/** De dónde sale el texto: de la IA (ahora o antes, en caché) o de la plantilla. */
export type OrigenExplicacion = "ia" | "cache" | "plantilla" | "sin_ia" | "tope";

export interface EventosExplicacion {
  /** Texto recibido hasta ahora, mientras la IA escribe. */
  alEscribir: (parcial: string) => void;
  /** Texto definitivo (sustituye a lo recibido) y su origen. */
  alTerminar: (texto: string, origen: OrigenExplicacion) => void;
}

/** Lee la explicación en flujo (Server-Sent Events). Rechaza si la API falla. */
export async function explicacionEnFlujo(
  recomendacion: number,
  { alEscribir, alTerminar }: EventosExplicacion,
  senal: AbortSignal,
): Promise<void> {
  const respuesta = await fetch(`${API_URL}/recomendaciones/${recomendacion}/explicacion/flujo`, {
    credentials: "include",
    signal: senal,
  });
  if (!respuesta.ok || !respuesta.body) throw new Error(`Explicación: HTTP ${respuesta.status}`);

  const lector = respuesta.body.pipeThrough(new TextDecoderStream()).getReader();
  let pendiente = "";
  let parcial = "";
  for (;;) {
    const { value, done } = await lector.read();
    if (done) break;
    pendiente += value;
    // Cada evento acaba en una línea en blanco: «event: …\ndata: {…}\n\n».
    let corte: number;
    while ((corte = pendiente.indexOf("\n\n")) >= 0) {
      const bloque = pendiente.slice(0, corte);
      pendiente = pendiente.slice(corte + 2);
      const evento = /^event: (.+)$/m.exec(bloque)?.[1];
      const datos = JSON.parse(/^data: (.+)$/m.exec(bloque)?.[1] ?? "{}");
      if (evento === "texto") {
        parcial += datos.t;
        alEscribir(parcial);
      } else if (evento === "fin") {
        alTerminar(datos.texto, datos.origen);
        return;
      }
    }
  }
  throw new Error("Explicación: el flujo terminó sin el evento final");
}
