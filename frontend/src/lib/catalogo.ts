/**
 * Tipos y utilidades del catálogo. Los datos están en data/catalogo.ts
 * (de ejemplo mientras no exista GET /internas/catalogo en el backend).
 */

export type Forma = "redonda" | "lagrima" | "diamante";
export type Balance = "bajo" | "medio" | "alto";
export type Caras = "fibra" | "hibrida" | "carbono";
export type Disponibilidad = "stock" | "ultimas" | "agotada";
/** 1 iniciación · 2 medio · 3 avanzado */
export type Nivel = 1 | 2 | 3;

export interface Tienda {
  id: string;
  nombre: string;
}

export interface Oferta {
  /** Identificador de la oferta: es el que usa GET /tienda/{oferta_id} en la API. */
  id: number;
  tienda: string;
  precio: number;
  disponibilidad: Disponibilidad;
  /** URL del producto en la tienda. null en el catálogo de ejemplo. */
  url: string | null;
}

/** Precio más bajo entre tiendas vigente desde hace `hace` días. */
export interface PuntoPrecio {
  hace: number;
  precio: number;
}

export interface Pala {
  /** modelo_id en la API. */
  id: number;
  slug: string;
  marca: string;
  nombre: string;
  temporada: number;
  junior: boolean;

  forma: Forma;
  balance: Balance;
  /** Peso nominal y rango en gramos. */
  peso: number;
  pesoMin: number;
  pesoMax: number;
  /** Dureza del núcleo: 1 muy blando … 5 duro. */
  dureza: 1 | 2 | 3 | 4 | 5;
  nucleo: string;
  caras: Caras;
  carasTexto: string;
  /** Gama de materiales: 1 básica · 2 media · 3 alta. */
  gama: 1 | 2 | 3;
  /** Rango de nivel de juego para el que está pensada. */
  nivel: [Nivel, Nivel];

  /** Valoraciones de 1 a 5. */
  control: number;
  tolerancia: number;
  potencia: number;

  resumen: string;
  paraTi: string[];
  mejorOtra: string[];

  ofertas: Oferta[];
  /** Histórico de 90 días, del más antiguo al más reciente. */
  historico: PuntoPrecio[];
}

// --- Textos ------------------------------------------------------------------

export const FORMAS: Forma[] = ["redonda", "lagrima", "diamante"];
export const BALANCES: Balance[] = ["bajo", "medio", "alto"];

export const textoForma: Record<Forma, string> = {
  redonda: "Redonda",
  lagrima: "Lágrima",
  diamante: "Diamante",
};

/** Etiqueta de la forma en plural, para listados y migas de pan. */
export const textoFormaPlural: Record<Forma, string> = {
  redonda: "Redondas",
  lagrima: "De lágrima",
  diamante: "De diamante",
};

/** Carácter de juego que da cada forma. */
export const textoCaracter: Record<Forma, string> = {
  redonda: "Control",
  lagrima: "Polivalente",
  diamante: "Potencia",
};

export const textoBalance: Record<Balance, string> = {
  bajo: "Bajo",
  medio: "Medio",
  alto: "Alto",
};

const NIVELES: Record<Nivel, string> = { 1: "Iniciación", 2: "Medio", 3: "Avanzado" };

export function textoNivel([min, max]: [Nivel, Nivel]): string {
  return min === max ? NIVELES[min] : `${NIVELES[min]} – ${NIVELES[max].toLowerCase()}`;
}

const DUREZAS = ["", "muy blando", "blando", "medio", "medio-duro", "duro"];

/** «Núcleo blando», «Núcleo medio-duro»… a partir de la dureza. */
export function textoNucleo(pala: Pala): string {
  return `Núcleo ${DUREZAS[pala.dureza]}`;
}

export function textoPeso(pala: Pala): string {
  return `${pala.pesoMin}–${pala.pesoMax} g`;
}

export const textoDisponibilidad: Record<Disponibilidad, string> = {
  stock: "En stock",
  ultimas: "Últimas unidades",
  agotada: "Agotada",
};

/** Nombre de la forma dentro de una frase: «forma redonda», «forma de lágrima». */
export function formaEnFrase(forma: Forma): string {
  return forma === "redonda" ? "redonda" : forma === "lagrima" ? "de lágrima" : "de diamante";
}

// --- Precios -----------------------------------------------------------------

/** 129.95 -> «129,95 €» (con espacio duro para que no se parta la línea). */
export function euros(valor: number): string {
  return `${valor.toFixed(2).replace(".", ",")} €`;
}

/** 150 -> «150 €», 129.95 -> «129,95 €»: sin decimales si no hacen falta. */
export function eurosCortos(valor: number): string {
  return Number.isInteger(valor) ? `${valor} €` : euros(valor);
}

const disponible = (o: Oferta) => o.disponibilidad !== "agotada";

/** Ofertas ordenadas: primero las disponibles por precio, al final las agotadas. */
export function ofertasOrdenadas(pala: Pala): Oferta[] {
  return [...pala.ofertas].sort(
    (a, b) => Number(disponible(b)) - Number(disponible(a)) || a.precio - b.precio,
  );
}

export function ofertasDisponibles(pala: Pala): Oferta[] {
  return ofertasOrdenadas(pala).filter(disponible);
}

/** La oferta disponible más barata, o null si está agotada en todas las tiendas. */
export function mejorOferta(pala: Pala): Oferta | null {
  return ofertasDisponibles(pala)[0] ?? null;
}

/** Precio «desde»: el de la mejor oferta, o el más bajo aunque esté agotada. */
export function precioDesde(pala: Pala): number {
  return (mejorOferta(pala) ?? ofertasOrdenadas(pala)[0]).precio;
}

export function minimoHistorico(pala: Pala): PuntoPrecio {
  return pala.historico.reduce((min, p) => (p.precio < min.precio ? p : min));
}

/** «una», «dos», «tres»… para frases; a partir de diez, la cifra. */
export function numeroEnPalabra(n: number): string {
  const palabras = ["cero", "una", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"];
  return palabras[n] ?? String(n);
}
