/**
 * Isla Preact del cuestionario: cabecera con progreso, preguntas y el panel
 * «Tu pala, tomando forma». El flujo y la persistencia están en lib/encuesta.
 */
import { useEffect, useRef, useState } from "preact/hooks";

import Icono from "@/components/Icono";
import { type Forma, textoForma } from "@/lib/catalogo";
import {
  type BalanceFino,
  MOMENTOS,
  type Paso,
  type Pregunta,
  type PuntoDulce,
  type Reanudacion,
  type Respuestas,
  SIN_SALUD,
  type Salud,
  TEXTO_BALANCE_FINO,
  TEXTO_CARAS,
  TEXTO_PUNTO_DULCE,
  ZONAS,
  borrarProgreso,
  cargarProgreso,
  definicion,
  guardarFinal,
  guardarProgreso,
  leerFinal,
  perfilOrientativo,
  progreso,
  responder,
  respuestasRecorridas,
  resumen,
  siguientePaso,
  textoMomento,
} from "@/lib/encuesta";
import { rutas } from "@/lib/rutas";

interface Estado {
  paso: Paso;
  /** Pasos ya recorridos, para «Atrás». */
  historial: Paso[];
  respuestas: Respuestas;
  salud: Salud;
}

const INICIAL: Estado = { paso: "camino", historial: [], respuestas: {}, salud: SIN_SALUD };

const TECLAS = "ABCD";

function esPregunta(paso: Paso): paso is Pregunta {
  return paso !== "zona" && paso !== "fin";
}

export default function Encuesta() {
  const [estado, setEstado] = useState<Estado>(INICIAL);
  const [aMedias, setAMedias] = useState<Reanudacion | null>(null);
  const titulo = useRef<HTMLHeadingElement>(null);
  const primerPintado = useRef(true);

  const { paso, historial, respuestas, salud } = estado;

  // Al llegar: editar las últimas respuestas, entrar con el camino ya elegido u ofrecer retomar.
  useEffect(() => {
    const parametros = new URLSearchParams(location.search);
    const camino = parametros.get("camino");

    if (parametros.has("editar")) {
      const ultimas = leerFinal();
      if (ultimas) setEstado({ ...INICIAL, respuestas: ultimas.respuestas, salud: ultimas.salud });
    } else if (camino === "primera" || camino === "cambio") {
      setEstado({ ...INICIAL, paso: "exp", historial: ["camino"], respuestas: { camino } });
    } else {
      setAMedias(cargarProgreso());
    }
  }, []);

  // Al cambiar de paso, el foco va al enunciado para que el teclado y los lectores sigan el hilo.
  useEffect(() => {
    if (primerPintado.current) {
      primerPintado.current = false;
      return;
    }
    titulo.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [paso]);

  function avanzar(desde: Paso, nuevas: Respuestas, nuevaSalud: Salud) {
    const siguiente = siguientePaso(desde, nuevas);
    if (siguiente === "fin") {
      guardarFinal(nuevas, nuevaSalud);
      borrarProgreso();
    } else {
      guardarProgreso(nuevas);
    }
    setAMedias(null);
    setEstado({ paso: siguiente, historial: [...historial, desde], respuestas: nuevas, salud: nuevaSalud });
  }

  function elegir(pregunta: Pregunta, id: string) {
    const nuevas = responder(respuestas, pregunta, id as never);
    // Si ya no hay molestias, se olvida el detalle.
    const nuevaSalud = pregunta === "mol" && id !== "si" ? SIN_SALUD : salud;
    avanzar(pregunta, nuevas, nuevaSalud);
  }

  function retroceder() {
    const previo = historial[historial.length - 1];
    if (previo) setEstado({ ...estado, paso: previo, historial: historial.slice(0, -1) });
  }

  function retomar() {
    if (!aMedias) return;
    setEstado({ paso: aMedias.paso, historial: aMedias.historial, respuestas: aMedias.respuestas, salud: SIN_SALUD });
    setAMedias(null);
  }

  // Las letras A–D eligen la opción correspondiente. El oyente se registra una
  // sola vez y lee el paso actual de una referencia, para no perder pulsaciones
  // entre una pregunta y la siguiente.
  const alTeclear = useRef<(letra: number) => boolean>(() => false);
  alTeclear.current = (letra) => {
    if (!esPregunta(paso)) return false;
    const opcion = definicion(paso, respuestas).opciones[letra];
    if (!opcion) return false;
    elegir(paso, opcion.id);
    return true;
  };

  useEffect(() => {
    const alPulsar = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey || e.repeat || e.key.length !== 1) return;
      const destino = e.target as HTMLElement | null;
      if (destino && /^(INPUT|TEXTAREA|SELECT)$/.test(destino.tagName)) return;
      const letra = TECLAS.indexOf(e.key.toUpperCase());
      if (letra >= 0 && alTeclear.current(letra)) e.preventDefault();
    };
    window.addEventListener("keydown", alPulsar);
    return () => window.removeEventListener("keydown", alPulsar);
  }, []);

  const avance = progreso(paso, respuestas);
  const zonaLista = Boolean(salud.zona && salud.momento && salud.consentimiento);
  const def = esPregunta(paso) ? definicion(paso, respuestas) : null;

  return (
    <>
      <header class="enc-cab">
        <div class="contenedor enc-cab-dentro">
          <a href={rutas.inicio} class="logo claro" aria-label="palaideal, ir al inicio">
            <span class="punto" aria-hidden="true" />
            <span>
              pala<span class="fino">ideal</span>
            </span>
          </a>
          <div class="enc-progreso">
            <span class="etiqueta">{avance.rotulo}</span>
            <div
              class="enc-barra"
              role="progressbar"
              aria-label="Progreso del cuestionario"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={avance.porcentaje}
            >
              <div class="bar" style={{ width: `${avance.porcentaje}%` }} />
            </div>
          </div>
          <a class="lnk lnk-alto enc-salir" href={rutas.inicio}>
            {paso === "fin" ? "Salir" : "Guardar y salir"}
          </a>
        </div>
      </header>

      <main id="contenido" class="contenedor enc-main">
        <div class="enc-col">
          {aMedias && paso === "camino" && (
            <div class="enc-retomar">
              <span>Tienes un cuestionario a medias.</span>
              <button type="button" class="btn btn-lima" onClick={retomar}>
                Retomar donde lo dejaste
              </button>
            </div>
          )}

          {def && esPregunta(paso) && (
            <div class="enc-pregunta" key={paso}>
              <p class="kicker">{paso === "camino" ? "Antes de empezar" : `${avance.rotulo} · ${def.nombre}`}</p>
              <h1 class="titulo" ref={titulo} tabIndex={-1}>
                {def.pregunta}
              </h1>
              <p class="enc-ayuda">{def.ayuda}</p>
              <div class="enc-opciones" role="group" aria-label="Opciones de respuesta">
                {def.opciones.map((opcion, i) => (
                  <button
                    type="button"
                    class="opt"
                    key={opcion.id}
                    aria-pressed={respuestas[paso] === opcion.id}
                    aria-keyshortcuts={TECLAS[i]}
                    onClick={() => elegir(paso, opcion.id)}
                  >
                    <span class="tecla" aria-hidden="true">
                      {TECLAS[i]}
                    </span>
                    <span class="texto">
                      <span class="t">{opcion.titulo}</span>
                      {opcion.detalle && <span class="d">{opcion.detalle}</span>}
                    </span>
                    <Icono nombre="flecha" grosor={2.2} color="#1747C9" class="arr" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {paso === "zona" && (
            <div class="enc-pregunta" key="zona">
              <p class="kicker">{avance.rotulo} · Molestias</p>
              <h1 class="titulo" ref={titulo} tabIndex={-1}>
                ¿Dónde lo notas y cuándo?
              </h1>
              <fieldset class="enc-grupo">
                <legend>Zona de la molestia</legend>
                <div class="enc-chips">
                  {ZONAS.map((zona) => (
                    <button
                      type="button"
                      class="chip"
                      key={zona}
                      aria-pressed={salud.zona === zona}
                      onClick={() => setEstado({ ...estado, salud: { ...salud, zona } })}
                    >
                      {zona}
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset class="enc-grupo">
                <legend>Cuándo aparece</legend>
                <div class="enc-chips">
                  {MOMENTOS.map((momento) => (
                    <button
                      type="button"
                      class="chip"
                      key={momento}
                      aria-pressed={salud.momento === momento}
                      onClick={() => setEstado({ ...estado, salud: { ...salud, momento } })}
                    >
                      {textoMomento(momento, respuestas)}
                    </button>
                  ))}
                </div>
              </fieldset>
              <label class="enc-consentimiento">
                <input
                  type="checkbox"
                  checked={salud.consentimiento}
                  onChange={(e) =>
                    setEstado({ ...estado, salud: { ...salud, consentimiento: e.currentTarget.checked } })
                  }
                />
                <span>
                  Acepto que uséis este dato de salud solo para calcular mi recomendación. No se guarda en mi perfil
                  ni se comparte con las tiendas.
                </span>
              </label>
              <div>
                <button
                  type="button"
                  class="btn btn-azul enc-continuar"
                  disabled={!zonaLista}
                  onClick={() => zonaLista && avanzar("zona", respuestas, salud)}
                >
                  Continuar
                  <Icono nombre="flecha" tamano={20} grosor={2.4} class="arr" />
                </button>
              </div>
            </div>
          )}

          {paso === "mol" && (
            <p class="enc-salud">
              <Icono nombre="candado" tamano={20} color="#1747C9" />
              <span>
                Las molestias son un dato de salud. Las usamos solo para esta recomendación y no se guardan en tu
                perfil. Puedes no contestar.
              </span>
            </p>
          )}

          {paso === "fin" && (
            <div class="enc-pregunta fin" key="fin">
              <p class="kicker">Completado</p>
              <h1 class="titulo" ref={titulo} tabIndex={-1}>
                Listo. Ya sabemos qué buscar.
              </h1>
              <dl class="enc-resumen">
                {resumen(respuestas).map(({ clave, valor }) => (
                  <div key={clave}>
                    <dt>{clave}</dt>
                    <dd>{valor}</dd>
                  </div>
                ))}
              </dl>
              <div>
                <a class="btn btn-xl btn-azul" href={rutas.recomendacion}>
                  Ver mi recomendación
                  <Icono nombre="flecha" tamano={22} grosor={2.4} class="arr" />
                </a>
              </div>
            </div>
          )}

          {historial.length > 0 && (
            <div>
              <button type="button" class="enc-atras" onClick={retroceder}>
                <Icono nombre="atras" tamano={18} grosor={2.2} />
                Atrás
              </button>
            </div>
          )}
        </div>

        <PalaTomandoForma respuestas={respuestasRecorridas(respuestas, historial)} salud={salud} />
      </main>
    </>
  );
}

// --- Panel «Tu pala, tomando forma» -------------------------------------------

/** Altura de la cabeza, radios y posición del punto dulce para cada forma (en unidades del dibujo). */
const SILUETA: Record<Forma, { alto: number; radio: string; punto: number }> = {
  redonda: { alto: 240, radio: "50% 50% 50% 50% / 50% 50% 50% 50%", punto: 247 },
  lagrima: { alto: 262, radio: "50% 50% 50% 50% / 44% 44% 56% 56%", punto: 274 },
  diamante: { alto: 268, radio: "42% 42% 50% 50% / 28% 28% 72% 72%", punto: 304 },
};

/** Altura del cursor de balance para cada uno de los cinco niveles (de bajo a alto). */
const ALTURA_BALANCE: Record<BalanceFino, number> = { 0: 203, 1: 248.5, 2: 294, 3: 339.5, 4: 385 };

/** Diámetro del punto dulce: cuanto más grande, más perdona los golpes descentrados. */
const DIAMETRO_PUNTO: Record<PuntoDulce, number> = { grande: 60, medio: 46, pequeño: 34 };

const u = (unidades: number) => `calc(var(--u) * ${unidades})`;

function PalaTomandoForma({ respuestas, salud }: { respuestas: Respuestas; salud: Salud }) {
  const perfil = perfilOrientativo(respuestas, salud);
  // Mientras no se sabe la forma, se dibuja una lágrima con trazo discontinuo.
  const silueta = SILUETA[perfil.forma ?? "lagrima"];
  const balance = ALTURA_BALANCE[perfil.balance ?? 2];
  // El punto dulce crece o encoge sin moverse de su centro.
  const diametro = DIAMETRO_PUNTO[perfil.puntoDulce ?? "medio"];
  const centro = silueta.punto + DIAMETRO_PUNTO.medio / 2;

  return (
    <aside class="enc-pala" aria-label="Perfil de pala orientativo">
      <svg aria-hidden="true" viewBox="0 0 480 760" preserveAspectRatio="xMidYMid slice">
        <path d="M-10 130 L490 130" fill="none" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="2.5" />
      </svg>
      <div class="enc-pala-dentro">
        <p class="kicker">Tu pala, tomando forma</p>

        <div class="dibujo" aria-hidden="true">
          <div class="mango" />
          <div class="tapon" />
          <div
            class={perfil.forma ? "cabeza" : "cabeza sin-definir"}
            data-caras={perfil.caras ?? undefined}
            style={{ height: u(silueta.alto), borderRadius: silueta.radio }}
          >
            <div class="agujeros" />
          </div>
          <div class="puente" />
          <div
            class="punto-dulce"
            style={{
              width: u(diametro),
              height: u(diametro),
              left: u(115 - diametro / 2),
              bottom: u(centro - diametro / 2),
              opacity: perfil.forma ? 1 : 0,
            }}
          />
          <div class="eje" />
          <span class="marca" style={{ bottom: u(384) }}>
            ALTO
          </span>
          <span class="marca" style={{ bottom: u(293) }}>
            MEDIO
          </span>
          <span class="marca" style={{ bottom: u(202) }}>
            BAJO
          </span>
          <div class="cursor" style={{ bottom: u(balance), opacity: perfil.balance !== null ? 1 : 0.3 }} />
          <span class="marca titulo-eje">BALANCE</span>
        </div>

        <dl class="enc-datos">
          <div>
            <dt>Forma</dt>
            <dd>{perfil.forma ? textoForma[perfil.forma] : "—"}</dd>
          </div>
          <div>
            <dt>Balance</dt>
            <dd>{perfil.balance !== null ? TEXTO_BALANCE_FINO[perfil.balance] : "—"}</dd>
          </div>
          <div>
            <dt>Punto dulce</dt>
            <dd>{perfil.puntoDulce ? TEXTO_PUNTO_DULCE[perfil.puntoDulce] : "—"}</dd>
          </div>
          <div>
            <dt>Núcleo</dt>
            <dd>{perfil.nucleo ?? "—"}</dd>
          </div>
          <div>
            <dt>Peso</dt>
            <dd>{perfil.peso ?? "—"}</dd>
          </div>
          <div>
            <dt>Caras</dt>
            <dd>{perfil.caras ? TEXTO_CARAS[perfil.caras] : "—"}</dd>
          </div>
        </dl>
        <p class="enc-nota">
          Orientativo: se afina con cada respuesta. La recomendación final sale del catálogo real.
        </p>
      </div>
    </aside>
  );
}
