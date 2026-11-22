from fastapi import APIRouter

from app.api.routes import acceso, analitica, cuenta, internas, recomendaciones, tienda

api_router = APIRouter()
for r in (
    recomendaciones.router,
    tienda.router,
    analitica.router,
    acceso.router,
    cuenta.perfil,
    cuenta.palas,
    cuenta.historial,
    cuenta.alertas,
    internas.router,
):
    api_router.include_router(r)
