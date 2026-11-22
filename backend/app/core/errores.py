"""Errores de dominio y su traducción a respuestas HTTP."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class Pendiente(NotImplementedError):
    """Funcionalidad definida en la arquitectura pero aún sin implementar."""


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(Pendiente)
    async def _pendiente(_: Request, exc: Pendiente) -> JSONResponse:
        return JSONResponse(status_code=501, content={"detail": f"Pendiente: {exc}"})
