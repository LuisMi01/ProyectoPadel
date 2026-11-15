/**
 * Formulario de acceso sin contraseña: pide el correo y la API envía un enlace.
 * Lo usan la página de acceso y la banda «Guarda esta recomendación».
 * Va siempre sobre fondo oscuro (.dk).
 */
import { useState } from "preact/hooks";

import Icono from "@/components/Icono";
import { ErrorApi, hayApi } from "@/lib/api";
import { pedirEnlace } from "@/lib/cuenta";

type Estado = { tipo: "inicial" } | { tipo: "enviando" } | { tipo: "enviado" } | { tipo: "error"; mensaje: string };

const CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface Props {
  /** Texto del botón. */
  boton?: string;
  /** Sufijo para que los id no choquen si hay dos formularios en la página. */
  idCampo?: string;
}

export default function FormularioAcceso({ boton = "Enviarme el enlace", idCampo = "correo" }: Props) {
  const [correo, setCorreo] = useState("");
  const [estado, setEstado] = useState<Estado>({ tipo: "inicial" });

  async function enviar(e: Event) {
    e.preventDefault();
    const direccion = correo.trim();
    if (!CORREO.test(direccion)) {
      setEstado({ tipo: "error", mensaje: "Escribe un correo válido, por ejemplo tu@correo.com." });
      return;
    }
    if (!hayApi) {
      setEstado({
        tipo: "error",
        mensaje:
          "El acceso por correo todavía no está activo. Mientras tanto, lo que guardes se queda en este navegador.",
      });
      return;
    }

    setEstado({ tipo: "enviando" });
    try {
      await pedirEnlace(direccion);
      setEstado({ tipo: "enviado" });
    } catch (error) {
      const invalido = error instanceof ErrorApi && error.estado === 422;
      setEstado({
        tipo: "error",
        mensaje: invalido
          ? "Ese correo no parece válido. Revísalo e inténtalo de nuevo."
          : "No hemos podido enviar el enlace. Inténtalo de nuevo en unos minutos.",
      });
    }
  }

  if (estado.tipo === "enviado") {
    return (
      <div class="acc-form pop" role="status">
        <p class="aviso-form ok acc-enviado">
          <Icono nombre="check" tamano={20} grosor={2.6} />
          <span>
            Te hemos enviado un enlace a <strong>{correo.trim()}</strong>. Ábrelo en este mismo navegador para
            entrar: caduca a los pocos minutos.
          </span>
        </p>
        <p class="acc-otra">
          <button type="button" class="lnk" onClick={() => setEstado({ tipo: "inicial" })}>
            Usar otro correo
          </button>
        </p>
      </div>
    );
  }

  const error = estado.tipo === "error" ? estado.mensaje : null;

  return (
    <form class="acc-form" onSubmit={enviar} noValidate>
      <label class="rotulo" for={idCampo}>
        Correo electrónico
      </label>
      <div class="acc-fila">
        <input
          id={idCampo}
          class="campo"
          type="email"
          name="email"
          autocomplete="email"
          placeholder="tu@correo.com"
          value={correo}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${idCampo}-error` : undefined}
          onInput={(e) => {
            setCorreo(e.currentTarget.value);
            if (error) setEstado({ tipo: "inicial" });
          }}
        />
        <button type="submit" class="btn btn-lima acc-boton" disabled={estado.tipo === "enviando"}>
          {estado.tipo === "enviando" ? "Enviando…" : boton}
        </button>
      </div>
      {error && (
        <p class="aviso-form error" id={`${idCampo}-error`} role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
