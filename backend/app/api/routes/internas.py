import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DB
from app.core.config import get_settings
from app.db.session import engine
from app.schemas import EstadoServicio
from app.services import catalogo

router = APIRouter(prefix="/internas", tags=["Internas"])


def exigir_token_interno(x_token_interno: Annotated[str | None, Header()] = None) -> None:
    """Si hay TOKEN_INTERNO configurado, la petición tiene que traerlo en X-Token-Interno."""
    esperado = get_settings().token_interno
    if esperado is None:
        return
    if not x_token_interno or not secrets.compare_digest(
        x_token_interno, esperado.get_secret_value()
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token interno no válido")


@router.get("/estado", response_model=EstadoServicio)
def estado_del_servicio() -> EstadoServicio:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        db_ok = False
    return EstadoServicio(estado="ok" if db_ok else "degradado", base_de_datos=db_ok)


@router.get("/catalogo", dependencies=[Depends(exigir_token_interno)])
def exportar_catalogo(db: DB):
    """Catálogo en el formato de frontend/src/data/catalogo.ts. Lo usa el build de la web."""
    return catalogo.exportar(db)
