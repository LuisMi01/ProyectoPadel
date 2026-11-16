/**
 * Textos de transparencia y legales.
 *
 * PROVISIONALES: describen cómo funciona la web hoy (todo se calcula y se
 * guarda en el navegador; la API solo interviene en el acceso por correo).
 * Hay que revisarlos con asesoría legal y completar los datos del titular en
 * lib/sitio.ts antes de publicar, y actualizarlos cuando cambie el tratamiento
 * de datos (p. ej. cuando la recomendación se calcule en el servidor).
 */
import type { Bloque } from "@/data/guias";
import { sitio } from "@/lib/sitio";

export interface PaginaTexto {
  slug: string;
  /** Nombre corto para migas y navegación. */
  kicker: string;
  titulo: string;
  resumen: string;
  bloques: Bloque[];
}

/** Mientras sea true, las páginas legales avisan de que el texto es provisional. */
export const LEGAL_PROVISIONAL = true;

export const comoGanamosDinero: PaginaTexto = {
  slug: "como-ganamos-dinero",
  kicker: "Cómo ganamos dinero",
  titulo: "No vendemos palas. Así ganamos dinero.",
  resumen:
    "Si compras en una tienda a la que has llegado desde aquí, la tienda nos paga una comisión. A ti te cuesta lo mismo, y la comisión no decide qué pala te recomendamos.",
  bloques: [
    { tipo: "h2", texto: "De dónde sale el dinero" },
    {
      tipo: "p",
      texto:
        "Los botones «Ir a la tienda» son enlaces de afiliado. Cuando pulsas uno y acabas comprando, la tienda sabe que llegaste desde palaideal y nos paga un porcentaje de la venta. Ese porcentaje sale del margen de la tienda: el precio que pagas es el mismo que si hubieras entrado por tu cuenta.",
    },
    {
      tipo: "p",
      texto:
        "Es nuestra única fuente de ingresos. No vendemos palas, no cobramos a las marcas por aparecer y no mostramos publicidad.",
    },
    { tipo: "h2", texto: "Qué decide la recomendación" },
    {
      tipo: "p",
      texto:
        "La recomendación sale de tus respuestas y de las características de cada pala: forma, balance, dureza del núcleo, peso, nivel para el que está pensada y tu tope de gasto. La comisión que nos paga cada tienda no es un criterio y no interviene en el cálculo.",
    },
    {
      tipo: "definiciones",
      elementos: [
        {
          termino: "Qué pala sale primero",
          texto: "La que mejor encaja con tus respuestas dentro de tu presupuesto. Nada más.",
        },
        {
          termino: "Qué tienda sale primero",
          texto: "La que tiene hoy el precio más bajo y la pala disponible.",
        },
        {
          termino: "Qué palas aparecen",
          texto: "Las del catálogo, tengan o no una tienda afiliada que las venda.",
        },
      ],
    },
    { tipo: "h2", texto: "Lo que no hacemos" },
    {
      tipo: "lista",
      elementos: [
        "No cobramos a marcas ni a tiendas por subir puestos.",
        "No ocultamos una tienda más barata porque pague menos comisión.",
        "No vendemos ni cedemos tus datos.",
        "No te enviamos publicidad: solo los avisos de precio que tú crees.",
      ],
    },
    { tipo: "h2", texto: "Lo que conviene que sepas" },
    {
      tipo: "lista",
      elementos: [
        "Solo comparamos las tiendas que tenemos conectadas. Puede haber otras con mejor precio.",
        "Revisamos los precios a diario, pero pueden cambiar entre una revisión y otra. El precio válido es siempre el que ves en la tienda.",
        "La compra, el envío, la garantía y las devoluciones son con la tienda, no con nosotros.",
        "El cuestionario orienta, pero no sustituye a probar la pala ni al consejo de un monitor o de un fisioterapeuta.",
      ],
    },
  ],
};

export const paginasLegales: PaginaTexto[] = [
  {
    slug: "afiliacion",
    kicker: "Política de afiliación",
    titulo: "Política de afiliación",
    resumen:
      "Qué es un enlace de afiliado, cómo reconocerlo en esta web y qué relación tenemos con las tiendas a las que enlazamos.",
    bloques: [
      { tipo: "h2", texto: "Qué es un enlace de afiliado" },
      {
        tipo: "p",
        texto: `Es un enlace a una tienda que incluye un identificador de ${sitio.nombre}. Si compras después de pulsarlo, la tienda nos atribuye la venta y nos paga una comisión. El precio para ti no cambia.`,
      },
      { tipo: "h2", texto: "Cómo reconocerlos" },
      {
        tipo: "lista",
        elementos: [
          "Todos los botones y enlaces «Ir a la tienda» son de afiliado.",
          "Lo indicamos junto a los precios, en la recomendación y en cada ficha.",
          "En el código de la página van marcados como enlaces patrocinados (rel=\"sponsored\").",
        ],
      },
      { tipo: "h2", texto: "Con quién trabajamos" },
      {
        tipo: "p",
        texto:
          "Trabajamos con tiendas de pádel, directamente o a través de redes de afiliación. Publicaremos aquí la lista de tiendas y redes a medida que se incorporen.",
      },
      { tipo: "h2", texto: "Independencia" },
      {
        tipo: "p",
        texto:
          "La comisión no interviene en qué pala recomendamos ni en qué orden aparecen las tiendas, que se ordenan por precio. Ninguna marca ni tienda paga por aparecer ni puede revisar nuestros textos.",
      },
      { tipo: "h2", texto: "Precios y disponibilidad" },
      {
        tipo: "p",
        texto:
          "Los precios y la disponibilidad que mostramos proceden de las tiendas y se revisan a diario. Son informativos: pueden haber cambiado cuando llegues a la tienda, y el precio válido es el que figure allí en el momento de la compra.",
      },
      { tipo: "h2", texto: "La compra es con la tienda" },
      {
        tipo: "p",
        texto: `${sitio.nombre} no vende productos ni interviene en el pago, el envío, la garantía o las devoluciones. Para cualquier incidencia con un pedido, el interlocutor es la tienda en la que compraste.`,
      },
      {
        tipo: "nota",
        titulo: "¿Algo no cuadra?",
        texto: `Si ves un precio incorrecto o un enlace que no funciona, escríbenos a ${sitio.correo}.`,
      },
    ],
  },
  {
    slug: "aviso-legal",
    kicker: "Aviso legal",
    titulo: "Aviso legal",
    resumen: "Quién está detrás de esta web y en qué condiciones puedes usarla.",
    bloques: [
      { tipo: "h2", texto: "Titular del sitio" },
      {
        tipo: "definiciones",
        elementos: [
          { termino: "Titular", texto: sitio.razonSocial },
          { termino: "NIF", texto: sitio.nif },
          { termino: "Domicilio", texto: sitio.domicilio },
          { termino: "Contacto", texto: sitio.correo },
        ],
      },
      { tipo: "h2", texto: "Qué es esta web" },
      {
        tipo: "p",
        texto: `${sitio.nombre} es un recomendador de palas de pádel. Ofrece un cuestionario, fichas de producto con comparativa de precios y guías. No vende productos: enlaza a tiendas de terceros.`,
      },
      { tipo: "h2", texto: "Condiciones de uso" },
      {
        tipo: "lista",
        elementos: [
          "El uso de la web es gratuito y no exige registro.",
          "Te comprometes a usarla de forma lícita y a no intentar dañarla ni extraer sus contenidos de forma masiva.",
          "Podemos modificar o retirar contenidos y funciones sin previo aviso.",
        ],
      },
      { tipo: "h2", texto: "Alcance de la información" },
      {
        tipo: "p",
        texto:
          "Las recomendaciones y las guías son orientativas. No constituyen asesoramiento médico ni deportivo profesional. Si tienes una lesión o una molestia persistente, consulta a un profesional sanitario.",
      },
      {
        tipo: "p",
        texto:
          "Los precios, la disponibilidad y las características de los productos proceden de terceros y pueden contener errores o haber cambiado. La información válida es la que figure en la tienda en el momento de la compra.",
      },
      { tipo: "h2", texto: "Enlaces a otras webs" },
      {
        tipo: "p",
        texto:
          "Esta web contiene enlaces a tiendas de terceros, algunos de ellos de afiliado. No controlamos esas webs ni respondemos de sus contenidos, sus condiciones de venta o su tratamiento de datos.",
      },
      { tipo: "h2", texto: "Propiedad intelectual" },
      {
        tipo: "p",
        texto:
          "Los textos, el diseño y el código de esta web pertenecen a su titular o se usan con licencia. Las marcas y los nombres de producto pertenecen a sus respectivos propietarios y se citan solo para identificarlos.",
      },
      { tipo: "h2", texto: "Legislación aplicable" },
      {
        tipo: "p",
        texto:
          "Este aviso se rige por la legislación española. Si eres consumidor, cualquier controversia se someterá a los juzgados y tribunales de tu domicilio.",
      },
    ],
  },
  {
    slug: "privacidad",
    kicker: "Privacidad",
    titulo: "Política de privacidad",
    resumen:
      "Qué datos tratamos, para qué y durante cuánto tiempo. La versión corta: el cuestionario funciona en tu navegador, y tus molestias no se guardan.",
    bloques: [
      { tipo: "h2", texto: "Responsable" },
      {
        tipo: "p",
        texto: `El responsable del tratamiento es ${sitio.razonSocial}, con NIF ${sitio.nif} y domicilio en ${sitio.domicilio}. Para cualquier cuestión sobre tus datos, escribe a ${sitio.correo}.`,
      },
      { tipo: "h2", texto: "Qué datos tratamos y para qué" },
      {
        tipo: "definiciones",
        elementos: [
          {
            termino: "Respuestas del cuestionario",
            texto:
              "Se usan para calcular tu recomendación. El cálculo se hace en tu navegador: las respuestas no se envían a nuestros servidores.",
          },
          {
            termino: "Molestias físicas",
            texto:
              "Son un dato de salud. Solo las pedimos con tu consentimiento expreso, se usan para ajustar la recomendación y se quedan en la pestaña del navegador: desaparecen al cerrarla. No se guardan en tu historial ni en tu cuenta, y no se comparten con las tiendas. Puedes no contestar.",
          },
          {
            termino: "Palas guardadas, avisos e historial",
            texto:
              "Se guardan en tu propio navegador para que los tengas a mano. Puedes borrarlos cuando quieras desde «Mi cuenta».",
          },
          {
            termino: "Correo electrónico",
            texto:
              "Solo si decides acceder con tu correo. Lo usamos para enviarte el enlace de acceso y los avisos de precio que tú hayas creado. No enviamos publicidad.",
          },
          {
            termino: "Valoración de la recomendación",
            texto:
              "Si contestas a «¿Te ha servido esta recomendación?», recibimos tu respuesta (sí o no) sin ningún dato que te identifique.",
          },
        ],
      },
      { tipo: "h2", texto: "Base legal" },
      {
        tipo: "lista",
        elementos: [
          "Tu consentimiento, para el dato de molestias y para crear la cuenta con tu correo.",
          "La prestación del servicio que pides, para enviarte el enlace de acceso y los avisos de precio.",
          "Nuestro interés legítimo en mejorar el recomendador, para las valoraciones anónimas.",
        ],
      },
      { tipo: "h2", texto: "Cuánto tiempo los conservamos" },
      {
        tipo: "lista",
        elementos: [
          "Lo guardado en tu navegador permanece hasta que lo borres tú.",
          "El correo y la cuenta, hasta que borres la cuenta desde «Mi cuenta» o nos lo pidas.",
          "Los enlaces de acceso caducan a los pocos minutos y las sesiones, a los 30 días.",
        ],
      },
      { tipo: "h2", texto: "Con quién los compartimos" },
      {
        tipo: "p",
        texto:
          "No vendemos ni cedemos tus datos. Solo acceden a ellos los proveedores que nos prestan el alojamiento y el envío de correo, como encargados del tratamiento. Cuando sales hacia una tienda, esa tienda y su red de afiliación aplican sus propias políticas.",
      },
      { tipo: "h2", texto: "Tus derechos" },
      {
        tipo: "p",
        texto: `Puedes acceder a tus datos, rectificarlos, suprimirlos, oponerte a su tratamiento, limitarlo y pedir su portabilidad, así como retirar tu consentimiento en cualquier momento. Escribe a ${sitio.correo}. Si crees que no hemos atendido bien tu solicitud, puedes reclamar ante la Agencia Española de Protección de Datos (aepd.es).`,
      },
    ],
  },
  {
    slug: "cookies",
    kicker: "Cookies",
    titulo: "Política de cookies",
    resumen:
      "No usamos cookies de publicidad ni de analítica de terceros. Solo guardamos en tu navegador lo necesario para que la web funcione.",
    bloques: [
      { tipo: "h2", texto: "Qué guardamos en tu navegador" },
      {
        tipo: "p",
        texto:
          "Esta web usa una cookie técnica y el almacenamiento local del navegador. Todo lo que guarda es necesario para una función que tú has pedido, por eso no mostramos un aviso de consentimiento.",
      },
      {
        tipo: "tabla",
        cabecera: ["Nombre", "Para qué sirve", "Duración"],
        filas: [
          ["sesion (cookie)", "Mantener tu sesión si accedes con tu correo", "30 días"],
          ["palaideal:sesion", "Recordar en este navegador que ya has accedido", "Hasta que cierres sesión"],
          ["palaideal:encuesta", "Retomar un cuestionario a medias (sin el dato de molestias)", "Hasta que lo termines"],
          [
            "palaideal:respuestas",
            "Mostrar la recomendación del cuestionario que acabas de hacer",
            "Hasta que cierres la pestaña",
          ],
          ["palaideal:guardadas", "Tus palas guardadas", "Hasta que las borres"],
          ["palaideal:alertas", "Tus avisos de precio", "Hasta que los borres"],
          ["palaideal:historial", "Tus recomendaciones anteriores (sin el dato de molestias)", "Hasta que las borres"],
        ],
      },
      { tipo: "h2", texto: "Cómo borrarlo" },
      {
        tipo: "lista",
        elementos: [
          "Desde «Mi cuenta» puedes borrar de una vez todo lo guardado en este navegador.",
          "También puedes borrar los datos del sitio desde los ajustes de tu navegador.",
          "Si navegas en modo privado, no se conserva nada al cerrar la ventana.",
        ],
      },
      { tipo: "h2", texto: "Cookies de las tiendas" },
      {
        tipo: "p",
        texto:
          "Cuando pulsas «Ir a la tienda» sales de esta web. La tienda y su red de afiliación pueden instalar sus propias cookies para atribuir la venta. Esas cookies dependen de ellas: consulta su política de cookies.",
      },
    ],
  },
];
