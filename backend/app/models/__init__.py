"""Importa todos los modelos para que Base.metadata los conozca (Alembic lo necesita)."""

from app.models.catalogo import FamiliaModelo, Modelo, Oferta, PrecioHistorico, Sku, Tienda
from app.models.recomendaciones import Comision, RecClick, Recomendacion, RecShown
from app.models.usuarios import AlertaPrecio, PalaGuardada, Sesion, TokenAcceso, Usuario

__all__ = [
    "AlertaPrecio",
    "Comision",
    "FamiliaModelo",
    "Modelo",
    "Oferta",
    "PalaGuardada",
    "PrecioHistorico",
    "RecClick",
    "RecShown",
    "Recomendacion",
    "Sesion",
    "Sku",
    "Tienda",
    "TokenAcceso",
    "Usuario",
]
