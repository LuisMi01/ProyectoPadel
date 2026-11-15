/** Iconos de trazo de los diseños. Sirve en páginas Astro y en islas Preact. */
import type { ComponentChildren } from "preact";

export type NombreIcono =
  | "flecha"
  | "salida"
  | "atras"
  | "check"
  | "cruz"
  | "candado"
  | "sobre"
  | "moneda"
  | "campana"
  | "marcador"
  | "info"
  | "mas"
  | "menu"
  | "papelera"
  | "reloj"
  | "usuario";

const TRAZOS: Record<NombreIcono, ComponentChildren> = {
  flecha: (
    <>
      <path d="M4 12h16" />
      <path d="M13 5l7 7-7 7" />
    </>
  ),
  salida: (
    <>
      <path d="M7 17L17 7" />
      <path d="M8 7h9v9" />
    </>
  ),
  atras: (
    <>
      <path d="M20 12H4" />
      <path d="M11 5l-7 7 7 7" />
    </>
  ),
  check: <path d="M4 12.5l5.5 5.5L20 7" />,
  cruz: (
    <>
      <path d="M6 6l12 12" />
      <path d="M18 6L6 18" />
    </>
  ),
  candado: (
    <>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
  sobre: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 8l9 6 9-6" />
    </>
  ),
  moneda: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15.5 8.6a4.2 4.2 0 1 0 0 6.8" />
      <path d="M7 10.8h6" />
      <path d="M7 13.4h5" />
    </>
  ),
  campana: (
    <>
      <path d="M6 9a6 6 0 0 1 12 0c0 6 2.5 7 2.5 7h-17S6 15 6 9z" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </>
  ),
  marcador: <path d="M6 4h12v17l-6-4.5L6 21z" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6" />
      <path d="M12 7.5v.5" />
    </>
  ),
  mas: (
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>
  ),
  menu: (
    <>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </>
  ),
  papelera: (
    <>
      <path d="M4 7h16" />
      <path d="M9 7V4.5h6V7" />
      <path d="M6.5 7l1 13h9l1-13" />
    </>
  ),
  reloj: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </>
  ),
  usuario: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
    </>
  ),
};

interface Props {
  nombre: NombreIcono;
  tamano?: number;
  grosor?: number;
  color?: string;
  relleno?: string;
  class?: string;
}

export default function Icono({
  nombre,
  tamano = 24,
  grosor = 2,
  color = "currentColor",
  relleno = "none",
  class: clase,
}: Props) {
  return (
    <svg
      class={clase}
      aria-hidden="true"
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill={relleno}
      stroke={color}
      stroke-width={grosor}
      stroke-linecap="round"
      stroke-linejoin="round"
      style={{ flex: "none" }}
    >
      {TRAZOS[nombre]}
    </svg>
  );
}
