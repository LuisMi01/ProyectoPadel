/** Cliente mínimo de la API FastAPI. La sesión viaja en cookie httpOnly. */

const BASE = import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000";

export class ErrorApi extends Error {
  constructor(
    public estado: number,
    mensaje: string,
  ) {
    super(mensaje);
  }
}

export async function api<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${ruta}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}));
    throw new ErrorApi(res.status, cuerpo.detail ?? res.statusText);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const post = <T>(ruta: string, datos: unknown) =>
  api<T>(ruta, { method: "POST", body: JSON.stringify(datos) });
