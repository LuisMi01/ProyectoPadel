"""Esquemas Pydantic: validan el JSON de entrada y dan forma al de salida."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Encuesta y recomendación -------------------------------------------------


class PerfilEncuesta(Esquema):
    """Respuestas de la encuesta (ver flujo en Figma). Sin datos de salud."""

    camino: Literal["primera", "cambiar"]
    experiencia_meses: int = Field(ge=0)
    frecuencia_semanal: int | None = Field(default=None, ge=0, le=14)
    estilo: Literal["defensivo", "polivalente", "ofensivo"] | None = None
    molestias: bool
    zona_molestia: Literal["codo", "hombro", "muneca"] | None = None
    momento_molestia: Literal["durante", "despues"] | None = None
    junior: bool
    presupuesto_max: Decimal = Field(gt=0)


class ModeloRecomendado(Esquema):
    modelo_id: int
    posicion: int
    nombre: str


class RecomendacionOut(Esquema):
    id: int
    fecha: datetime
    modelos: list[ModeloRecomendado]


class ExplicacionOut(Esquema):
    recomendacion_id: int
    texto: str


class ValoracionIn(Esquema):
    puntuacion: int = Field(ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=1000)


# --- Analítica ---------------------------------------------------------------


class EventoIn(Esquema):
    tipo: str = Field(max_length=50)
    datos: dict[str, str | int | float | bool | None] = {}


# --- Acceso ------------------------------------------------------------------


class SolicitudEnlace(Esquema):
    email: EmailStr


class VerificarEnlace(Esquema):
    token: str


# --- Cuenta ------------------------------------------------------------------


class PerfilOut(Esquema):
    id: int
    email: EmailStr
    creado_en: datetime


class PalaGuardadaIn(Esquema):
    modelo_id: int


class PalaGuardadaOut(Esquema):
    modelo_id: int
    fecha: datetime


class AlertaIn(Esquema):
    modelo_id: int
    precio_objetivo: Decimal = Field(gt=0)


class AlertaOut(Esquema):
    id: int
    modelo_id: int
    precio_objetivo: Decimal


class HistorialItem(Esquema):
    id: int
    fecha: datetime


class EstadoServicio(Esquema):
    estado: Literal["ok", "degradado"]
    base_de_datos: bool
