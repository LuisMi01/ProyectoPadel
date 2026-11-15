/**
 * Lo que el usuario guarda: palas, avisos de precio, historial y sesión.
 *
 * Funciona primero en el navegador (localStorage), para que guardar una pala o
 * crear un aviso no exija registrarse. El acceso por correo sí usa la API
 * (/acceso/*, /perfil).
 *
 * PENDIENTE (backend): cuando el catálogo exista en la base de datos, volcar
 * aquí las palas guardadas y los avisos a /palas-guardadas y /alertas al
 * iniciar sesión, para que vivan en la cuenta y no solo en este navegador.
 */
import { ErrorApi, api, borrar, post } from "@/lib/api";
import { type Respuestas, sinSalud } from "@/lib/encuesta";

const CLAVES = {
  guardadas: "palaideal:guardadas",
  alertas: "palaideal:alertas",
  historial: "palaideal:historial",
  sesion: "palaideal:sesion",
} as const;

const EVENTO_CAMBIO = "palaideal:cambio";
const MAX_HISTORIAL = 20;

function leer<T>(clave: string, defecto: T): T {
  try {
    const crudo = localStorage.getItem(clave);
    return crudo ? (JSON.parse(crudo) as T) : defecto;
  } catch {
    return defecto;
  }
}

function escribir(clave: string, valor: unknown): void {
  try {
    if (valor === null) localStorage.removeItem(clave);
    else localStorage.setItem(clave, JSON.stringify(valor));
  } catch {
    /* modo privado o almacenamiento lleno: no se puede guardar */
  }
  window.dispatchEvent(new Event(EVENTO_CAMBIO));
}

/** Avisa cuando cambia algo guardado (en esta pestaña o en otra). Devuelve cómo dejar de escuchar. */
export function suscribir(alCambiar: () => void): () => void {
  window.addEventListener(EVENTO_CAMBIO, alCambiar);
  window.addEventListener("storage", alCambiar);
  return () => {
    window.removeEventListener(EVENTO_CAMBIO, alCambiar);
    window.removeEventListener("storage", alCambiar);
  };
}

// --- Palas guardadas -----------------------------------------------------------

export interface PalaGuardada {
  slug: string;
  fecha: string;
}

export function palasGuardadas(): PalaGuardada[] {
  return leer<PalaGuardada[]>(CLAVES.guardadas, []);
}

export function estaGuardada(slug: string): boolean {
  return palasGuardadas().some((p) => p.slug === slug);
}

/** Guarda la pala o la quita si ya estaba. Devuelve si queda guardada. */
export function alternarGuardada(slug: string): boolean {
  const lista = palasGuardadas();
  const estaba = lista.some((p) => p.slug === slug);
  escribir(
    CLAVES.guardadas,
    estaba ? lista.filter((p) => p.slug !== slug) : [{ slug, fecha: new Date().toISOString() }, ...lista],
  );
  return !estaba;
}

// --- Avisos de precio ---------------------------------------------------------

export interface Alerta {
  id: string;
  slug: string;
  /** Precio en euros por debajo del cual avisar. */
  objetivo: number;
  fecha: string;
}

export function alertas(): Alerta[] {
  return leer<Alerta[]>(CLAVES.alertas, []);
}

export function alertaDe(slug: string): Alerta | undefined {
  return alertas().find((a) => a.slug === slug);
}

/** Crea el aviso de una pala. Si ya tenía uno, lo sustituye. */
export function crearAlerta(slug: string, objetivo: number): Alerta {
  const alerta: Alerta = { id: Date.now().toString(36), slug, objetivo, fecha: new Date().toISOString() };
  escribir(CLAVES.alertas, [alerta, ...alertas().filter((a) => a.slug !== slug)]);
  return alerta;
}

export function eliminarAlerta(id: string): void {
  escribir(
    CLAVES.alertas,
    alertas().filter((a) => a.id !== id),
  );
}

// --- Historial de recomendaciones --------------------------------------------

export type Voto = "si" | "no";

export interface EntradaHistorial {
  id: string;
  fecha: string;
  /** Respuestas del cuestionario, siempre sin el dato de molestias. */
  respuestas: Respuestas;
  /** Slugs de las palas recomendadas, en orden. */
  palas: string[];
  voto?: Voto;
}

export function historial(): EntradaHistorial[] {
  return leer<EntradaHistorial[]>(CLAVES.historial, []);
}

export function entradaHistorial(id: string): EntradaHistorial | undefined {
  return historial().find((e) => e.id === id);
}

/** Añade la recomendación al historial (o la actualiza si ya estaba). */
export function registrarRecomendacion(entrada: EntradaHistorial): void {
  const limpia: EntradaHistorial = { ...entrada, respuestas: sinSalud(entrada.respuestas) };
  const previa = entradaHistorial(entrada.id);
  if (previa) limpia.voto = previa.voto;
  const resto = historial().filter((e) => e.id !== entrada.id);
  escribir(CLAVES.historial, [limpia, ...resto].slice(0, MAX_HISTORIAL));
}

export function votar(id: string, voto: Voto): void {
  escribir(
    CLAVES.historial,
    historial().map((e) => (e.id === id ? { ...e, voto } : e)),
  );
}

export function eliminarDelHistorial(id: string): void {
  escribir(
    CLAVES.historial,
    historial().filter((e) => e.id !== id),
  );
}

/** Borra todo lo guardado en este navegador (no cierra la sesión). */
export function borrarDatosLocales(): void {
  escribir(CLAVES.guardadas, null);
  escribir(CLAVES.alertas, null);
  escribir(CLAVES.historial, null);
}

// --- Sesión (API) -------------------------------------------------------------

export interface Sesion {
  email: string;
  /** Fecha de alta de la cuenta (ISO). */
  desde: string | null;
}

interface PerfilApi {
  id: number;
  email: string;
  creado_en: string;
}

export type EstadoSesion =
  | { tipo: "activa"; sesion: Sesion }
  | { tipo: "invitado" }
  /** No se ha podido preguntar a la API: se muestra lo último que se sabía. */
  | { tipo: "sin-conexion"; sesion: Sesion | null };

/** Última sesión conocida, sin consultar a la API (para pintar la cabecera al instante). */
export function sesionRecordada(): Sesion | null {
  return leer<Sesion | null>(CLAVES.sesion, null);
}

function recordar(sesion: Sesion | null): void {
  if (JSON.stringify(sesionRecordada()) !== JSON.stringify(sesion)) escribir(CLAVES.sesion, sesion);
}

/** Pregunta a la API si hay sesión y actualiza lo recordado. */
export async function comprobarSesion(): Promise<EstadoSesion> {
  try {
    const perfil = await api<PerfilApi>("/perfil");
    const sesion: Sesion = { email: perfil.email, desde: perfil.creado_en };
    recordar(sesion);
    return { tipo: "activa", sesion };
  } catch (e) {
    if (e instanceof ErrorApi && e.estado === 401) {
      recordar(null);
      return { tipo: "invitado" };
    }
    return { tipo: "sin-conexion", sesion: sesionRecordada() };
  }
}

/** Pide el enlace de acceso: registro e inicio de sesión son el mismo paso. */
export function pedirEnlace(email: string): Promise<void> {
  return post<void>("/acceso/enlace", { email });
}

/** Canjea el token del enlace por una sesión y devuelve el perfil. */
export async function verificarEnlace(token: string): Promise<Sesion | null> {
  await post<void>("/acceso/verificar", { token });
  const estado = await comprobarSesion();
  return estado.tipo === "activa" ? estado.sesion : null;
}

export async function cerrarSesion(): Promise<void> {
  try {
    await post<void>("/acceso/cerrar");
  } finally {
    recordar(null);
  }
}

/** Borra la cuenta en el servidor y lo guardado en este navegador. */
export async function borrarCuenta(): Promise<void> {
  await borrar<void>("/perfil");
  recordar(null);
  borrarDatosLocales();
}
