/** Isla de /acceso/verificar/: canjea el token del enlace por una sesión. */
import { useEffect, useState } from "preact/hooks";

import { ErrorApi } from "@/lib/api";
import { verificarEnlace } from "@/lib/cuenta";
import { rutas } from "@/lib/rutas";

type Fallo = "sin-token" | "caducado" | "sin-conexion";
type Estado = "verificando" | "dentro" | Fallo;

const TEXTOS: Record<Fallo, { titulo: string; texto: string }> = {
  "sin-token": {
    titulo: "A este enlace le falta algo.",
    texto: "Parece que el enlace está incompleto. Ábrelo de nuevo desde el correo o pide otro.",
  },
  caducado: {
    titulo: "Este enlace ya no sirve.",
    texto:
      "Los enlaces de acceso caducan a los pocos minutos y solo se pueden usar una vez. Pide otro y entra al momento.",
  },
  "sin-conexion": {
    titulo: "No hemos podido comprobar el enlace.",
    texto: "No hay conexión con el servidor ahora mismo. Vuelve a abrir el enlace dentro de unos minutos.",
  },
};

export default function VerificarAcceso() {
  const [estado, setEstado] = useState<Estado>("verificando");

  useEffect(() => {
    const token = new URLSearchParams(location.search).get("token");
    if (!token) {
      setEstado("sin-token");
      return;
    }
    verificarEnlace(token)
      .then(() => {
        setEstado("dentro");
        location.replace(rutas.cuenta);
      })
      .catch((e: unknown) => setEstado(e instanceof ErrorApi && !e.sinConexion ? "caducado" : "sin-conexion"));
  }, []);

  if (estado === "verificando" || estado === "dentro") {
    return (
      <div class="verificar" role="status">
        <h1 class="titulo">{estado === "dentro" ? "Ya estás dentro." : "Comprobando tu enlace…"}</h1>
        <p class="lead">
          {estado === "dentro" ? "Te llevamos a tu cuenta." : "Es solo un momento. No cierres esta pestaña."}
        </p>
      </div>
    );
  }

  const { titulo, texto } = TEXTOS[estado];
  return (
    <div class="verificar" role="alert">
      <h1 class="titulo">{titulo}</h1>
      <p class="lead">{texto}</p>
      <div class="acciones">
        <a class="btn btn-l btn-azul" href={rutas.acceso}>
          Pedir otro enlace
        </a>
        <a class="lnk lnk-azul lnk-alto" href={rutas.inicio}>
          Volver al inicio
        </a>
      </div>
    </div>
  );
}
