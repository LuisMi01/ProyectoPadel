"""Importa todos los modelos para que Base.metadata los conozca (Alembic lo necesita)."""

from app.models.catalogo import (
    FamiliaModelo,
    Modelo,
    Oferta,
    PrecioHistorico,
    Sku,
    Tienda,
    VocabMap,
)
from app.models.recomendaciones import (
    Comision,
    ExplicacionCache,
    Feedback,
    RecClick,
    Recomendacion,
    RecShown,
)
from app.models.sistema import Evento, JobRun, MetricaDiaria
from app.models.staging import Importacion, ProductoFeed, RevisionPendiente
from app.models.usuarios import AlertaPrecio, PalaGuardada, Sesion, TokenAcceso, Usuario

__all__ = [
    "AlertaPrecio",
    "Comision",
    "Evento",
    "ExplicacionCache",
    "FamiliaModelo",
    "Feedback",
    "Importacion",
    "JobRun",
    "MetricaDiaria",
    "Modelo",
    "Oferta",
    "PalaGuardada",
    "PrecioHistorico",
    "ProductoFeed",
    "RecClick",
    "RecShown",
    "Recomendacion",
    "RevisionPendiente",
    "Sesion",
    "Sku",
    "Tienda",
    "TokenAcceso",
    "Usuario",
    "VocabMap",
]
