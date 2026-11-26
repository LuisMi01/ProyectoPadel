/**
 * Isla Preact de la recomendación: calcula el resultado a partir de las
 * respuestas del cuestionario y lo muestra con sus ofertas y alternativas.
 * Si hay API, la registra (sin molestias), pinta la explicación con IA y los
 * botones de tienda llevan el id para que el clic cuente para esta recomendación.
 */
import { useEffect, useState } from "preact/hooks";

import { AvisoEnLinea } from "@/components/AvisoPrecio";
import FormularioAcceso from "@/components/FormularioAcceso";
import { AvisoGuardada, BotonGuardar } from "@/components/GuardarPala";
import Icono from "@/components/Icono";
import { PalaGrande, Silueta, descripcionForma } from "@/components/dibujos";
import { useGuardado } from "@/components/ganchos";
import { nombreTienda, palas } from "@/data/catalogo";
import { hayApi, post } from "@/lib/api";
import {
  type Oferta,
  type Pala,
  euros,
  eurosCortos,
  formaEnFrase,
  mejorOferta,
  ofertasOrdenadas,
  precioDesde,
  textoBalance,
  textoDisponibilidad,
  textoNucleo,
} from "@/lib/catalogo";
import {
  type Voto,
  entradaHistorial,
  historial,
  registrarRecomendacion,
  sesionRecordada,
  votar,
} from "@/lib/cuenta";
import { type Respuestas, type Salud, etiquetas, leerFinal, tope } from "@/lib/encuesta";
import { type Alternativa, type Recomendacion as Resultado, recomendar } from "@/lib/recomendador";
import { rutas } from "@/lib/rutas";
import { type OrigenExplicacion, explicacionEnFlujo, registrarEnServidor } from "@/lib/servidor";

type Estado =
  | { tipo: "cargando" }
  | { tipo: "sin-respuestas" }
  | { tipo: "sin-resultados"; respuestas: Respuestas }
  | {
      tipo: "ok";
      id: string;
      respuestas: Respuestas;
      resultado: Resultado;
      /** Fecha de la recomendación si viene del historial (calculada sin el dato de molestias). */
      guardadaEl: string | null;
    };

/** Decide de dónde salen las respuestas: historial (?h=), el cuestionario recién hecho o la última guardada. */
function cargar(): Estado {
  const pedida = new URLSearchParams(location.search).get("h");
  const final = leerFinal();

  let id: string;
  let respuestas: Respuestas;
  let salud: Salud | null;
  let guardadaEl: string | null;

  const delHistorial = pedida ? entradaHistorial(pedida) : undefined;
  if (delHistorial && delHistorial.id !== final?.id) {
    ({ id, respuestas } = delHistorial);
    salud = null;
    guardadaEl = delHistorial.fecha;
  } else if (final) {
    ({ id, respuestas, salud } = final);
    guardadaEl = null;
  } else {
    const ultima = historial()[0];
    if (!ultima) return { tipo: "sin-respuestas" };
    ({ id, respuestas } = ultima);
    salud = null;
    guardadaEl = ultima.fecha;
  }

  const resultado = recomendar(respuestas, salud, palas);
  if (!resultado) return { tipo: "sin-resultados", respuestas };

  if (!guardadaEl) {
    registrarRecomendacion({
      id,
      fecha: final?.fecha ?? new Date().toISOString(),
      respuestas,
      palas: [resultado.mejor, ...resultado.alternativas.map((a) => a.pala)].map((p) => p.slug),
    });
  }
  return { tipo: "ok", id, respuestas, resultado, guardadaEl };
}

function fechaLarga(iso: string): string {
  return new Date(iso).toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" });
}

export default function Recomendacion() {
  const [estado, setEstado] = useState<Estado>({ tipo: "cargando" });

  useEffect(() => setEstado(cargar()), []);

  switch (estado.tipo) {
    case "cargando":
      return <main id="contenido" class="contenedor rec-main" aria-busy="true" />;

    case "sin-respuestas":
      return (
        <main id="contenido" class="contenedor rec-main">
          <section class="rec-vacio s1">
            <h1 class="titulo t-pagina">Todavía no has hecho el cuestionario.</h1>
            <p>Son 6 preguntas sobre cómo juegas. Al terminar te decimos qué pala te conviene y por qué.</p>
            <div class="acciones">
              <a class="btn btn-xl btn-azul" href={rutas.encuesta}>
                Empezar el cuestionario
              </a>
              <a class="lnk lnk-azul lnk-alto" href={rutas.palas}>
                Ver todas las palas
              </a>
            </div>
          </section>
        </main>
      );

    case "sin-resultados": {
      const limite = tope(estado.respuestas);
      return (
        <main id="contenido" class="contenedor rec-main">
          <section class="rec-vacio s1">
            <h1 class="titulo t-pagina">No hay ninguna pala que cumpla todo lo que pides.</h1>
            <p>
              {limite === Infinity
                ? "Hoy no queda ninguna pala disponible en el catálogo para ese perfil."
                : `Con un tope de ${eurosCortos(limite)} hoy no queda ninguna pala disponible para ese perfil. Prueba a subir el presupuesto.`}
            </p>
            <div class="acciones">
              <a class="btn btn-xl btn-azul" href={rutas.encuestaEditar}>
                Cambiar respuestas
              </a>
              <a class="lnk lnk-azul lnk-alto" href={rutas.palas}>
                Ver todas las palas
              </a>
            </div>
          </section>
        </main>
      );
    }

    case "ok":
      return <Resultados {...estado} />;
  }
}

// --- Resultado ----------------------------------------------------------------

function Resultados({
  id,
  respuestas,
  resultado,
  guardadaEl,
}: {
  id: string;
  respuestas: Respuestas;
  resultado: Resultado;
  guardadaEl: string | null;
}) {
  const { mejor, motivos, alternativas, nota, titular } = resultado;
  const [avisoAbierto, setAvisoAbierto] = useState(false);
  const precio = precioDesde(mejor);
  // Id en la API. Solo se registra la recomendación recién hecha, no la que se vuelve a ver del historial.
  const [recId, setRecId] = useState<number | null>(null);

  useEffect(() => {
    if (guardadaEl || !hayApi) return;
    let vigente = true;
    const ids = [mejor.id, ...alternativas.map((a) => a.pala.id)];
    registrarEnServidor(id, respuestas, ids).then((nuevo) => vigente && setRecId(nuevo));
    return () => {
      vigente = false;
    };
  }, [id]);

  return (
    <main id="contenido" class="contenedor rec-main">
      <section class="rec-cabeza s1">
        <h1 class="titulo t-pagina">{titular}</h1>
        <div class="rec-respuestas">
          <ul aria-label="Tus respuestas">
            {etiquetas(respuestas).map((texto) => (
              <li key={texto}>{texto}</li>
            ))}
          </ul>
          <a class="lnk lnk-azul lnk-alto" href={guardadaEl ? rutas.encuesta : rutas.encuestaEditar}>
            {guardadaEl ? "Repetir el cuestionario" : "Cambiar respuestas"}
          </a>
        </div>
        {guardadaEl && (
          <p class="rec-info">
            <Icono nombre="reloj" tamano={20} color="var(--azul)" />
            <span>
              Recomendación del {fechaLarga(guardadaEl)}, recalculada con los precios de hoy y sin el dato de
              molestias, que no guardamos.
            </span>
          </p>
        )}
        <p class="rec-info">
          <Icono nombre="info" tamano={20} color="var(--azul)" />
          <span>
            Los botones «Ir a la tienda» son enlaces de afiliado: si compras, la tienda nos paga una comisión. A ti
            te cuesta lo mismo y no cambia el orden de esta lista.{" "}
            <a class="lnk lnk-azul" href={rutas.comoGanamosDinero}>
              Cómo ganamos dinero
            </a>
          </span>
        </p>
      </section>

      <article class="rec-mejor s2" aria-labelledby="rec1">
        <div class="rec-panel dk">
          <svg class="linea" aria-hidden="true" viewBox="0 0 440 720" preserveAspectRatio="xMidYMid slice">
            <path d="M-10 250 L450 250" fill="none" stroke-opacity="0.2" stroke-width="2.5" style="stroke: var(--blanco)" />
          </svg>
          <p class="rec-puesto">
            <span class="n">01</span>
            <span>Mejor encaje</span>
          </p>
          <PalaGrande
            class="pala"
            forma={mejor.forma}
            uid="mejor"
            etiqueta={`Pala de ${descripcionForma(mejor.forma)}`}
          />
          <dl class="rec-barras">
            <Barra nombre="Control" valor={mejor.control} retraso={0.6} />
            <Barra nombre="Tolerancia al fallo" valor={mejor.tolerancia} retraso={0.75} />
            <Barra nombre="Potencia" valor={mejor.potencia} retraso={0.9} />
          </dl>
        </div>

        <div class="rec-detalle">
          <div class="rec-nombre">
            <span class="etiqueta">{mejor.marca}</span>
            <h2 id="rec1" class="titulo">
              {mejor.nombre}
            </h2>
            <ul class="rec-rasgos" aria-label="Características">
              <li class="pastilla">Forma {formaEnFrase(mejor.forma)}</li>
              <li class="pastilla">Balance {textoBalance[mejor.balance].toLowerCase()}</li>
              <li class="pastilla">{mejor.peso} g</li>
              <li class="pastilla">{textoNucleo(mejor)}</li>
            </ul>
          </div>

          <div class="rec-porque">
            <h3 class="subtitulo">Por qué esta pala</h3>
            <ul>
              {motivos.map(({ respuesta, explicacion }) => (
                <li key={respuesta}>
                  <span class="respuesta">{respuesta}</span>
                  <span class="explicacion">{explicacion}</span>
                </li>
              ))}
            </ul>
            {nota && (
              <p class="rec-nota">
                <Icono nombre="info" tamano={18} color="var(--azul)" />
                <span>{nota}</span>
              </p>
            )}
            {recId !== null && <Explicacion recomendacion={recId} />}
          </div>

          <Ofertas pala={mejor} recomendacion={recId} />

          <div class="rec-acciones">
            <div class="rec-botones">
              <BotonGuardar slug={mejor.slug} />
              <button
                type="button"
                class="btn btn-m btn-contorno"
                aria-expanded={avisoAbierto}
                aria-controls="aviso-mejor"
                onClick={() => setAvisoAbierto(!avisoAbierto)}
              >
                <Icono nombre="campana" tamano={18} />
                Avisarme si baja
              </button>
              <a class="lnk lnk-azul lnk-alto" href={rutas.pala(mejor.slug)}>
                Ver ficha completa
              </a>
            </div>
            <AvisoGuardada slug={mejor.slug} />
            <div id="aviso-mejor">{avisoAbierto && <AvisoEnLinea slug={mejor.slug} precioActual={precio} />}</div>
          </div>
        </div>
      </article>

      {alternativas.length > 0 && (
        <section class="rec-otras s3">
          <h2 class="titulo t-bloque">
            {alternativas.length === 1 ? "Otra que también encaja" : "Otras dos que también encajan"}
          </h2>
          <div class="rec-rejilla">
            {alternativas.map((alt, i) => (
              <TarjetaAlternativa key={alt.pala.slug} alt={alt} puesto={i + 2} recomendacion={recId} />
            ))}
          </div>
        </section>
      )}

      <GuardarRecomendacion />
      <Valoracion id={id} recomendacion={recId} />
    </main>
  );
}

/** Explicación en pocas palabras, según la IA la va escribiendo. Si la API falla, no se muestra. */
function Explicacion({ recomendacion }: { recomendacion: number }) {
  const [texto, setTexto] = useState("");
  const [origen, setOrigen] = useState<OrigenExplicacion | null>(null);
  const [fallo, setFallo] = useState(false);

  useEffect(() => {
    const control = new AbortController();
    explicacionEnFlujo(
      recomendacion,
      {
        alEscribir: setTexto,
        alTerminar: (definitivo, de) => {
          setTexto(definitivo);
          setOrigen(de);
        },
      },
      control.signal,
    ).catch(() => {
      if (!control.signal.aborted) setFallo(true);
    });
    return () => control.abort();
  }, [recomendacion]);

  if (fallo) return null;
  // Mientras llega por trozos solo puede ser de la IA; al final, «fin» dice de dónde sale.
  const conIa = origen === null ? texto !== "" : origen === "ia" || origen === "cache";
  return (
    <div class="rec-ia" aria-busy={origen === null}>
      <h3 class="subtitulo">En pocas palabras</h3>
      {texto ? <p>{texto}</p> : <p class="cargando">Preparando la explicación…</p>}
      {conIa && (
        <p class="aviso">
          <Icono nombre="info" tamano={16} color="var(--azul)" />
          <span>Texto redactado con IA a partir de los datos de las palas.</span>
        </p>
      )}
    </div>
  );
}

function Barra({ nombre, valor, retraso }: { nombre: string; valor: number; retraso: number }) {
  return (
    <div>
      <div class="fila">
        <dt>{nombre}</dt>
        <dd>{valor} / 5</dd>
      </div>
      <div class="pista" aria-hidden="true">
        <div class="fill" style={{ width: `${valor * 20}%`, animationDelay: `${retraso}s` }} />
      </div>
    </div>
  );
}

/** Caja de ofertas: la mejor destacada y el resto en filas. */
function Ofertas({ pala, recomendacion }: { pala: Pala; recomendacion: number | null }) {
  const mejor = mejorOferta(pala);
  const resto = ofertasOrdenadas(pala).filter((o) => o !== mejor);
  const salida = { origen: "recomendacion", posicion: 1, recomendacion } as const;

  return (
    <div class="ofertas" id="ofertas">
      {mejor && (
        <div class="oferta-mejor">
          <div class="datos">
            <span class="tienda">
              {nombreTienda(mejor.tienda)}
              <span class="distintivo">Mejor precio hoy</span>
            </span>
            <span class="precio">{euros(mejor.precio)}</span>
            <span class="estado">{textoDisponibilidad[mejor.disponibilidad]} · precios revisados a diario</span>
          </div>
          <a
            class="btn btn-l btn-azul"
            href={rutas.tienda(mejor.id, salida)}
            rel="sponsored nofollow noopener"
            aria-label={`Ir a la tienda ${nombreTienda(mejor.tienda)}, enlace de afiliado`}
          >
            Ir a la tienda
            <Icono nombre="salida" tamano={20} grosor={2.4} class="arr" />
          </a>
        </div>
      )}
      {resto.map((oferta) => (
        <FilaOferta key={oferta.id} oferta={oferta} href={rutas.tienda(oferta.id, salida)} />
      ))}
    </div>
  );
}

function FilaOferta({ oferta, href }: { oferta: Oferta; href: string }) {
  const tienda = nombreTienda(oferta.tienda);
  const contenido = (
    <>
      <span class="nombre">{tienda}</span>
      <span class="lado">
        <span class="estado">{textoDisponibilidad[oferta.disponibilidad]}</span>
        <span class="precio">{euros(oferta.precio)}</span>
        {oferta.disponibilidad !== "agotada" && <Icono nombre="salida" tamano={16} grosor={2.4} color="var(--azul)" />}
      </span>
    </>
  );

  if (oferta.disponibilidad === "agotada") return <div class="ofr agotada">{contenido}</div>;
  return (
    <a
      class="ofr"
      href={href}
      rel="sponsored nofollow noopener"
      aria-label={`Ir a la tienda ${tienda}, ${euros(oferta.precio)}, enlace de afiliado`}
    >
      {contenido}
    </a>
  );
}

function TarjetaAlternativa({
  alt,
  puesto,
  recomendacion,
}: {
  alt: Alternativa;
  puesto: number;
  recomendacion: number | null;
}) {
  const { pala, etiqueta, ganas, pierdes } = alt;
  const oferta = mejorOferta(pala);

  return (
    <article class="alt card">
      <div class="alt-cabeza">
        <div class="alt-titulo">
          <span class="alt-etiqueta">
            <span class="n">{String(puesto).padStart(2, "0")}</span>
            <span>{etiqueta}</span>
          </span>
          <span class="etiqueta">{pala.marca}</span>
          <h3 class="titulo">{pala.nombre}</h3>
        </div>
        <Silueta forma={pala.forma} ancho={84} />
      </div>
      <dl>
        <div>
          <dt>Ganas</dt>
          <dd>{ganas}</dd>
        </div>
        <div>
          <dt>Pierdes</dt>
          <dd>{pierdes}</dd>
        </div>
      </dl>
      <div class="alt-pie">
        <span class="alt-precio">
          <span class="desde">desde</span>
          <span class="valor">{euros(precioDesde(pala))}</span>
        </span>
        <span class="alt-enlaces">
          <a class="lnk lnk-azul lnk-alto" href={rutas.pala(pala.slug)} aria-label={`Ver ficha de ${pala.nombre}`}>
            Ver ficha
          </a>
          {oferta && (
            <a
              class="btn btn-m btn-tinta"
              href={rutas.tienda(oferta.id, { origen: "recomendacion", posicion: puesto, recomendacion })}
              rel="sponsored nofollow noopener"
              aria-label={`Ir a la tienda ${nombreTienda(oferta.tienda)} para ${pala.nombre}, enlace de afiliado`}
            >
              Ir a la tienda
              <Icono nombre="salida" tamano={18} grosor={2.4} class="arr" />
            </a>
          )}
        </span>
      </div>
    </article>
  );
}

/** Banda oscura: pedir el enlace de acceso o, si ya hay sesión, ir al historial. */
function GuardarRecomendacion() {
  const conSesion = useGuardado(() => sesionRecordada() !== null, false);

  if (conSesion) {
    return (
      <section id="guardar" class="rec-guardar dk s4">
        <div class="texto">
          <h2 class="titulo">Esta recomendación está en tu historial</h2>
          <p>Puedes volver a ella cuando quieras desde tu cuenta, con los precios al día.</p>
        </div>
        <div class="lado">
          <a class="btn btn-l btn-lima" href={rutas.historial}>
            Ver mi historial
          </a>
        </div>
      </section>
    );
  }

  return (
    <section id="guardar" class="rec-guardar dk s4">
      <div class="texto">
        <h2 class="titulo">Guarda esta recomendación</h2>
        <p>
          Te enviamos un enlace de acceso al correo, sin contraseña. Guardamos tus respuestas sin el dato de
          molestias.
        </p>
      </div>
      <FormularioAcceso />
    </section>
  );
}

function Valoracion({ id, recomendacion }: { id: string; recomendacion: number | null }) {
  const [voto, setVoto] = useState<Voto | null>(null);

  useEffect(() => setVoto(entradaHistorial(id)?.voto ?? null), [id]);

  function elegir(nuevo: Voto) {
    setVoto(nuevo);
    votar(id, nuevo);
    // La valoración también se envía a la API, sin bloquear ni molestar si no responde.
    if (hayApi) {
      post("/eventos", { tipo: "recomendacion_valorada", datos: { util: nuevo === "si" } }).catch(() => {});
    }
    // Y, si está registrada, unida a esta recomendación (la API puntúa de 1 a 5).
    if (recomendacion !== null) {
      const puntuacion = nuevo === "si" ? 5 : 2;
      post(`/recomendaciones/${recomendacion}/valoracion`, { puntuacion }).catch(() => {});
    }
  }

  return (
    <section class="rec-voto s4">
      <h2 class="subtitulo">¿Te ha servido esta recomendación?</h2>
      {voto === null ? (
        <div class="botones">
          <button type="button" class="btn btn-m btn-contorno" onClick={() => elegir("si")}>
            Sí
          </button>
          <button type="button" class="btn btn-m btn-contorno" onClick={() => elegir("no")}>
            No del todo
          </button>
        </div>
      ) : (
        <p class="gracias pop" role="status">
          <Icono nombre="check" tamano={20} grosor={2.6} />
          Gracias. Lo usamos para afinar el recomendador.
        </p>
      )}
    </section>
  );
}
