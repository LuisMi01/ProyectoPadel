/**
 * Aviso de bajada de precio. Dos presentaciones con la misma lógica:
 * la tarjeta oscura de la ficha (por defecto) y el panel claro de la recomendación.
 */
import { useState } from "preact/hooks";

import Icono from "@/components/Icono";
import { useGuardado } from "@/components/ganchos";
import { eurosCortos } from "@/lib/catalogo";
import { type Alerta, alertaDe, crearAlerta, eliminarAlerta, sesionRecordada } from "@/lib/cuenta";
import { rutas } from "@/lib/rutas";

interface Props {
  slug: string;
  /** Precio más bajo de hoy, para validar el objetivo. */
  precioActual: number;
}

/** Sugerencia para el campo: un precio redondo algo por debajo del actual. */
function sugerencia(precio: number): string {
  return String(Math.max(5, Math.floor((precio * 0.93) / 5) * 5));
}

function useAviso({ slug, precioActual }: Props) {
  const alerta = useGuardado<Alerta | undefined>(() => alertaDe(slug), undefined);
  const conCorreo = useGuardado(() => sesionRecordada() !== null, false);
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editando, setEditando] = useState(false);

  function crear(e: Event) {
    e.preventDefault();
    const objetivo = Number(valor.replace(",", "."));
    if (!valor.trim() || !Number.isFinite(objetivo) || objetivo <= 0) {
      setError("Escribe un precio en euros.");
      return;
    }
    if (objetivo >= precioActual) {
      setError(`Hoy ya cuesta ${eurosCortos(precioActual)}. Pon un precio más bajo.`);
      return;
    }
    crearAlerta(slug, Math.round(objetivo * 100) / 100);
    setError(null);
    setEditando(false);
  }

  function cambiar() {
    if (alerta) setValor(String(alerta.objetivo));
    setEditando(true);
  }

  function quitar() {
    if (alerta) eliminarAlerta(alerta.id);
    setValor("");
    setEditando(false);
  }

  return {
    alerta: editando ? undefined : alerta,
    conCorreo,
    valor,
    error,
    placeholder: sugerencia(precioActual),
    escribir: (texto: string) => {
      setValor(texto);
      setError(null);
    },
    crear,
    cambiar,
    quitar,
  };
}

/** Lo que se muestra cuando el aviso ya existe. */
function AvisoCreado({ aviso }: { aviso: ReturnType<typeof useAviso> }) {
  if (!aviso.alerta) return null;
  return (
    <div class="aviso-creado pop" role="status">
      <p class="aviso-form ok">
        <Icono nombre="check" tamano={18} grosor={2.6} />
        <span>
          Aviso creado: te escribiremos cuando baje de <strong>{eurosCortos(aviso.alerta.objetivo)}</strong>.
        </span>
      </p>
      {!aviso.conCorreo && (
        <p class="aviso-falta">
          Falta tu correo para poder avisarte.{" "}
          <a class="lnk" href={rutas.acceso}>
            Acceder
          </a>
        </p>
      )}
      <p class="aviso-enlaces">
        <button type="button" class="lnk" onClick={aviso.cambiar}>
          Cambiar precio
        </button>
        <button type="button" class="lnk" onClick={aviso.quitar}>
          Quitar aviso
        </button>
        <a class="lnk" href={rutas.alertas}>
          Ver mis avisos
        </a>
      </p>
    </div>
  );
}

/** Tarjeta oscura de la ficha: «¿Esperas a que baje?». */
export default function AvisoPrecio(props: Props) {
  const aviso = useAviso(props);
  const id = `objetivo-${props.slug}`;

  return (
    <form class="aviso-ficha dk" onSubmit={aviso.crear} noValidate>
      <Icono nombre="campana" tamano={30} grosor={1.8} color="#D9F53B" />
      <h3 class="titulo">¿Esperas a que baje?</h3>
      <p class="aviso-intro">Dinos tu precio y te escribimos el día que alguna tienda lo alcance.</p>

      {aviso.alerta ? (
        <AvisoCreado aviso={aviso} />
      ) : (
        <>
          <div class="aviso-campo">
            <label class="rotulo" for={id}>
              Avísame cuando baje de
            </label>
            <div class="aviso-entrada">
              <input
                id={id}
                class="campo"
                type="number"
                inputMode="decimal"
                min="1"
                step="any"
                placeholder={aviso.placeholder}
                value={aviso.valor}
                aria-invalid={aviso.error ? true : undefined}
                aria-describedby={aviso.error ? `${id}-error` : undefined}
                onInput={(e) => aviso.escribir(e.currentTarget.value)}
              />
              <span aria-hidden="true">€</span>
            </div>
            {aviso.error && (
              <p class="aviso-form error" id={`${id}-error`} role="alert">
                {aviso.error}
              </p>
            )}
          </div>
          <button type="submit" class="btn btn-lima aviso-boton">
            Crear aviso
          </button>
        </>
      )}
    </form>
  );
}

/** Panel claro que se despliega bajo «Avisarme si baja» en la recomendación. */
export function AvisoEnLinea(props: Props) {
  const aviso = useAviso(props);
  const id = `objetivo-${props.slug}`;

  if (aviso.alerta) {
    return (
      <div class="aviso-linea">
        <AvisoCreado aviso={aviso} />
      </div>
    );
  }

  return (
    <form class="aviso-linea pop" onSubmit={aviso.crear} noValidate>
      <div class="aviso-campo">
        <label class="rotulo" for={id}>
          Avísame cuando baje de
        </label>
        <div class="aviso-entrada">
          <input
            id={id}
            class="campo"
            type="number"
            inputMode="decimal"
            min="1"
            step="any"
            placeholder={aviso.placeholder}
            value={aviso.valor}
            aria-invalid={aviso.error ? true : undefined}
            aria-describedby={aviso.error ? `${id}-error` : undefined}
            onInput={(e) => aviso.escribir(e.currentTarget.value)}
          />
          <span aria-hidden="true">€</span>
        </div>
      </div>
      <button type="submit" class="btn btn-tinta aviso-boton">
        Crear aviso
      </button>
      <span class="aviso-nota">Te lo mandamos al correo con el que accedas. Sin publicidad.</span>
      {aviso.error && (
        <p class="aviso-form error" id={`${id}-error`} role="alert">
          {aviso.error}
        </p>
      )}
    </form>
  );
}
