from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, MetaData
from sqlalchemy.orm import DeclarativeBase

# Esquemas de la base de datos (docs/BASE_DE_DATOS.md):
#   public  -> datos limpios que usa la aplicación.
#   staging -> catálogos de las tiendas tal como llegan, antes de normalizar.
ESQUEMA_STAGING = "staging"

# Nombres de constraints deterministas para que Alembic genere migraciones estables.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def en(valores: type[StrEnum], columna: str) -> str:
    """Expresión SQL de un CHECK que limita la columna a los valores de un StrEnum."""
    lista = ", ".join(f"'{v.value}'" for v in valores)
    return f"{columna} IN ({lista})"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # Todas las fechas se guardan con zona horaria (timestamptz).
    type_annotation_map = {datetime: DateTime(timezone=True)}
