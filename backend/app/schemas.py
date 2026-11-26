"""Esquemas Pydantic: validan el JSON de entrada y dan forma al de salida."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Encuesta y recomendación -------------------------------------------------


class RecomendacionIn(Esquema):
    """Recomendación que ha calculado el navegador (frontend/src/lib/recomendador.ts).

    Trae las respuestas con los mismos valores que frontend/src/lib/encuesta.ts y los modelos que
    se han enseñado, en orden. La API no recibe nunca datos de salud: las molestias se quedan en el
    navegador, y cualquier campo que no esté aquí (como `mol` o `salud`) se rechaza con un 422.
    """

    model_config = ConfigDict(extra="forbid")

    camino: Literal["primera", "cambio"]
    exp: Literal["nunca", "lt6", "m6a2", "gt2"]
    frec: Literal["1", "2-3", "4+"] | None = None
    estilo: Literal["control", "mixto", "potencia"] | None = None
    edad: Literal["adulto", "junior"]
    ppto: Literal["100", "150", "250", "max"]
    # La mejor y sus alternativas (ids de modelo, los mismos que en el catálogo de la web).
    palas: list[int] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def _coherente(self) -> "RecomendacionIn":
        if self.exp == "nunca":
            # Quien no ha jugado nunca no tiene frecuencia ni estilo: el cuestionario los salta.
            self.frec = None
            self.estilo = None
        elif self.frec is None or self.estilo is None:
            raise ValueError("Si ya juegas, hacen falta la frecuencia y el estilo")
        if len(set(self.palas)) != len(self.palas):
            raise ValueError("Una pala no puede salir dos veces en la misma recomendación")
        return self

    def perfil(self) -> dict[str, str]:
        """Las respuestas, tal como se guardan en recomendacion.perfil."""
        return self.model_dump(exclude={"palas"}, exclude_none=True)


class RecomendacionGuardadaOut(Esquema):
    id: int
    fecha: datetime


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
