/**
 * Islas del área de cuenta: perfil, palas guardadas, avisos de precio e historial.
 * Lo guardado vive en este navegador (lib/cuenta); la sesión, en la API.
 */
import type { ComponentChildren } from "preact";
import { useState } from "preact/hooks";

import Icono from "@/components/Icono";
import PalaMini from "@/components/PalaMini";
import { Silueta } from "@/components/dibujos";
import { useGuardado, useMontado, useSesion } from "@/components/ganchos";
import { nombreTienda, palaPorSlug } from "@/data/catalogo";
import { type Pala, euros, eurosCortos, mejorOferta, precioDesde } from "@/lib/catalogo";
import {
  type Alerta,
  type EntradaHistorial,
  type PalaGuardada,
  alertas,
  alternarGuardada,
  borrarCuenta,
  borrarDatosLocales,
  cerrarSesion,
  cerrarTodasLasSesiones,
  eliminarAlerta,
  eliminarDelHistorial,
  historial,
  palasGuardadas,
  sesionRecordada,
} from "@/lib/cuenta";
import { etiquetas } from "@/lib/encuesta";
import { rutas } from "@/lib/rutas";

function fecha(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
}

/** Estado vacío común a las tres listas. */
function Vacio({ titulo, texto, children }: { titulo: string; texto: string; children: ComponentChildren }) {
  return (
    <div class="cta-vacio">
      <h2 class="subtitulo">{titulo}</h2>
      <p>{texto}</p>
      <div class="cta-acciones">{children}</div>
    </div>
  );
}

/** Recordatorio de que, sin correo, lo guardado se queda en este navegador. */
function AvisoSinCuenta({ texto }: { texto: string }) {
  const conSesion = useGuardado(() => sesionRecordada() !== null, true);
  if (conSesion) return null;
  return (
    <p class="cta-aviso">
      <Icono nombre="info" tamano={20} color="var(--azul)" />
      <span>
        {texto}{" "}
        <a class="lnk lnk-azul" href={rutas.acceso}>
          Acceder con tu correo
        </a>
      </span>
    </p>
  );
}

// --- Perfil -------------------------------------------------------------------

export function PanelPerfil() {
  const estado = useSesion();
  const guardadas = useGuardado(() => palasGuardadas().length, 0);
  const avisos = useGuardado(() => alertas().length, 0);
  const recomendaciones = useGuardado(() => historial().length, 0);
  const [confirmar, setConfirmar] = useState<"cuenta" | "datos" | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const sesion = estado && estado.tipo !== "invitado" ? estado.sesion : null;

  async function salir() {
    setOcupado(true);
    await cerrarSesion().catch(() => {});
    location.reload();
  }

  async function salirDeTodos() {
    setOcupado(true);
    try {
      await cerrarTodasLasSesiones();
      location.reload();
    } catch {
      setOcupado(false);
      setMensaje("No hemos podido cerrar las sesiones. Inténtalo de nuevo en unos minutos.");
    }
  }

  async function borrarLaCuenta() {
    setOcupado(true);
    try {
      await borrarCuenta();
      location.assign(rutas.inicio);
    } catch {
      setOcupado(false);
      setConfirmar(null);
      setMensaje("No hemos podido borrar la cuenta. Inténtalo de nuevo en unos minutos.");
    }
  }

  function borrarDatos() {
    borrarDatosLocales();
    setConfirmar(null);
    setMensaje("Hemos borrado lo guardado en este navegador.");
  }

  return (
    <div class="cta-perfil">
      {estado === null ? (
        <div class="cta-sesion cargando" aria-busy="true">
          <p>Comprobando tu sesión…</p>
        </div>
      ) : sesion ? (
        <div class="cta-sesion">
          <div class="quien">
            <span class="etiqueta">Has accedido como</span>
            <strong class="correo">{sesion.email}</strong>
            {sesion.desde && <span class="desde">Cuenta creada el {fecha(sesion.desde)}</span>}
            {estado.tipo === "sin-conexion" && (
              <span class="desde">No hemos podido comprobar tu sesión ahora mismo.</span>
            )}
          </div>
          <div class="cta-acciones">
            <button type="button" class="btn btn-m btn-contorno" onClick={salir} disabled={ocupado}>
              Cerrar sesión
            </button>
            {estado.tipo === "activa" && (
              <button type="button" class="lnk" onClick={salirDeTodos} disabled={ocupado}>
                Cerrar sesión en todos los dispositivos
              </button>
            )}
            {confirmar === "cuenta" ? (
              <span class="cta-confirmar pop" role="alert">
                <span>Se borran tu cuenta y lo guardado en este navegador.</span>
                <button type="button" class="btn btn-m btn-tinta" onClick={borrarLaCuenta} disabled={ocupado}>
                  Sí, borrar mi cuenta
                </button>
                <button type="button" class="lnk" onClick={() => setConfirmar(null)}>
                  Cancelar
                </button>
              </span>
            ) : (
              <button type="button" class="lnk cta-peligro" onClick={() => setConfirmar("cuenta")}>
                Borrar mi cuenta
              </button>
            )}
          </div>
        </div>
      ) : (
        <div class="cta-sesion invitado dk">
          <div class="quien">
            <h2 class="titulo">Estás usando palaideal sin registrarte.</h2>
            <p>
              Lo que guardas se queda en este navegador. Si accedes con tu correo podremos escribirte cuando baje el
              precio de una pala.
            </p>
          </div>
          <a class="btn btn-l btn-lima" href={rutas.acceso}>
            Acceder con tu correo
          </a>
        </div>
      )}

      <ul class="cta-resumen">
        <li>
          <a href={rutas.palasGuardadas}>
            <span class="n">{guardadas}</span>
            <span class="que">{guardadas === 1 ? "Pala guardada" : "Palas guardadas"}</span>
            <Icono nombre="flecha" tamano={22} class="arr" />
          </a>
        </li>
        <li>
          <a href={rutas.alertas}>
            <span class="n">{avisos}</span>
            <span class="que">{avisos === 1 ? "Aviso de precio" : "Avisos de precio"}</span>
            <Icono nombre="flecha" tamano={22} class="arr" />
          </a>
        </li>
        <li>
          <a href={rutas.historial}>
            <span class="n">{recomendaciones}</span>
            <span class="que">{recomendaciones === 1 ? "Recomendación" : "Recomendaciones"}</span>
            <Icono nombre="flecha" tamano={22} class="arr" />
          </a>
        </li>
      </ul>

      <section class="cta-datos">
        <div>
          <h2 class="subtitulo">Lo guardado en este navegador</h2>
          <p>
            Tus palas guardadas, tus avisos y tu historial se guardan aquí, en este dispositivo. El dato de molestias
            no se guarda nunca.
          </p>
        </div>
        {confirmar === "datos" ? (
          <span class="cta-confirmar pop" role="alert">
            <span>Se borran palas guardadas, avisos e historial.</span>
            <button type="button" class="btn btn-m btn-tinta" onClick={borrarDatos}>
              Sí, borrar
            </button>
            <button type="button" class="lnk" onClick={() => setConfirmar(null)}>
              Cancelar
            </button>
          </span>
        ) : (
          <button type="button" class="btn btn-m btn-contorno" onClick={() => setConfirmar("datos")}>
            <Icono nombre="papelera" tamano={18} />
            Borrar estos datos
          </button>
        )}
      </section>

      {mensaje && (
        <p class="aviso-form ok pop" role="status">
          <Icono nombre="check" tamano={18} grosor={2.6} />
          <span>{mensaje}</span>
        </p>
      )}
    </div>
  );
}

// --- Palas guardadas ----------------------------------------------------------

export function ListaGuardadas() {
  const montado = useMontado();
  const lista = useGuardado<PalaGuardada[]>(palasGuardadas, []);
  const conPala = lista.flatMap((g) => {
    const pala = palaPorSlug(g.slug);
    return pala ? [{ ...g, pala }] : [];
  });

  if (!montado) return <div class="cta-lista" aria-busy="true" />;

  if (conPala.length === 0) {
    return (
      <Vacio
        titulo="Todavía no has guardado ninguna pala."
        texto="Guarda las que te interesen desde su ficha o desde tu recomendación y las tendrás aquí para compararlas."
      >
        <a class="btn btn-l btn-azul" href={rutas.encuesta}>
          Hacer el cuestionario
        </a>
        <a class="lnk lnk-azul lnk-alto" href={rutas.palas}>
          Ver todas las palas
        </a>
      </Vacio>
    );
  }

  return (
    <div class="cta-lista">
      <AvisoSinCuenta texto="Estas palas están guardadas solo en este navegador." />
      <div class="rejilla-palas">
        {conPala.map(({ pala, fecha: guardadaEl }) => (
          <PalaMini key={pala.slug} pala={pala} texto={`Guardada el ${fecha(guardadaEl)}`}>
            <button type="button" class="lnk encima cta-quitar" onClick={() => alternarGuardada(pala.slug)}>
              Quitar
            </button>
          </PalaMini>
        ))}
      </div>
    </div>
  );
}

// --- Avisos de precio ---------------------------------------------------------

function FilaAlerta({ alerta, pala }: { alerta: Alerta; pala: Pala }) {
  const hoy = precioDesde(pala);
  const oferta = mejorOferta(pala);
  const cumplida = oferta !== null && hoy < alerta.objetivo;

  return (
    <li class={cumplida ? "cta-alerta cumplida" : "cta-alerta"}>
      <Silueta forma={pala.forma} ancho={56} trazo={7} punto={12} />
      <div class="datos">
        <a class="nombre" href={rutas.pala(pala.slug)}>
          {pala.nombre}
        </a>
        <span class="objetivo">
          Avisar cuando baje de <strong>{eurosCortos(alerta.objetivo)}</strong>
        </span>
        <span class="estado">
          {cumplida
            ? `Ya está por debajo: hoy cuesta ${euros(hoy)} en ${nombreTienda(oferta.tienda)}.`
            : `Hoy cuesta ${euros(hoy)}: le faltan ${eurosCortos(Math.ceil(hoy - alerta.objetivo))} por bajar.`}
        </span>
      </div>
      <div class="acciones">
        {cumplida && (
          <a
            class="btn btn-m btn-azul"
            href={rutas.tienda(oferta.id, { origen: "cuenta" })}
            rel="sponsored nofollow noopener"
          >
            Ir a la tienda
            <Icono nombre="salida" tamano={18} grosor={2.4} class="arr" />
          </a>
        )}
        <button
          type="button"
          class="btn btn-m btn-contorno"
          onClick={() => eliminarAlerta(alerta.id)}
          aria-label={`Quitar el aviso de ${pala.nombre}`}
        >
          <Icono nombre="papelera" tamano={18} />
          Quitar
        </button>
      </div>
    </li>
  );
}

export function ListaAlertas() {
  const montado = useMontado();
  const lista = useGuardado<Alerta[]>(alertas, []);
  const conPala = lista.flatMap((alerta) => {
    const pala = palaPorSlug(alerta.slug);
    return pala ? [{ alerta, pala }] : [];
  });

  if (!montado) return <div class="cta-lista" aria-busy="true" />;

  if (conPala.length === 0) {
    return (
      <Vacio
        titulo="No tienes ningún aviso de precio."
        texto="En la ficha de cada pala puedes decirnos tu precio. Te escribimos el día que alguna tienda lo alcance."
      >
        <a class="btn btn-l btn-azul" href={rutas.palas}>
          Ver todas las palas
        </a>
        <a class="lnk lnk-azul lnk-alto" href={rutas.palasGuardadas}>
          Ir a mis palas guardadas
        </a>
      </Vacio>
    );
  }

  return (
    <div class="cta-lista">
      <AvisoSinCuenta texto="Falta tu correo para poder avisarte cuando baje el precio." />
      <ul class="cta-alertas">
        {conPala.map(({ alerta, pala }) => (
          <FilaAlerta key={alerta.id} alerta={alerta} pala={pala} />
        ))}
      </ul>
    </div>
  );
}

// --- Historial ----------------------------------------------------------------

function FilaHistorial({ entrada }: { entrada: EntradaHistorial }) {
  const recomendadas = entrada.palas.flatMap((slug) => palaPorSlug(slug) ?? []);

  return (
    <li class="cta-entrada">
      <div class="cabeza">
        <span class="etiqueta">{fecha(entrada.fecha)}</span>
        <ul class="respuestas" aria-label="Respuestas">
          {etiquetas(entrada.respuestas).map((texto) => (
            <li key={texto}>{texto}</li>
          ))}
        </ul>
      </div>
      <ol class="palas">
        {recomendadas.map((pala, i) => (
          <li key={pala.slug}>
            <span class="n">{String(i + 1).padStart(2, "0")}</span>
            <a class="lnk" href={rutas.pala(pala.slug)}>
              {pala.nombre}
            </a>
            <span class="precio">{euros(precioDesde(pala))}</span>
          </li>
        ))}
      </ol>
      <div class="acciones">
        <a class="btn btn-m btn-tinta" href={rutas.recomendacionGuardada(entrada.id)}>
          Ver recomendación
        </a>
        <button type="button" class="lnk" onClick={() => eliminarDelHistorial(entrada.id)}>
          Quitar del historial
        </button>
      </div>
    </li>
  );
}

export function ListaHistorial() {
  const montado = useMontado();
  const lista = useGuardado<EntradaHistorial[]>(historial, []);

  if (!montado) return <div class="cta-lista" aria-busy="true" />;

  if (lista.length === 0) {
    return (
      <Vacio
        titulo="Todavía no tienes recomendaciones."
        texto="Cada vez que termines el cuestionario, la recomendación se guarda aquí para que puedas volver a ella."
      >
        <a class="btn btn-l btn-azul" href={rutas.encuesta}>
          Hacer el cuestionario
        </a>
      </Vacio>
    );
  }

  return (
    <div class="cta-lista">
      <AvisoSinCuenta texto="Tu historial está guardado solo en este navegador, sin el dato de molestias." />
      <ul class="cta-historial">
        {lista.map((entrada) => (
          <FilaHistorial key={entrada.id} entrada={entrada} />
        ))}
      </ul>
    </div>
  );
}
