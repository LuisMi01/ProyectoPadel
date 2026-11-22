"""Textos de los correos que envía la aplicación."""

from html import escape

from app.core.correo import Correo


def enlace_de_acceso(para: str, enlace: str, nombre_web: str, minutos: int) -> Correo:
    """Correo con el enlace para entrar o crear la cuenta (son el mismo paso)."""
    asunto = f"Tu enlace para entrar en {nombre_web}"
    texto = (
        f"Hola:\n\n"
        f"Abre este enlace para entrar en {nombre_web}. Si aún no tenías cuenta, "
        f"se crea al entrar.\n\n"
        f"{enlace}\n\n"
        f"El enlace caduca en {minutos} minutos y solo sirve una vez. Ábrelo en el mismo "
        f"navegador desde el que lo pediste.\n\n"
        f"Si no lo has pedido tú, ignora este correo: sin el enlace nadie puede entrar.\n"
    )
    e_enlace, e_web = escape(enlace, quote=True), escape(nombre_web)
    html = f"""<!doctype html>
<html lang="es">
  <body style="margin:0;padding:24px;background:#f1f4f8;font-family:Arial,sans-serif;color:#0a1b3d">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:12px">
      <tr><td style="padding:32px">
        <p style="margin:0 0 8px;font-size:22px;font-weight:800">{e_web}</p>
        <p style="margin:0 0 24px;font-size:16px;line-height:1.5">
          Pulsa el botón para entrar. Si aún no tenías cuenta, se crea al entrar.
        </p>
        <p style="margin:0 0 24px">
          <a href="{e_enlace}"
             style="display:inline-block;padding:14px 22px;border-radius:10px;
                    background:#1747c9;color:#ffffff;font-weight:700;text-decoration:none">
            Entrar en {e_web}
          </a>
        </p>
        <p style="margin:0 0 16px;font-size:14px;line-height:1.5;color:#46566f">
          Caduca en {minutos} minutos y solo sirve una vez. Ábrelo en el mismo navegador
          desde el que lo pediste.
        </p>
        <p style="margin:0;font-size:13px;line-height:1.5;color:#46566f">
          Si el botón no funciona, copia esta dirección en el navegador:<br>
          <span style="word-break:break-all">{e_enlace}</span>
        </p>
        <p style="margin:24px 0 0;font-size:13px;color:#46566f">
          Si no lo has pedido tú, ignora este correo: sin el enlace nadie puede entrar.
        </p>
      </td></tr>
    </table>
  </body>
</html>
"""
    return Correo(para=para, asunto=asunto, texto=texto, html=html)
