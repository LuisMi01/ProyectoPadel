/** Tarjeta compacta de una pala: silueta, nombre, una línea de texto y precio. */
import type { ComponentChildren } from "preact";

import { Silueta } from "@/components/dibujos";
import { type Pala, euros, precioDesde } from "@/lib/catalogo";
import { rutas } from "@/lib/rutas";

interface Props {
  pala: Pala;
  /** Línea descriptiva bajo el nombre. Por defecto, la marca. */
  texto?: string;
  /** Contenido extra bajo el precio (p. ej. acciones en el área de cuenta). */
  children?: ComponentChildren;
}

export default function PalaMini({ pala, texto, children }: Props) {
  return (
    <article class="pala-mini card card-enlace">
      <Silueta forma={pala.forma} ancho={64} trazo={7} punto={12} />
      <div class="cuerpo">
        <a class="nombre cubre" href={rutas.pala(pala.slug)}>
          {pala.nombre}
        </a>
        <span class="descripcion">{texto ?? pala.marca}</span>
        <span class="precio">desde {euros(precioDesde(pala))}</span>
        {children}
      </div>
    </article>
  );
}
