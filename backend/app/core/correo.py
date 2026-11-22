"""Envío de correo. Independiente del proveedor: cualquier servicio con SMTP vale
(Resend, Brevo, Amazon SES, Postmark, el del dominio…).

CORREO_MODO=consola escribe el correo en el log (desarrollo); CORREO_MODO=smtp lo envía.
Los tests sustituyen el envío con `capturar_correos()`.
"""

import logging
import smtplib
import ssl
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid

from app.core.config import get_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Correo:
    para: str
    asunto: str
    texto: str
    html: str


class ErrorCorreo(Exception):
    """No se ha podido entregar el correo al servidor SMTP."""


_capturados: list[Correo] | None = None


def enviar(correo: Correo) -> None:
    if _capturados is not None:
        _capturados.append(correo)
        return

    ajustes = get_settings()
    if ajustes.correo_modo == "consola":
        log.info("✉ Correo para %s — %s\n%s", correo.para, correo.asunto, correo.texto)
        return

    mensaje = EmailMessage()
    mensaje["From"] = ajustes.correo_remitente
    mensaje["To"] = correo.para
    mensaje["Subject"] = correo.asunto
    mensaje["Message-ID"] = make_msgid()
    mensaje.set_content(correo.texto)
    mensaje.add_alternative(correo.html, subtype="html")

    contexto = ssl.create_default_context()
    try:
        if ajustes.smtp_seguridad == "ssl":
            servidor = smtplib.SMTP_SSL(
                ajustes.smtp_host, ajustes.smtp_puerto, context=contexto, timeout=10
            )
        else:
            servidor = smtplib.SMTP(ajustes.smtp_host, ajustes.smtp_puerto, timeout=10)
        with servidor:
            if ajustes.smtp_seguridad == "starttls":
                servidor.starttls(context=contexto)
            if ajustes.smtp_usuario:
                servidor.login(ajustes.smtp_usuario, ajustes.smtp_password.get_secret_value())
            servidor.send_message(mensaje)
    except (OSError, smtplib.SMTPException) as e:
        # No se registra el destinatario: es un dato personal.
        log.error("Fallo al enviar correo por SMTP: %s", type(e).__name__)
        raise ErrorCorreo from e


@contextmanager
def capturar_correos() -> Iterator[list[Correo]]:
    """Para tests: guarda los correos en una lista en vez de enviarlos."""
    global _capturados
    previo, _capturados = _capturados, []
    try:
        yield _capturados
    finally:
        _capturados = previo
