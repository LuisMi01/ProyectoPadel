/**
 * Guías de la web. El contenido va en bloques tipados (no en Markdown) para
 * poder enlazar con rutas.* y con el catálogo sin escribir URLs a mano.
 */

export type Bloque =
  | { tipo: "p"; texto: string }
  | { tipo: "h2"; texto: string }
  | { tipo: "lista"; elementos: string[] }
  /** Lista de términos con su explicación. */
  | { tipo: "definiciones"; elementos: { termino: string; texto: string }[] }
  | { tipo: "tabla"; cabecera: string[]; filas: string[][] }
  /** Recuadro destacado: avisos y resúmenes. */
  | { tipo: "nota"; titulo: string; texto: string }
  /** Tarjetas de palas del catálogo, por slug. */
  | { tipo: "palas"; titulo: string; slugs: string[] };

export interface Guia {
  slug: string;
  /** Etiqueta corta: «Formas», «Molestias»… */
  categoria: string;
  titulo: string;
  resumen: string;
  /** Minutos de lectura aproximados. */
  lectura: number;
  /** Las destacadas salen en la portada, en este orden. */
  destacada?: boolean;
  bloques: Bloque[];
}

export const guias: Guia[] = [
  {
    slug: "redonda-lagrima-o-diamante",
    categoria: "Formas",
    titulo: "Pala redonda, lágrima o diamante: cuál te conviene",
    resumen:
      "La forma decide dónde queda el punto dulce y cuánto perdona la pala. Te explicamos qué cambia de una a otra y cómo elegir sin equivocarte.",
    lectura: 5,
    destacada: true,
    bloques: [
      {
        tipo: "p",
        texto:
          "La forma de la cabeza es lo primero que se ve de una pala y lo que más condiciona cómo se comporta. No es una cuestión de estética: decide dos cosas muy concretas. La primera, dónde queda el punto dulce, que es la zona de la cara en la que la bola sale limpia y sin vibraciones. La segunda, hacia dónde se reparte el peso, lo que se llama balance.",
      },
      {
        tipo: "p",
        texto:
          "Hay tres formas básicas. Cada una mueve el punto dulce y el peso un poco más hacia arriba que la anterior, y con eso cambia la pala entera.",
      },
      { tipo: "h2", texto: "Redonda: control y margen de error" },
      {
        tipo: "p",
        texto:
          "En una pala redonda el punto dulce es amplio y queda en el centro de la cara. El peso se concentra cerca del puño (balance bajo), así que la pala se mueve con facilidad y llega a tiempo a las bolas rápidas.",
      },
      {
        tipo: "p",
        texto:
          "Es la forma que más perdona: aunque no golpees justo en el centro, la bola sale razonablemente bien. A cambio, es la que menos pegada da en el remate. Es la elección habitual para empezar, para quien juega a colocar la bola y para quien arrastra molestias en el brazo.",
      },
      { tipo: "h2", texto: "Lágrima: un poco de todo" },
      {
        tipo: "p",
        texto:
          "La lágrima sube el punto dulce un poco y lo hace algo más pequeño. El balance queda en el medio. El resultado es una pala polivalente: defiende bien desde el fondo y tiene pegada suficiente cuando subes a la red.",
      },
      {
        tipo: "p",
        texto:
          "Es el paso natural cuando ya llevas un tiempo jugando y empiezas a atacar más, pero todavía no quieres renunciar a la tolerancia de una redonda.",
      },
      { tipo: "h2", texto: "Diamante: pegada a cambio de exigencia" },
      {
        tipo: "p",
        texto:
          "En el diamante el punto dulce es pequeño y está en la parte alta de la cara, y el peso se va hacia la cabeza (balance alto). Eso hace de palanca en los golpes por arriba: más pegada en el remate y en la víbora.",
      },
      {
        tipo: "p",
        texto:
          "El precio es claro: perdona poco cuando no golpeas en el centro, cuesta más moverla en defensa y le exige más al brazo. Tiene sentido si llevas años jugando, tu juego pasa por la red y no tienes molestias.",
      },
      { tipo: "h2", texto: "Las tres, de un vistazo" },
      {
        tipo: "tabla",
        cabecera: ["Forma", "Punto dulce", "Balance", "Lo mejor", "Lo peor"],
        filas: [
          ["Redonda", "Amplio y centrado", "Bajo", "Control y tolerancia", "Menos pegada"],
          ["Lágrima", "Medio, algo más arriba", "Medio", "Sirve para todo", "No destaca en nada"],
          ["Diamante", "Pequeño y alto", "Alto", "Pegada en el remate", "Perdona poco y carga el brazo"],
        ],
      },
      { tipo: "h2", texto: "Cómo decidir" },
      {
        tipo: "lista",
        elementos: [
          "Si llevas menos de seis meses, redonda. Todavía se está formando tu golpe y lo que más ayuda es que la pala perdone.",
          "Si juegas a aguantar la bola y esperar el fallo, redonda, lleves el tiempo que lleves.",
          "Si haces un poco de todo, lágrima.",
          "Si buscas el remate y llevas más de dos años, diamante. Si llevas menos, mejor una lágrima: tendrás pegada sin castigarte los golpes descentrados.",
          "Si notas molestias en codo, hombro o muñeca, descarta el diamante aunque te guste atacar.",
        ],
      },
      {
        tipo: "nota",
        titulo: "El error más habitual",
        texto:
          "Comprar un diamante porque es la pala que lleva un jugador profesional. Esas palas están pensadas para quien golpea casi siempre en el centro. Con menos técnica, lo normal es jugar peor y acabar con el brazo cargado.",
      },
      {
        tipo: "palas",
        titulo: "Una pala de cada forma",
        slugs: ["redonda-control-360", "lagrima-polivalente-365", "diamante-potencia-370"],
      },
    ],
  },
  {
    slug: "que-pala-usar-si-te-duele-el-codo",
    categoria: "Molestias",
    titulo: "Qué pala usar si te duele el codo",
    resumen:
      "Una pala no cura una lesión, pero una pala inadecuada la empeora. Qué buscar y qué evitar si notas molestias en el codo, el hombro o la muñeca.",
    lectura: 5,
    destacada: true,
    bloques: [
      {
        tipo: "nota",
        titulo: "Antes de nada",
        texto:
          "Esta guía habla de material, no de medicina. Si el dolor dura más de unos días o aparece también fuera de la pista, lo primero es que te vea un fisioterapeuta o un médico. Una pala no sustituye a un tratamiento.",
      },
      {
        tipo: "p",
        texto:
          "El dolor en la cara externa del codo es una de las molestias más frecuentes entre quienes juegan al pádel. Suele venir de una suma de cosas: técnica, carga de partidos, descanso y también material. La pala es solo una parte, pero es la más fácil de cambiar.",
      },
      {
        tipo: "p",
        texto:
          "La idea general es sencilla: cuanta menos vibración llegue al brazo y menos palanca haga la pala, mejor.",
      },
      { tipo: "h2", texto: "Qué buscar" },
      {
        tipo: "definiciones",
        elementos: [
          {
            termino: "Núcleo blando",
            texto:
              "Una goma blanda absorbe parte del impacto en lugar de transmitirlo al brazo. Es lo que más se nota.",
          },
          {
            termino: "Balance bajo o medio",
            texto:
              "Con el peso cerca del puño la pala hace menos palanca sobre el codo y cuesta menos frenarla después de cada golpe.",
          },
          {
            termino: "Forma redonda",
            texto:
              "Los golpes descentrados son los que más vibran. Un punto dulce amplio reduce cuántos de tus golpes lo son.",
          },
          {
            termino: "Un peso contenido",
            texto:
              "Una pala pesada cansa antes el brazo. Pero cuidado con irse al extremo contrario: una pala demasiado ligera absorbe peor el impacto y obliga a acelerar más el gesto.",
          },
          {
            termino: "Caras de fibra de vidrio",
            texto: "Son más flexibles que las de carbono y dan un tacto más amable.",
          },
        ],
      },
      { tipo: "h2", texto: "Qué evitar" },
      {
        tipo: "lista",
        elementos: [
          "Palas de diamante con balance alto: son las que más cargan el brazo.",
          "Núcleos duros y tactos secos, habituales en las palas de competición.",
          "Las palas más pesadas de cada gama.",
          "Seguir jugando con una pala rota o con el núcleo fatigado: ha perdido su capacidad de absorber el golpe.",
        ],
      },
      { tipo: "h2", texto: "Más allá de la pala" },
      {
        tipo: "lista",
        elementos: [
          "Revisa el grosor de la empuñadura. Si es demasiado fina, aprietas más de la cuenta en cada golpe; uno o dos overgrips lo corrigen.",
          "Cambia las bolas a tiempo. Una bola gastada o mojada pesa más y bota menos, y cada golpe exige más fuerza.",
          "Calienta antes de jugar y respeta los descansos entre partidos.",
          "Si puedes, que un monitor revise tu técnica: golpear tarde o con el brazo rígido carga mucho el codo.",
        ],
      },
      {
        tipo: "nota",
        titulo: "Cómo lo tratamos en el cuestionario",
        texto:
          "Si nos dices que notas molestias, priorizamos núcleo blando, menos peso y balance bajo. Es un dato de salud: lo usamos solo para calcular tu recomendación y no lo guardamos. Puedes saltarte la pregunta.",
      },
      {
        tipo: "palas",
        titulo: "Palas cómodas del catálogo",
        slugs: ["redonda-confort-350", "redonda-control-360", "lagrima-confort-355"],
      },
    ],
  },
  {
    slug: "palas-para-empezar-por-menos-de-100-euros",
    categoria: "Presupuesto",
    titulo: "Palas para empezar por menos de 100 €",
    resumen:
      "Para empezar no hace falta gastar más de 100 €. Qué puedes esperar en ese rango, en qué fijarte y cuándo compensa subir de precio.",
    lectura: 4,
    destacada: true,
    bloques: [
      {
        tipo: "p",
        texto:
          "La primera pala no tiene que ser cara. Durante los primeros meses lo que más ayuda es una pala ligera, que perdone y que no te cargue el brazo, y eso se encuentra de sobra por debajo de 100 €.",
      },
      { tipo: "h2", texto: "Qué te llevas por menos de 100 €" },
      {
        tipo: "p",
        texto:
          "En este rango las palas suelen tener caras de fibra de vidrio y un núcleo de goma EVA de dureza media o blanda. Son materiales sencillos, pero adecuados para aprender: la fibra de vidrio es flexible y ayuda a sacar la bola aunque todavía no tengas un golpe potente.",
      },
      {
        tipo: "p",
        texto:
          "Lo que no vas a encontrar son caras de carbono ni núcleos de varias densidades. No los necesitas todavía: esas mejoras se notan cuando el golpe ya es regular.",
      },
      { tipo: "h2", texto: "En qué fijarte" },
      {
        tipo: "lista",
        elementos: [
          "Forma redonda: punto dulce amplio y centrado.",
          "Balance bajo: el peso cerca del puño, para que la pala sea fácil de mover.",
          "Un peso contenido, sin irte a las más pesadas de la gama.",
          "Que venga con protector en el marco, o cuenta con ponérselo: los primeros meses la pala roza mucho la pared y el suelo.",
        ],
      },
      { tipo: "h2", texto: "En qué no fijarte" },
      {
        tipo: "lista",
        elementos: [
          "El nombre del jugador que la anuncia. Las palas de iniciación de una marca no se parecen a las que llevan sus profesionales.",
          "Las tecnologías con nombre propio. En esta gama casi todas hacen lo mismo.",
          "La rugosidad de la cara. Sirve para dar efecto, y eso viene después.",
        ],
      },
      { tipo: "h2", texto: "Cuándo compensa gastar más" },
      {
        tipo: "p",
        texto:
          "Si vas a jugar dos o tres veces por semana desde el principio, una pala de entre 100 y 150 € te durará más y no se te quedará corta en un año. Si no sabes todavía cuánto vas a jugar, empieza por una económica: siempre estás a tiempo de cambiar.",
      },
      {
        tipo: "nota",
        titulo: "Un truco para ahorrar",
        texto:
          "Los modelos de la temporada anterior suelen bajar de precio cuando sale la colección nueva, y la pala es la misma. En cada ficha te enseñamos el precio más bajo de los últimos 90 días para que sepas si hoy es buen momento.",
      },
      {
        tipo: "palas",
        titulo: "Palas del catálogo por menos de 100 €",
        slugs: ["redonda-basica-350", "lagrima-basica-360", "redonda-inicio-355"],
      },
    ],
  },
  {
    slug: "como-elegir-tu-primera-pala",
    categoria: "Primeros pasos",
    titulo: "Cómo elegir tu primera pala de pádel",
    resumen:
      "Cuatro decisiones y ninguna necesita jerga: forma, balance, peso y núcleo. Lo que importa de verdad cuando empiezas y lo que puedes ignorar.",
    lectura: 4,
    bloques: [
      {
        tipo: "p",
        texto:
          "Entrar en una tienda de pádel sin haber jugado es abrumador: cientos de palas, nombres de tecnologías y precios que van de 40 a más de 300 €. La buena noticia es que para una primera pala solo hay cuatro decisiones, y casi todas tienen una respuesta clara.",
      },
      { tipo: "h2", texto: "Las cuatro decisiones" },
      {
        tipo: "definiciones",
        elementos: [
          {
            termino: "Forma: redonda",
            texto:
              "Es la que tiene el punto dulce más amplio y centrado, y por tanto la que más perdona. Las formas de lágrima y diamante llegan después.",
          },
          {
            termino: "Balance: bajo",
            texto:
              "Significa que el peso queda cerca del puño. La pala se mueve rápido y no cansa. Las redondas suelen tenerlo así.",
          },
          {
            termino: "Peso: contenido",
            texto:
              "Una pala ligera se maneja mejor mientras aprendes el gesto. Si dudas entre dos pesos, quédate con el menor.",
          },
          {
            termino: "Núcleo: blando o medio",
            texto:
              "El núcleo es la goma de dentro. Si es blando, la bola sale con facilidad aunque no golpees fuerte, y llega menos vibración al brazo.",
          },
        ],
      },
      { tipo: "h2", texto: "Cuánto gastar" },
      {
        tipo: "p",
        texto:
          "Entre 60 y 130 € hay palas de sobra para empezar bien. Por debajo de eso los materiales suelen durar poco; por encima, pagas mejoras que todavía no vas a notar.",
      },
      { tipo: "h2", texto: "Lo que puedes ignorar por ahora" },
      {
        tipo: "lista",
        elementos: [
          "El tipo de carbono y sus números (3K, 12K, 18K).",
          "La rugosidad de la cara.",
          "Las palas «de» un jugador profesional.",
          "Las comparativas de potencia: con unos meses de juego, la potencia la pones tú.",
        ],
      },
      { tipo: "h2", texto: "Lo que sí merece la pena añadir" },
      {
        tipo: "lista",
        elementos: [
          "Un protector para el marco, si la pala no lo trae.",
          "Un overgrip: mejora el agarre, absorbe el sudor y se cambia por muy poco dinero.",
          "Una funda o un paletero que la proteja del calor: dejar la pala en el coche en verano estropea la goma.",
        ],
      },
      {
        tipo: "nota",
        titulo: "Si prefieres que lo hagamos por ti",
        texto:
          "El cuestionario hace estas mismas preguntas y te enseña palas concretas con su precio en varias tiendas. Si llevas menos de seis meses jugando, son solo cuatro preguntas.",
      },
      {
        tipo: "palas",
        titulo: "Tres palas para empezar",
        slugs: ["redonda-inicio-355", "redonda-control-360", "redonda-basica-350"],
      },
    ],
  },
  {
    slug: "balance-peso-y-nucleo",
    categoria: "Materiales",
    titulo: "Balance, peso y núcleo: qué notas de verdad en la pista",
    resumen:
      "Las fichas de las palas están llenas de datos. Estos son los cuatro que cambian cómo se siente una pala, explicados sin tecnicismos.",
    lectura: 6,
    bloques: [
      {
        tipo: "p",
        texto:
          "Dos palas de la misma forma pueden comportarse de manera muy distinta. La diferencia está en cuatro cosas: dónde llevan el peso, cuánto pesan, cómo es la goma de dentro y de qué están hechas las caras.",
      },
      { tipo: "h2", texto: "Balance: dónde está el peso" },
      {
        tipo: "p",
        texto:
          "El balance indica hacia dónde se reparte el peso de la pala. Con balance bajo, el peso está cerca del puño: la pala se mueve con rapidez y es fácil de controlar. Con balance alto, el peso se va hacia la cabeza: cuesta más moverla, pero golpea con más inercia en el remate.",
      },
      {
        tipo: "p",
        texto:
          "Por eso dos palas que pesan lo mismo pueden parecer una ligera y la otra pesada. Lo que notas en la mano no es el peso total, sino dónde está.",
      },
      { tipo: "h2", texto: "Peso: diez gramos se notan" },
      {
        tipo: "p",
        texto:
          "La mayoría de palas de adulto pesa entre 350 y 375 gramos. Parece un margen pequeño, pero diez gramos se notan al final de un partido. Más peso da estabilidad y pegada; menos peso da manejabilidad y descansa el brazo.",
      },
      {
        tipo: "p",
        texto:
          "Las tiendas dan un rango y no una cifra exacta porque cada unidad sale de fábrica con una pequeña variación. Ten en cuenta también que el protector y el overgrip añaden unos gramos.",
      },
      { tipo: "h2", texto: "Núcleo: la goma de dentro" },
      {
        tipo: "p",
        texto:
          "El núcleo es el relleno de la pala, casi siempre una goma llamada EVA en distintas durezas. Es lo que decide el tacto.",
      },
      {
        tipo: "definiciones",
        elementos: [
          {
            termino: "Núcleo blando",
            texto:
              "La bola se hunde más y sale con facilidad aunque golpees despacio. Es cómodo y transmite menos vibración. En los golpes muy fuertes pierde algo de precisión.",
          },
          {
            termino: "Núcleo duro",
            texto:
              "Responde mejor cuanto más fuerte golpeas y da mucho control a quien tiene buena técnica. A cambio, saca peor la bola desde el fondo y es más exigente con el brazo.",
          },
        ],
      },
      {
        tipo: "nota",
        titulo: "El frío también cuenta",
        texto:
          "La goma se endurece con el frío y se ablanda con el calor. La misma pala se nota más dura en invierno que en verano.",
      },
      { tipo: "h2", texto: "Caras: fibra de vidrio o carbono" },
      {
        tipo: "p",
        texto:
          "Las caras son las dos láminas que golpean la bola. La fibra de vidrio es más flexible y más barata: da salida de bola y un tacto amable, y dura algo menos. El carbono es más rígido y resistente: aguanta mejor el uso intenso y da un golpe más firme, pero cuesta más.",
      },
      {
        tipo: "p",
        texto:
          "Los números que acompañan al carbono (3K, 12K, 18K) indican los miles de filamentos de cada hilo del tejido. No son una escala de calidad: cambian el tacto, y cada marca los combina con resinas y núcleos distintos. No compares dos palas solo por ese número.",
      },
      { tipo: "h2", texto: "Resumen rápido" },
      {
        tipo: "tabla",
        cabecera: ["Si quieres…", "Busca", "Renuncias a"],
        filas: [
          ["Una pala fácil de mover", "Balance bajo y poco peso", "Pegada en el remate"],
          ["Más pegada arriba", "Balance alto", "Manejabilidad y descanso para el brazo"],
          ["Comodidad y salida de bola", "Núcleo blando y fibra de vidrio", "Precisión en los golpes fuertes"],
          ["Control con golpe fuerte", "Núcleo firme y carbono", "Comodidad y tolerancia"],
        ],
      },
    ],
  },
];

export const guiasDestacadas = guias.filter((g) => g.destacada);

export function guiaPorSlug(slug: string): Guia | undefined {
  return guias.find((g) => g.slug === slug);
}
