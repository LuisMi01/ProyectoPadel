"""Puertos: lo que el dominio necesita del exterior. Los implementan los adaptadores."""

from collections.abc import Iterable, Iterator
from typing import Any, Protocol

from app.domain.modelos import Pala, ProductoFeed


class RepositorioCatalogo(Protocol):
    def palas(self) -> list[Pala]:
        """Modelos activos del catálogo, con sus ofertas."""
        ...


class ExplicacionFallida(Exception):
    """La IA no ha terminado bien la explicación (error, rechazo o respuesta cortada)."""


class ProveedorExplicaciones(Protocol):
    def explicar(self, hechos: str) -> str | None:
        """Redacta la explicación a partir de hechos del catálogo; None si falla."""
        ...

    def redactar(self, hechos: str) -> Iterator[str]:
        """La misma explicación, por trozos según se escribe. Lanza ExplicacionFallida si no
        termina bien (los trozos ya enviados no valen)."""
        ...


class FuenteFeed(Protocol):
    def productos(self) -> Iterable[ProductoFeed]:
        """Productos del feed de una tienda, ya traducidos a nuestros campos."""
        ...


class ComprobadorEnlaces(Protocol):
    def codigo(self, url: str) -> int | None:
        """Código HTTP de la página (tras seguir redirecciones); None si no responde."""
        ...


class ExtractorFichas(Protocol):
    def extraer(self, texto: str) -> dict[str, Any] | None:
        """Ficha de la pala (forma, balance, peso…) leída del texto de la tienda; None si falla."""
        ...


class EnviadorEmail(Protocol):
    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None: ...
