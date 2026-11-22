/**
 * Cliente mínimo de la API FastAPI. La sesión viaja en cookie httpOnly.
 *
 * PUBLIC_API_URL indica dónde está la API. En desarrollo, si no se define, se
 * usa http://localhost:8000. En producción, si no se define, la API se da por
 * no disponible y la web funciona solo con lo que guarda el navegador.
 */

const configurada = (import.meta.env.PUBLIC_API_URL as string | undefined)?.trim().replace(/\/+$/, "");

export const API_URL: string | null = configurada || (import.meta.env.DEV ? "http://localhost:8000" : null);

/** false cuando la web se ha desplegado sin backend. */
export const hayApi = API_URL !== null;

const ESPERA_MS = 20_000;

export class ErrorApi extends Error {
  constructor(
    /** Código HTTP, o 0 si no hubo respuesta (sin conexión, sin API o tiempo agotado). */
    public estado: number,
    mensaje: string,
  ) {
    super(mensaje);
  }

  get sinConexion(): boolean {
    return this.estado === 0;
  }
}

export async function api<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  if (!API_URL) throw new ErrorApi(0, "API no configurada");

  let res: Response;
  try {
    res = await fetch(`${API_URL}${ruta}`, {
      ...init,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...init.headers },
      signal: AbortSignal.timeout(ESPERA_MS),
    });
  } catch {
    throw new ErrorApi(0, "Sin conexión con el servidor");
  }

  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}));
    throw new ErrorApi(res.status, typeof cuerpo.detail === "string" ? cuerpo.detail : res.statusText);
  }
  // 202 y 204 pueden llegar sin cuerpo o con «null».
  const texto = await res.text();
  return (texto ? JSON.parse(texto) : undefined) as T;
}

export const post = <T>(ruta: string, datos?: unknown) =>
  api<T>(ruta, { method: "POST", body: datos === undefined ? undefined : JSON.stringify(datos) });

export const borrar = <T>(ruta: string) => api<T>(ruta, { method: "DELETE" });
