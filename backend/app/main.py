"""Punto de entrada de la API: uvicorn app.main:app"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.errores import registrar_manejadores
from app.core.origen import ComprobarOrigen


def crear_app() -> FastAPI:
    ajustes = get_settings()
    app = FastAPI(title="ProyectoPadel API", version="0.1.0")
    # El último middleware añadido es el primero en ejecutarse: CORS responde antes los
    # preflight y después ComprobarOrigen filtra las peticiones que cambian datos.
    app.add_middleware(ComprobarOrigen, origenes_permitidos=ajustes.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ajustes.cors_origins,
        allow_credentials=True,  # la sesión viaja en cookie
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_manejadores(app)
    app.include_router(api_router)
    return app


app = crear_app()
