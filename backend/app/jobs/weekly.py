"""Tareas semanales (lunes)."""

from typing import Any

from app.adapters.enlaces import ComprobadorEnlacesHTTP
from app.db.session import SessionLocal
from app.services import enlaces


def check_links() -> dict[str, Any]:
    """Comprueba la página de cada oferta y oculta las que no existen dos semanas seguidas."""
    comprobador = ComprobadorEnlacesHTTP()
    try:
        with SessionLocal() as db:
            return enlaces.comprobar_ofertas(db, comprobador)
    finally:
        comprobador.cerrar()


def weekly_digest() -> dict[str, Any]:
    """Resumen semanal por correo al equipo (llega con el envío de correo, junto a los usuarios)."""
    return {"omitida": "pendiente (necesita el envío de correo)"}
