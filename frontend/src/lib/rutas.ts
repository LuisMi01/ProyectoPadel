/**
 * Mapa único de rutas de la web. Usa siempre estas constantes para enlazar
 * entre páginas: si una URL cambia, se cambia solo aquí.
 */
export const rutas = {
  inicio: "/",
  encuesta: "/encuesta/",
  encuestaCamino: (camino: "primera" | "cambiar") => `/encuesta/?camino=${camino}`,
  recomendacion: "/recomendacion/",
  palas: "/palas/",
  pala: (slug: string) => `/palas/${slug}/`,
  guias: "/guias/",
  guia: (slug: string) => `/guias/${slug}/`,
  acceso: "/acceso/",
  accesoVerificar: "/acceso/verificar/",
  cuenta: "/cuenta/",
  palasGuardadas: "/cuenta/palas-guardadas/",
  alertas: "/cuenta/alertas/",
  historial: "/cuenta/historial/",
} as const;

/** Enlaces de la navegación principal (cabecera). */
export const navegacion = [
  { texto: "Encuesta", href: rutas.encuesta },
  { texto: "Palas", href: rutas.palas },
  { texto: "Guías", href: rutas.guias },
  { texto: "Mi cuenta", href: rutas.cuenta },
] as const;

/** Sub-navegación del área de cuenta. */
export const navegacionCuenta = [
  { texto: "Perfil", href: rutas.cuenta },
  { texto: "Palas guardadas", href: rutas.palasGuardadas },
  { texto: "Alertas de precio", href: rutas.alertas },
  { texto: "Historial", href: rutas.historial },
] as const;
