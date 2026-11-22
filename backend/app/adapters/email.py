"""EnviadorEmail: enlaces de acceso y alertas de precio. Proveedor pendiente de elegir."""


class EnviadorEmailPendiente:
    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None:
        raise NotImplementedError("envío de email")
