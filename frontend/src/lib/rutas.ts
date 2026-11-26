/**
 * Mapa único de rutas de la web. Usa siempre estas constantes para enlazar
 * entre páginas: si una URL cambia, se cambia solo aquí.
 */
export type FiltroForma = "redonda" | "lagrima" | "diamante" | "junior";

/** Desde dónde se sale a la tienda (lo registra la API con el clic). */
export type OrigenSalida = "recomendacion" | "ficha" | "catalogo" | "cuenta";

export interface Salida {
  origen: OrigenSalida;
  /** Puesto de la pala en la recomendación (1 = la mejor). */
  posicion?: number;
  /** Id de la recomendación guardada en la API. */
  recomendacion?: number | null;
}

function salidaATienda(ofertaId: number, { origen, posicion, recomendacion }: Salida): string {
  const parametros = new URLSearchParams({ origen });
  if (posicion) parametros.set("pos", String(posicion));
  if (recomendacion) parametros.set("rec", String(recomendacion));
  return `/ir/${ofertaId}/?${parametros}`;
}

export const rutas = {
  inicio: "/",
  comoFunciona: "/#como-funciona",
  transparencia: "/#transparencia",

  encuesta: "/encuesta/",
  /** Entra al cuestionario con el punto de partida ya elegido. */
  encuestaCamino: (camino: "primera" | "cambio") => `/encuesta/?camino=${camino}`,
  /** Reabre el cuestionario con las últimas respuestas para cambiarlas. */
  encuestaEditar: "/encuesta/?editar=1",

  recomendacion: "/recomendacion/",
  /** Vuelve a mostrar una recomendación guardada en el historial. */
  recomendacionGuardada: (id: string) => `/recomendacion/?h=${encodeURIComponent(id)}`,

  palas: "/palas/",
  palasPorForma: (forma: FiltroForma) => `/palas/?forma=${forma}`,
  pala: (slug: string) => `/palas/${slug}/`,
  palaPrecios: (slug: string) => `/palas/${slug}/#precios`,
  /** Salida a tienda: página intermedia que pasa por la API (registra el clic) y redirige. */
  tienda: salidaATienda,

  guias: "/guias/",
  guia: (slug: string) => `/guias/${slug}/`,

  comoGanamosDinero: "/como-ganamos-dinero/",
  afiliacion: "/legal/afiliacion/",
  avisoLegal: "/legal/aviso-legal/",
  /** El correo de contacto está con los datos del titular. */
  contacto: "/legal/aviso-legal/",
  privacidad: "/legal/privacidad/",
  cookies: "/legal/cookies/",

  acceso: "/acceso/",
  accesoVerificar: "/acceso/verificar/",
  cuenta: "/cuenta/",
  palasGuardadas: "/cuenta/palas-guardadas/",
  alertas: "/cuenta/alertas/",
  historial: "/cuenta/historial/",
} as const;

export type SeccionNav = "cuestionario" | "palas" | "guias";

/** Enlaces de la navegación principal (cabecera). «Cómo ganamos dinero» va en el pie, en Transparencia. */
export const navegacion: { id: SeccionNav; texto: string; href: string }[] = [
  { id: "cuestionario", texto: "Cuestionario", href: rutas.encuesta },
  { id: "palas", texto: "Palas", href: rutas.palas },
  { id: "guias", texto: "Guías", href: rutas.guias },
];

/** Sub-navegación del área de cuenta. */
export const navegacionCuenta = [
  { texto: "Perfil", href: rutas.cuenta },
  { texto: "Palas guardadas", href: rutas.palasGuardadas },
  { texto: "Avisos de precio", href: rutas.alertas },
  { texto: "Historial", href: rutas.historial },
] as const;

/** Columnas del pie completo. */
export const pieColumnas = [
  {
    titulo: "Producto",
    enlaces: [
      { texto: "Cuestionario", href: rutas.encuesta },
      { texto: "Palas", href: rutas.palas },
      { texto: "Guías", href: rutas.guias },
    ],
  },
  {
    titulo: "Tu cuenta",
    enlaces: [
      { texto: "Acceder", href: rutas.acceso },
      { texto: "Palas guardadas", href: rutas.palasGuardadas },
    ],
  },
  {
    titulo: "Transparencia",
    enlaces: [
      { texto: "Cómo ganamos dinero", href: rutas.comoGanamosDinero },
      { texto: "Política de afiliación", href: rutas.afiliacion },
    ],
  },
  {
    titulo: "Legal",
    enlaces: [
      { texto: "Aviso legal", href: rutas.avisoLegal },
      { texto: "Privacidad", href: rutas.privacidad },
      { texto: "Cookies", href: rutas.cookies },
      { texto: "Contacto", href: rutas.contacto },
    ],
  },
] as const;

/** Enlaces del pie compacto. */
export const pieLegal = [
  { texto: "Política de afiliación", href: rutas.afiliacion },
  { texto: "Privacidad", href: rutas.privacidad },
  { texto: "Cookies", href: rutas.cookies },
  { texto: "Aviso legal", href: rutas.avisoLegal },
] as const;
