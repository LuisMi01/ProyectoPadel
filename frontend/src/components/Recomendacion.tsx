/** Isla Preact: envía el perfil de la encuesta a la API y muestra el resultado. */
import { useEffect, useState } from "preact/hooks";

import { ErrorApi, post } from "@/lib/api";
import { leerPerfilFinal } from "@/lib/encuesta";
import { rutas } from "@/lib/rutas";

interface ModeloRecomendado {
  modelo_id: number;
  posicion: number;
  nombre: string;
}

interface RecomendacionOut {
  id: number;
  modelos: ModeloRecomendado[];
}

type Estado =
  | { tipo: "sin-perfil" }
  | { tipo: "cargando" }
  | { tipo: "ok"; datos: RecomendacionOut }
  | { tipo: "error"; mensaje: string };

export default function Recomendacion() {
  const [estado, setEstado] = useState<Estado>({ tipo: "cargando" });

  useEffect(() => {
    const perfil = leerPerfilFinal();
    if (!perfil) {
      setEstado({ tipo: "sin-perfil" });
      return;
    }
    post<RecomendacionOut>("/recomendaciones", perfil)
      .then((datos) => setEstado({ tipo: "ok", datos }))
      .catch((e: unknown) =>
        setEstado({
          tipo: "error",
          mensaje:
            e instanceof ErrorApi && e.estado === 501
              ? "El motor de recomendación aún está en construcción."
              : "No hemos podido conectar con el servidor. Inténtalo más tarde.",
        }),
      );
  }, []);

  switch (estado.tipo) {
    case "sin-perfil":
      return (
        <p class="aviso">
          Aún no has hecho la encuesta. <a href={rutas.encuesta}>Empieza aquí</a>.
        </p>
      );
    case "cargando":
      return <p class="suave">Buscando tus palas…</p>;
    case "error":
      return <p class="aviso">{estado.mensaje}</p>;
    case "ok":
      return (
        <ol class="rejilla">
          {estado.datos.modelos.map((m) => (
            <li key={m.modelo_id} class="tarjeta">
              <strong>#{m.posicion}</strong> {m.nombre}
            </li>
          ))}
        </ol>
      );
  }
}
