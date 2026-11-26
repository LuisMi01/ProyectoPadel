/**
 * Dibujos de pala de los diseños, por forma. Son componentes Preact para poder
 * usarlos igual en páginas Astro (se renderizan a HTML) y dentro de las islas.
 */
import type { Caras, Forma } from "@/lib/catalogo";

// --- Silueta pequeña (viewBox 160×210) ----------------------------------------

const SILUETAS: Record<Forma, { contorno: string; puntoY: number }> = {
  redonda: {
    contorno: "M80 10 C117 10 145 40 145 78 C145 115 121 139 94 152 L66 152 C39 139 15 115 15 78 C15 40 43 10 80 10 Z",
    puntoY: 80,
  },
  lagrima: {
    contorno: "M80 8 C120 8 146 34 146 66 C146 104 116 126 94 152 L66 152 C44 126 14 104 14 66 C14 34 40 8 80 8 Z",
    puntoY: 66,
  },
  diamante: {
    contorno: "M80 8 C102 8 150 12 150 52 C150 96 114 124 94 152 L66 152 C46 124 10 96 10 52 C10 12 58 8 80 8 Z",
    puntoY: 52,
  },
};

interface PropsSilueta {
  forma: Forma;
  ancho: number;
  /** Cara blanca (sobre fondo tenue) o tenue (sobre fondo blanco). */
  cara?: "blanca" | "tenue";
  trazo?: number;
  /** Radio del punto dulce. */
  punto?: number;
  /** Añade el anillo que late al pasar el ratón por la tarjeta (.card:hover .spot). */
  anillo?: boolean;
  class?: string;
}

export function Silueta({ forma, ancho, cara = "tenue", trazo = 6, punto = 11, anillo = false, class: clase }: PropsSilueta) {
  const { contorno, puntoY } = SILUETAS[forma];
  return (
    <svg
      class={clase}
      aria-hidden="true"
      width={ancho}
      height={Math.round((ancho * 210) / 160)}
      viewBox="0 0 160 210"
      style={{ flex: "none" }}
    >
      <rect x="68" y="146" width="24" height="58" rx="5" style="fill: var(--tinta)" />
      <path
        d={contorno}
        stroke-width={trazo}
        stroke-linejoin="round"
        style={`fill: ${cara === "blanca" ? "var(--blanco)" : "var(--tenue)"}; stroke: var(--tinta)`}
      />
      {anillo && (
        <circle class="spot" cx="80" cy={puntoY} r={punto + 3} fill="none" stroke-width="2.5" style="stroke: var(--azul)" />
      )}
      <circle cx="80" cy={puntoY} r={punto} style="fill: var(--azul)" />
    </svg>
  );
}

// --- Pala grande con agujeros y punto dulce (viewBox 320×420) -----------------

interface Geometria {
  contorno: string;
  /** Elipse que recorta la zona de agujeros. */
  cara: { cx: number; cy: number; rx: number; ry: number };
  puntoY: number;
  descripcion: string;
}

const PALAS: Record<Forma, Geometria> = {
  redonda: {
    contorno:
      "M160 20 C234 20 290 80 290 156 C290 230 242 278 188 304 L132 304 C78 278 30 230 30 156 C30 80 86 20 160 20 Z",
    cara: { cx: 160, cy: 150, rx: 88, ry: 92 },
    puntoY: 156,
    descripcion: "forma redonda con el punto dulce centrado",
  },
  lagrima: {
    contorno:
      "M160 16 C240 16 292 68 292 132 C292 208 232 252 188 304 L132 304 C88 252 28 208 28 132 C28 68 80 16 160 16 Z",
    cara: { cx: 160, cy: 140, rx: 92, ry: 90 },
    puntoY: 132,
    descripcion: "forma de lágrima con el punto dulce algo más arriba",
  },
  diamante: {
    contorno:
      "M160 16 C204 16 300 24 300 104 C300 192 228 248 188 304 L132 304 C92 248 20 192 20 104 C20 24 116 16 160 16 Z",
    cara: { cx: 160, cy: 124, rx: 100, ry: 84 },
    puntoY: 104,
    descripcion: "forma de diamante con el punto dulce alto",
  },
};

/** «forma redonda con el punto dulce centrado», para textos alternativos. */
export function descripcionForma(forma: Forma): string {
  return PALAS[forma].descripcion;
}

interface PropsPala {
  forma: Forma;
  /** Sufijo único para los id del patrón y el recorte (hay varias palas por página). */
  uid: string;
  etiqueta: string;
  /** Dibuja el contorno y hace aparecer los agujeros al cargar (ficha). */
  animada?: boolean;
  /** Material de las caras: cambia el color de la cara y le pone la trama del tejido. */
  caras?: Caras;
  class?: string;
}

/** Radio del punto dulce según la forma: grande en la redonda, medio en la lágrima, pequeño en el diamante. */
const RADIO_PUNTO: Record<Forma, number> = { redonda: 24, lagrima: 19, diamante: 14 };

/** Cómo se ve cada material: color de la cara, trama del tejido y color de los agujeros. */
const MATERIAL: Record<Caras, { cara: string; tejido: number; agujero: string }> = {
  fibra: { cara: "var(--blanco)", tejido: 0, agujero: "var(--azul)" },
  hibrida: { cara: "#e3e7ee", tejido: 0.35, agujero: "var(--azul)" },
  carbono: { cara: "#2b303b", tejido: 0.9, agujero: "#8fb0ff" },
};

export function PalaGrande({
  forma,
  uid,
  etiqueta,
  animada = false,
  caras = "fibra",
  class: clase,
}: PropsPala) {
  const { contorno, cara, puntoY } = PALAS[forma];
  const radio = RADIO_PUNTO[forma];
  const material = MATERIAL[caras];
  const patron = `agujeros-${uid}`;
  const recorte = `cara-${uid}`;
  const tejido = `tejido-${uid}`;

  return (
    <svg class={clase} role="img" aria-label={etiqueta} viewBox="0 0 320 420">
      <defs>
        <pattern id={patron} width="30" height="30" patternUnits="userSpaceOnUse">
          <circle cx="7.5" cy="7.5" r="4.8" style={`fill: ${material.agujero}`} />
          <circle cx="22.5" cy="22.5" r="4.8" style={`fill: ${material.agujero}`} />
        </pattern>
        {/* Trama de tejido (sarga): cuadros alternos claros y oscuros en diagonal. */}
        <pattern id={tejido} width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="5" height="5" fill="rgba(255,255,255,0.14)" />
          <rect x="5" y="5" width="5" height="5" fill="rgba(255,255,255,0.14)" />
          <rect x="5" width="5" height="5" fill="rgba(0,0,0,0.12)" />
          <rect y="5" width="5" height="5" fill="rgba(0,0,0,0.12)" />
        </pattern>
        <clipPath id={recorte}>
          <ellipse cx={cara.cx} cy={cara.cy} rx={cara.rx} ry={cara.ry} />
        </clipPath>
      </defs>
      <rect x="138" y="288" width="44" height="120" rx="9" style="fill: var(--noche)" />
      <rect x="131" y="394" width="58" height="18" rx="8" style="fill: var(--lima)" />
      <path d={contorno} style={`fill: ${material.cara}`} />
      {material.tejido > 0 && <path d={contorno} fill={`url(#${tejido})`} opacity={material.tejido} />}
      <rect
        class={animada ? "holes" : undefined}
        x={cara.cx - cara.rx}
        y={cara.cy - cara.ry}
        width={cara.rx * 2}
        height={cara.ry * 2}
        fill={`url(#${patron})`}
        clip-path={`url(#${recorte})`}
      />
      <path
        class={animada ? "dr" : undefined}
        pathLength={animada ? 1 : undefined}
        d={contorno}
        fill="none"
        stroke-width="8"
        stroke-linejoin="round" style="stroke: var(--noche)"
      />
      <path d="M140 262 L180 262 L160 292 Z" stroke-width="4.5" stroke-linejoin="round" style="fill: var(--azul); stroke: var(--noche)" />
      <circle
        class={animada ? "ring tarde" : "ring"}
        cx="160"
        cy={puntoY}
        r={radio}
        fill="none"
        stroke-width="2.5" style="stroke: var(--noche)"
      />
      <circle cx="160" cy={puntoY} r={radio} stroke-width="3" style="fill: var(--lima); stroke: var(--noche)" />
    </svg>
  );
}
