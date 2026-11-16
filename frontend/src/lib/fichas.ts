/** Textos y geometría que la ficha de una pala deriva de sus datos. */
import { type Pala, euros, eurosCortos, minimoHistorico, precioDesde, textoBalance } from "@/lib/catalogo";

// --- Preguntas frecuentes ----------------------------------------------------

export interface PreguntaFrecuente {
  pregunta: string;
  respuesta: string;
}

const FISIO = "Si el dolor sigue, consulta a un fisioterapeuta: una pala no sustituye a un tratamiento.";

function primeraPala(pala: Pala): PreguntaFrecuente {
  if (pala.junior) {
    return {
      pregunta: "¿Para qué edades es?",
      respuesta: `Para menores de 14 años. Es más corta y ligera que una pala de adulto (${pala.pesoMin}–${pala.pesoMax} g), para que puedan moverla sin forzar el brazo. A partir de los 14 años, o antes si ya tienen fuerza, conviene pasar a una pala de adulto ligera.`,
    };
  }
  const pregunta = "¿Sirve como primera pala?";
  const [nivelMin] = pala.nivel;
  if (nivelMin === 1 && pala.forma === "redonda") {
    return {
      pregunta,
      respuesta:
        "Sí. La forma redonda y el balance bajo dan un punto dulce amplio y una pala fácil de mover, que es lo que más ayuda mientras se aprende la técnica.",
    };
  }
  if (nivelMin === 1) {
    return {
      pregunta,
      respuesta:
        "Sí, sobre todo si ya has jugado algunas veces. Perdona algo menos que una redonda, pero a cambio no se te queda corta cuando empiezas a atacar.",
    };
  }
  if (nivelMin === 2) {
    return {
      pregunta,
      respuesta:
        "No es la mejor opción para empezar. Está pensada para quien ya lleva un tiempo jugando y golpea con cierta regularidad. Para los primeros meses, una redonda de balance bajo perdona más.",
    };
  }
  return {
    pregunta,
    respuesta:
      "No. Es una pala exigente, pensada para jugadores avanzados que golpean casi siempre en el centro. Si estás empezando, jugarás mejor y con menos riesgo para el brazo con una redonda de balance bajo.",
  };
}

function molestias(pala: Pala): PreguntaFrecuente {
  const pregunta = "¿Es buena idea si me duele el codo?";
  const balance = textoBalance[pala.balance].toLowerCase();

  if (pala.dureza <= 2 && pala.balance !== "alto") {
    return {
      pregunta,
      respuesta: `Un núcleo blando y un balance ${balance} transmiten menos vibración al brazo, y por eso suelen recomendarse cuando hay molestias. ${FISIO}`,
    };
  }
  if (pala.dureza === 3 && pala.balance !== "alto") {
    return {
      pregunta,
      respuesta: `Es una pala intermedia: no es de las que más cargan el brazo, pero hay opciones con el núcleo más blando. Si la molestia es habitual, mejor una de esas. ${FISIO}`,
    };
  }
  return {
    pregunta,
    respuesta: `No es la más indicada. ${
      pala.balance === "alto" ? "El balance alto hace más palanca sobre el brazo" : "Un núcleo firme transmite más vibración"
    }, y eso se nota si ya hay molestias. Busca una pala de núcleo blando y balance bajo o medio. ${FISIO}`,
  };
}

function diferencia(pala: Pala): PreguntaFrecuente {
  if (pala.junior) {
    return {
      pregunta: "¿En qué se diferencia de una pala de adulto?",
      respuesta:
        "Es más corta, tiene la cabeza más pequeña y pesa bastante menos. Con una pala de adulto, un niño llega tarde a la bola y carga el hombro y el codo.",
    };
  }
  switch (pala.forma) {
    case "redonda":
      return {
        pregunta: "¿En qué se diferencia de una pala de lágrima?",
        respuesta:
          "La lágrima sube el punto dulce y el balance: gana pegada y pierde algo de tolerancia. La redonda es más fácil de controlar y perdona más.",
      };
    case "lagrima":
      return {
        pregunta: "¿En qué se diferencia de una redonda y de un diamante?",
        respuesta:
          "Está a medio camino. Frente a una redonda, tiene el punto dulce algo más arriba y más pegada, y perdona un poco menos. Frente a un diamante, es más fácil de controlar y carga menos el brazo.",
      };
    case "diamante":
      return {
        pregunta: "¿En qué se diferencia de una pala de lágrima?",
        respuesta:
          "El diamante lleva el punto dulce y el peso más arriba: pega más fuerte en el remate, pero perdona menos y cuesta más moverlo en defensa. La lágrima es más equilibrada.",
      };
  }
}

export function preguntasFrecuentes(pala: Pala): PreguntaFrecuente[] {
  return [primeraPala(pala), molestias(pala), diferencia(pala)];
}

// --- Histórico de precio ------------------------------------------------------

const DIAS = 90;
/** Zona de dibujo dentro de un viewBox de 860 × 290. */
const X0 = 60;
const X1 = 840;
const Y_ARRIBA = 90;
const Y_BASE = 240;
const SALTO_Y = 50;

export interface GraficoPrecio {
  titular: string;
  descripcion: string;
  /** Marcas del eje de precios, de arriba abajo. */
  marcasY: { y: number; texto: string }[];
  linea: string;
  area: string;
  hoy: { x: number; y: number; texto: string };
  /** Punto del mínimo, si no coincide con el precio de hoy. */
  minimo: { x: number; y: number; texto: string; ancla: "start" | "middle" | "end" } | null;
}

/** Calcula el gráfico escalonado del precio más bajo de los últimos 90 días. */
export function graficoPrecio(pala: Pala): GraficoPrecio {
  const serie = pala.historico;
  const hoy = precioDesde(pala);
  const min = minimoHistorico(pala);
  const max = Math.max(...serie.map((p) => p.precio), hoy);
  const minPrecio = Math.min(min.precio, hoy);

  // Paso del eje: el más fino que deje el mínimo dentro de las tres líneas.
  const paso = [5, 10, 20, 25, 50, 100, 200].find((s) => {
    const techo = Math.ceil(max / s) * s;
    return minPrecio >= techo - 2 * s - s * 0.15;
  })!;
  const techo = Math.ceil(max / paso) * paso;

  const x = (hace: number) => Math.round((X0 + ((DIAS - hace) * (X1 - X0)) / DIAS) * 10) / 10;
  const y = (precio: number) => Math.round((Y_ARRIBA + ((techo - precio) * SALTO_Y) / paso) * 10) / 10;

  let linea = `M${X0} ${y(serie[0].precio)}`;
  for (const punto of serie.slice(1)) linea += ` H${x(punto.hace)} V${y(punto.precio)}`;
  linea += ` H${X1}`;
  if (serie[serie.length - 1].precio !== hoy) linea += ` V${y(hoy)}`;

  const diferenciaHoy = Math.round(hoy - min.precio);
  const enMinimo = hoy <= min.precio + 0.5;

  let minimo: GraficoPrecio["minimo"] = null;
  if (!enMinimo) {
    const i = serie.indexOf(min);
    const inicio = x(min.hace);
    const fin = i < serie.length - 1 ? x(serie[i + 1].hace) : X1;
    const centro = Math.round((inicio + fin) / 2);
    minimo = {
      x: centro,
      y: y(min.precio),
      texto: `Mínimo ${euros(min.precio)}`,
      ancla: centro < 130 ? "start" : centro > 700 ? "end" : "middle",
    };
  }

  const primero = serie[0].precio;
  return {
    titular: enMinimo
      ? "Hoy está en su precio más bajo de los últimos 90 días"
      : `Hoy está ${eurosCortos(Math.max(1, diferenciaHoy))} por encima de su mínimo`,
    descripcion:
      `Histórico de precio de los últimos 90 días: empezó en ${euros(primero)}` +
      (enMinimo
        ? ` y hoy está en ${euros(hoy)}, su precio más bajo del periodo.`
        : `, bajó a un mínimo de ${euros(min.precio)} hace unos ${min.hace} días y hoy está en ${euros(hoy)}.`),
    marcasY: [0, 1, 2].map((i) => ({ y: Y_ARRIBA + i * SALTO_Y, texto: String(techo - i * paso) })),
    linea,
    area: `${linea} V${Y_BASE} H${X0} Z`,
    hoy: { x: X1, y: y(hoy), texto: enMinimo ? `Hoy ${euros(hoy)} · mínimo` : `Hoy ${euros(hoy)}` },
    minimo,
  };
}
