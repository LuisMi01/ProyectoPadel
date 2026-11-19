"""Puertos: lo que el dominio necesita del exterior. Los implementan los adaptadores."""

from collections.abc import Iterable
from typing import Protocol

from app.domain.modelos import Pala, ProductoFeed


class RepositorioCatalogo(Protocol):
    def palas(self) -> list[Pala]:
        """Modelos activos del catálogo, con sus ofertas."""
        ...


class ProveedorExplicaciones(Protocol):
    def explicar(self, hechos: str) -> str | None:
        """Redacta la explicación a partir de hechos del catálogo; None si falla."""
        ...


class FuenteFeed(Protocol):
    def productos(self) -> Iterable[ProductoFeed]:
        """Productos del feed de una tienda, ya traducidos a nuestros campos."""
        ...


class EnviadorEmail(Protocol):
    def enviar(self, destino: str, asunto: str, cuerpo: str) -> None: ...
