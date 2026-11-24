/** Botón «Guardar pala». Se guarda en este navegador, sin necesidad de cuenta. */
import Icono from "@/components/Icono";
import { useGuardado } from "@/components/ganchos";
import { alternarGuardada, estaGuardada } from "@/lib/cuenta";
import { rutas } from "@/lib/rutas";

interface Props {
  slug: string;
  /** Muestra debajo el enlace a las palas guardadas cuando ya lo está. */
  conEnlace?: boolean;
}

export function BotonGuardar({ slug }: { slug: string }) {
  const guardada = useGuardado(() => estaGuardada(slug), false);
  return (
    <button
      type="button"
      class="btn btn-m btn-contorno"
      aria-pressed={guardada}
      onClick={() => alternarGuardada(slug)}
    >
      <Icono nombre="marcador" tamano={18} relleno={guardada ? "var(--lima)" : "none"} />
      {guardada ? "Guardada" : "Guardar pala"}
    </button>
  );
}

/** Aviso de que la pala está guardada, con enlace a la lista. */
export function AvisoGuardada({ slug }: { slug: string }) {
  const guardada = useGuardado(() => estaGuardada(slug), false);
  if (!guardada) return null;
  return (
    <p class="aviso-form ok pop" role="status">
      <Icono nombre="check" tamano={18} grosor={2.6} />
      <span>
        Guardada en este navegador.{" "}
        <a class="lnk" href={rutas.palasGuardadas}>
          Ver mis palas guardadas
        </a>
      </span>
    </p>
  );
}

export default function GuardarPala({ slug, conEnlace = true }: Props) {
  return (
    <div class="guardar-pala">
      <BotonGuardar slug={slug} />
      {conEnlace && <AvisoGuardada slug={slug} />}
    </div>
  );
}
