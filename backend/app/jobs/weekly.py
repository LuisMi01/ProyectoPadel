"""Tareas semanales (lunes)."""

from typing import Any


def check_links() -> dict[str, Any]:
    """Comprobar que la página de cada oferta sigue existiendo (tras el lanzamiento)."""
    return {"omitida": "pendiente (tras el lanzamiento)"}


def weekly_digest() -> dict[str, Any]:
    """Resumen semanal por correo al equipo (llega con el envío de correo, junto a los usuarios)."""
    return {"omitida": "pendiente (necesita el envío de correo)"}
