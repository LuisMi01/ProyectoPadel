"""ProveedorExplicaciones con Claude (SDK oficial `anthropic`).

Solo recibe hechos del catálogo y las respuestas sin datos de salud: nunca datos personales.
Si la API falla, rechaza la petición o se corta la respuesta, devuelve None y el servicio usa la
plantilla.
"""

import logging

import anthropic

log = logging.getLogger(__name__)

SISTEMA = """\
Eres el redactor de palaideal, un recomendador independiente de palas de pádel.
Te pasamos las respuestas de una persona al cuestionario y las palas que el motor le ha
recomendado, con sus datos. Escribe en español de España, tuteando, una explicación breve
(entre 60 y 120 palabras, uno o dos párrafos, sin títulos, listas ni formato) de por qué la
primera pala le encaja y en qué se diferencian las otras.

- Usa solo los datos que te damos. No inventes medidas, materiales, precios ni tiendas.
- Nombra las palas exactamente como aparecen.
- Relaciona cada rasgo de la pala con una respuesta concreta de la persona.
- No des consejos médicos ni hables de comisiones o de enlaces.
"""


class ProveedorExplicacionesClaude:
    def __init__(self, api_key: str, modelo: str) -> None:
        self._cliente = anthropic.Anthropic(api_key=api_key, timeout=30.0, max_retries=2)
        self._modelo = modelo

    def explicar(self, hechos: str) -> str | None:
        try:
            respuesta = self._cliente.messages.create(
                model=self._modelo,
                max_tokens=2000,
                system=SISTEMA,
                output_config={"effort": "low"},  # texto corto con los datos ya dados
                messages=[{"role": "user", "content": hechos}],
            )
        except anthropic.RateLimitError:
            log.warning("IA: límite de peticiones alcanzado, se usa la plantilla")
            return None
        except anthropic.APIStatusError as exc:
            log.warning("IA: error %s de la API, se usa la plantilla", exc.status_code)
            return None
        except anthropic.APIConnectionError:
            log.warning("IA: sin conexión con la API, se usa la plantilla")
            return None

        if respuesta.stop_reason != "end_turn":
            # refusal, max_tokens...: mejor la plantilla que un texto incompleto.
            log.warning("IA: respuesta descartada (stop_reason=%s)", respuesta.stop_reason)
            return None
        texto = "".join(b.text for b in respuesta.content if b.type == "text").strip()
        return texto or None
