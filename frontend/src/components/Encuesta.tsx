/** Isla Preact: guía la encuesta paso a paso y guarda el progreso en el navegador. */
import { useEffect, useState } from "preact/hooks";

import {
  type Camino,
  type EstadoEncuesta,
  type Paso,
  type Respuestas,
  PRIMER_PASO,
  borrarProgreso,
  cargarProgreso,
  guardarPerfilFinal,
  guardarProgreso,
  recorrido,
  siguientePaso,
} from "@/lib/encuesta";
import { rutas } from "@/lib/rutas";

interface Props {
  camino: Camino;
}

const TITULOS: Record<Paso, string> = {
  experiencia: "¿Cuánto tiempo llevas jugando?",
  frecuencia: "¿Cuántas veces juegas por semana?",
  estilo: "¿Cómo juegas un punto?",
  molestias: "¿Tienes alguna molestia al jugar?",
  zona: "¿Dónde y cuándo notas la molestia?",
  edad: "¿Quién va a usar la pala?",
  presupuesto: "¿Cuánto quieres gastar como máximo?",
};

export default function Encuesta({ camino }: Props) {
  const [estado, setEstado] = useState<EstadoEncuesta>({
    camino,
    paso: PRIMER_PASO,
    respuestas: {},
  });
  const [guardado, setGuardado] = useState<EstadoEncuesta | null>(null);

  // "¿Respuestas guardadas?" -> ofrecer "Retomar encuesta".
  useEffect(() => {
    const previo = cargarProgreso();
    if (previo && previo.paso !== PRIMER_PASO) setGuardado(previo);
  }, []);

  const { paso, respuestas } = estado;
  const pasos = recorrido(respuestas);
  const indice = pasos.indexOf(paso);

  function responder(cambios: Partial<Respuestas>) {
    setEstado((e) => ({ ...e, respuestas: { ...e.respuestas, ...cambios } }));
  }

  function avanzar() {
    const siguiente = siguientePaso(paso, respuestas);
    if (siguiente === null) {
      guardarPerfilFinal(estado);
      borrarProgreso();
      window.location.href = rutas.recomendacion;
      return;
    }
    const nuevo = { ...estado, paso: siguiente };
    setEstado(nuevo);
    guardarProgreso(nuevo);
  }

  function retroceder() {
    if (indice > 0) setEstado({ ...estado, paso: pasos[indice - 1] });
  }

  if (guardado) {
    return (
      <div class="tarjeta">
        <p>Tienes una encuesta a medias. ¿Quieres seguir donde lo dejaste?</p>
        <div class="acciones">
          <button
            class="boton"
            onClick={() => {
              setEstado(guardado);
              setGuardado(null);
            }}
          >
            Retomar encuesta
          </button>
          <button
            class="boton secundario"
            onClick={() => {
              borrarProgreso();
              setGuardado(null);
            }}
          >
            Empezar de nuevo
          </button>
        </div>
      </div>
    );
  }

  return (
    <form
      class="tarjeta"
      onSubmit={(e) => {
        e.preventDefault();
        avanzar();
      }}
    >
      <p class="suave">
        Paso {indice + 1} de {pasos.length}
      </p>
      <progress max={pasos.length} value={indice + 1} />
      <h2>{TITULOS[paso]}</h2>

      <CamposPaso paso={paso} r={respuestas} responder={responder} />

      <div class="acciones">
        {indice > 0 && (
          <button type="button" class="boton secundario" onClick={retroceder}>
            Atrás
          </button>
        )}
        <button type="submit" class="boton" disabled={!pasoCompleto(paso, respuestas)}>
          {siguientePaso(paso, respuestas) === null ? "Ver recomendación" : "Siguiente"}
        </button>
      </div>
    </form>
  );
}

function pasoCompleto(paso: Paso, r: Respuestas): boolean {
  switch (paso) {
    case "experiencia":
      return r.experiencia_meses !== undefined;
    case "frecuencia":
      return r.frecuencia_semanal !== undefined;
    case "estilo":
      return r.estilo !== undefined;
    case "molestias":
      return r.molestias !== undefined;
    case "zona":
      return r.zona_molestia !== undefined && r.momento_molestia !== undefined;
    case "edad":
      return r.junior !== undefined;
    case "presupuesto":
      return (r.presupuesto_max ?? 0) > 0;
  }
}

interface Opcion<T> {
  valor: T;
  texto: string;
}

function Opciones<T>(props: {
  nombre: string;
  opciones: Opcion<T>[];
  actual: T | undefined;
  elegir: (v: T) => void;
}) {
  return (
    <fieldset>
      {props.opciones.map((o) => (
        <label key={String(o.valor)}>
          <input
            type="radio"
            name={props.nombre}
            checked={props.actual === o.valor}
            onChange={() => props.elegir(o.valor)}
          />{" "}
          {o.texto}
        </label>
      ))}
    </fieldset>
  );
}

function CamposPaso({
  paso,
  r,
  responder,
}: {
  paso: Paso;
  r: Respuestas;
  responder: (c: Partial<Respuestas>) => void;
}) {
  switch (paso) {
    case "experiencia":
      return (
        <Opciones
          nombre="experiencia"
          actual={r.experiencia_meses}
          elegir={(v) => responder({ experiencia_meses: v })}
          opciones={[
            { valor: 0, texto: "Estoy empezando" },
            { valor: 3, texto: "Menos de 6 meses" },
            { valor: 12, texto: "Entre 6 meses y 2 años" },
            { valor: 36, texto: "Más de 2 años" },
          ]}
        />
      );
    case "frecuencia":
      return (
        <Opciones
          nombre="frecuencia"
          actual={r.frecuencia_semanal}
          elegir={(v) => responder({ frecuencia_semanal: v })}
          opciones={[
            { valor: 1, texto: "1 vez" },
            { valor: 2, texto: "2–3 veces" },
            { valor: 4, texto: "4 o más" },
          ]}
        />
      );
    case "estilo":
      return (
        <Opciones<NonNullable<Respuestas["estilo"]>>
          nombre="estilo"
          actual={r.estilo}
          elegir={(v) => responder({ estilo: v })}
          opciones={[
            { valor: "defensivo", texto: "Defiendo y espero el error" },
            { valor: "polivalente", texto: "Un poco de todo" },
            { valor: "ofensivo", texto: "Busco rematar" },
          ]}
        />
      );
    case "molestias":
      return (
        <Opciones
          nombre="molestias"
          actual={r.molestias}
          elegir={(v) =>
            responder(
              v ? { molestias: v } : { molestias: v, zona_molestia: undefined, momento_molestia: undefined },
            )
          }
          opciones={[
            { valor: false, texto: "No, juego cómodo" },
            { valor: true, texto: "Sí, alguna molestia" },
          ]}
        />
      );
    case "zona":
      return (
        <>
          <Opciones<NonNullable<Respuestas["zona_molestia"]>>
            nombre="zona"
            actual={r.zona_molestia}
            elegir={(v) => responder({ zona_molestia: v })}
            opciones={[
              { valor: "codo", texto: "Codo" },
              { valor: "hombro", texto: "Hombro" },
              { valor: "muneca", texto: "Muñeca" },
            ]}
          />
          <Opciones<NonNullable<Respuestas["momento_molestia"]>>
            nombre="momento"
            actual={r.momento_molestia}
            elegir={(v) => responder({ momento_molestia: v })}
            opciones={[
              { valor: "durante", texto: "Mientras juego" },
              { valor: "despues", texto: "Después de jugar" },
            ]}
          />
        </>
      );
    case "edad":
      return (
        <Opciones
          nombre="edad"
          actual={r.junior}
          elegir={(v) => responder({ junior: v })}
          opciones={[
            { valor: false, texto: "Adulto (14 años o más)" },
            { valor: true, texto: "Junior (menos de 14)" },
          ]}
        />
      );
    case "presupuesto":
      return (
        <label>
          Presupuesto máximo (€){" "}
          <input
            type="number"
            min={20}
            step={10}
            value={r.presupuesto_max ?? ""}
            onInput={(e) => responder({ presupuesto_max: Number(e.currentTarget.value) })}
          />
        </label>
      );
  }
}
