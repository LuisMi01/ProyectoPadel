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

  /** Valoraciones de 1 a 5 con un decimal, calculadas con valoraciones() a partir de la ficha. */
  /** Lo fácil que es moverla. */
  manejabilidad: number;
  /** Lo exacta que sale la bola. */
  precision: number;
  tolerancia: number;
  potencia: number;
  /** Cuánto absorbe las vibraciones (y cuida el brazo). Baja: tacto seco. */
  amortiguacion: number;
  /** Control de juego: no se enseña, lo usa el recomendador para la alternativa «más control». */
  control: number;

  resumen: string;
  paraTi: string[];
  mejorOtra: string[];

  ofertas: Oferta[];
  /** Histórico de 90 días, del más antiguo al más reciente. */
  historico: PuntoPrecio[];
}

// --- Textos ------------------------------------------------------------------

/** Lo que se escribe de una pala: las valoraciones se calculan (ver conValoraciones). */
export type FichaPala = Omit<Pala, "manejabilidad" | "precision" | "tolerancia" | "potencia" | "amortiguacion" | "control">;

/** De 0 a 1 a una nota de 1 a 5, con un decimal para que se distingan palas de la misma forma. */
const nota = (x: number) => Math.round((1 + 4 * x) * 10) / 10;

/**
 * Manejabilidad, precisión, tolerancia, potencia y amortiguación (más el control de juego que usa
 * el recomendador), de 1 a 5, a partir de la ficha. Son iguales para
 * todas las palas y no se pueden inflar a mano. Mismas fórmulas en backend/app/domain/valoraciones.py.
 */
export function valoraciones({
  forma,
  balance,
  dureza,
  peso,
  caras,
}: Pick<Pala, "forma" | "balance" | "dureza" | "peso" | "caras">): Pick<
  Pala,
  "manejabilidad" | "precision" | "tolerancia" | "potencia" | "amortiguacion" | "control"
> {
  const puntoDulce = { redonda: 1, lagrima: 0.5, diamante: 0 }[forma]; // amplio y centrado: 1
  const cabeza = { bajo: 0, medio: 0.5, alto: 1 }[balance]; // peso hacia la cabeza: 1
  const blandura = (5 - dureza) / 4; // núcleo muy blando: 1; duro: 0
  const ligereza = Math.min(1, Math.max(0, (375 - peso) / 30)); // 345 g o menos: 1; 375 g: 0
  const rigidez = { fibra: 0, hibrida: 0.5, carbono: 1 }[caras];
  return {
    manejabilidad: nota(0.6 * ligereza + 0.4 * (1 - cabeza)),
    // Núcleo duro y caras rígidas: la bola sale como la mandas. Un punto dulce pequeño también
    // premia a quien golpea en el centro.
    precision: nota(0.45 * (1 - blandura) + 0.3 * rigidez + 0.25 * (1 - puntoDulce)),
    tolerancia: nota(0.6 * puntoDulce + 0.25 * blandura + 0.15 * (1 - cabeza)),
    // Control de juego (no se enseña): forma, balance bajo, núcleo duro y ligereza.
    control: nota(0.35 * puntoDulce + 0.25 * (1 - cabeza) + 0.25 * (1 - blandura) + 0.15 * ligereza),
    potencia: nota(0.4 * (1 - puntoDulce) + 0.3 * cabeza + 0.15 * (1 - blandura) + 0.15 * rigidez),
    amortiguacion: nota(0.4 * blandura + 0.25 * ligereza + 0.2 * (1 - cabeza) + 0.15 * (1 - rigidez)),
  };
}

/** La pala con sus valoraciones calculadas. */
export function conValoraciones(ficha: FichaPala): Pala {
  return { ...ficha, ...valoraciones(ficha) };
}

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
