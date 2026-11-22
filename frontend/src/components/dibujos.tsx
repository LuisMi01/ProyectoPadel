/**
 * Dibujos de pala de los diseños, por forma. Son componentes Preact para poder
 * usarlos igual en páginas Astro (se renderizan a HTML) y dentro de las islas.
 */
import type { Forma } from "@/lib/catalogo";

// --- Silueta pequeña (viewBox 160×210) ----------------------------------------

const SILUETAS: Record<Forma, { contorno: string; puntoY: number }> = {
  redonda: {
    contorno: "M80 10 C116 10 142 38 142 74 C142 110 118 128 94 152 L66 152 C42 128 18 110 18 74 C18 38 44 10 80 10 Z",
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
      <rect x="68" y="146" width="24" height="58" rx="5" fill="#0A1B3D" />
      <path
        d={contorno}
        fill={cara === "blanca" ? "#FFFFFF" : "#E3EAF4"}
        stroke="#0A1B3D"
        stroke-width={trazo}
        stroke-linejoin="round"
      />
      {anillo && (
        <circle class="spot" cx="80" cy={puntoY} r={punto + 3} fill="none" stroke="#1747C9" stroke-width="2.5" />
      )}
      <circle cx="80" cy={puntoY} r={punto} fill="#1747C9" />
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
      "M160 20 C232 20 284 76 284 148 C284 220 236 256 188 304 L132 304 C84 256 36 220 36 148 C36 76 88 20 160 20 Z",
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
  class?: string;
}

export function PalaGrande({ forma, uid, etiqueta, animada = false, class: clase }: PropsPala) {
  const { contorno, cara, puntoY } = PALAS[forma];
  const patron = `agujeros-${uid}`;
  const recorte = `cara-${uid}`;

  return (
    <svg class={clase} role="img" aria-label={etiqueta} viewBox="0 0 320 420">
      <defs>
        <pattern id={patron} width="30" height="30" patternUnits="userSpaceOnUse">
          <circle cx="7.5" cy="7.5" r="4.8" fill="#1747C9" />
          <circle cx="22.5" cy="22.5" r="4.8" fill="#1747C9" />
        </pattern>
        <clipPath id={recorte}>
          <ellipse cx={cara.cx} cy={cara.cy} rx={cara.rx} ry={cara.ry} />
        </clipPath>
      </defs>
      <rect x="138" y="288" width="44" height="120" rx="9" fill="#081535" />
      <rect x="131" y="394" width="58" height="18" rx="8" fill="#D9F53B" />
      <path d={contorno} fill="#FFFFFF" />
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
        stroke="#081535"
        stroke-width="8"
        stroke-linejoin="round"
      />
      <path d="M140 262 L180 262 L160 292 Z" fill="#1747C9" stroke="#081535" stroke-width="4.5" stroke-linejoin="round" />
      <circle
        class={animada ? "ring tarde" : "ring"}
        cx="160"
        cy={puntoY}
        r="20"
        fill="none"
        stroke="#081535"
        stroke-width="2.5"
      />
      <circle cx="160" cy={puntoY} r="20" fill="#D9F53B" stroke="#081535" stroke-width="3" />
    </svg>
  );
}
