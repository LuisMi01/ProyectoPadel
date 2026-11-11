from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.errores import Pendiente
from app.db.session import engine
from app.schemas import EstadoServicio

router = APIRouter(prefix="/internas", tags=["Internas"])


@router.get("/estado", response_model=EstadoServicio)
def estado_del_servicio() -> EstadoServicio:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        db_ok = False
    return EstadoServicio(estado="ok" if db_ok else "degradado", base_de_datos=db_ok)


@router.get("/catalogo")
def exportar_catalogo():
    # Lo consume el build del frontend para generar las fichas estáticas.
    raise Pendiente("exportar catálogo")
