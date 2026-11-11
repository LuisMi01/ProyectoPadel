/**
 * Datos de ejemplo mientras no exista GET /internas/catalogo.
 * Cuando exista, las páginas de ficha leerán el catálogo exportado en build.
 */
export interface PalaResumen {
  slug: string;
  marca: string;
  nombre: string;
  anio: number;
  forma: "redonda" | "lágrima" | "diamante";
}

export const palasDeEjemplo: PalaResumen[] = [
  { slug: "ejemplo-control-2026", marca: "Marca A", nombre: "Control", anio: 2026, forma: "redonda" },
  { slug: "ejemplo-hibrida-2026", marca: "Marca B", nombre: "Híbrida", anio: 2026, forma: "lágrima" },
  { slug: "ejemplo-potencia-2026", marca: "Marca C", nombre: "Potencia", anio: 2026, forma: "diamante" },
];

export interface Guia {
  slug: string;
  titulo: string;
  resumen: string;
}

export const guiasDeEjemplo: Guia[] = [
  {
    slug: "como-elegir-tu-primera-pala",
    titulo: "Cómo elegir tu primera pala",
    resumen: "Forma, peso y balance explicados sin jerga.",
  },
  {
    slug: "forma-de-la-pala",
    titulo: "Redonda, lágrima o diamante",
    resumen: "Qué cambia en el juego según la forma.",
  },
];
