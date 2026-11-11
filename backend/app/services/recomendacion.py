"""Motor de recomendación. Esqueleto: el algoritmo y el ranker están pendientes."""

from sqlalchemy.orm import Session

from app.core.errores import Pendiente
from app.models import Recomendacion, Usuario
from app.schemas import PerfilEncuesta, ValoracionIn


def obtener(db: Session, perfil: PerfilEncuesta, usuario: Usuario | None) -> Recomendacion:
    # Pasos previstos:
    #   1. Filtrar modelos activos por presupuesto, junior y molestias.
    #   2. Puntuar con el ranker (entrenado mensualmente por jobs.monthly.train_ranker).
    #   3. Guardar Recomendacion + RecShown con la posición de cada modelo.
    raise Pendiente("motor de recomendación")


def explicar(db: Session, recomendacion_id: int) -> str:
    # Las explicaciones se pregeneran a diario (jobs.daily.pregenerate_explanations).
    raise Pendiente("explicación con IA")


def valorar(db: Session, recomendacion_id: int, valoracion: ValoracionIn) -> None:
    raise Pendiente("valoración de recomendaciones")
