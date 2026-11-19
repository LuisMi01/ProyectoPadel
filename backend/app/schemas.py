"""Esquemas Pydantic: validan el JSON de entrada y dan forma al de salida."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class Esquema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Encuesta y recomendación -------------------------------------------------


class SaludIn(Esquema):
    """Detalle de la molestia. Solo se acepta con el consentimiento expreso del cuestionario."""

    zona: Literal["Codo", "Hombro", "Muñeca", "Espalda"]
    momento: Literal["Mientras juego", "Al día siguiente", "Casi siempre"]
    consentimiento: Literal[True]


class PerfilEncuesta(Esquema):
    """Respuestas del cuestionario, con los mismos valores que frontend/src/lib/encuesta.ts.

    `mol` y `salud` son datos de salud: se usan para calcular la recomendación y no se guardan
    ni se escriben en los logs.
    """

    camino: Literal["primera", "cambio"]
    exp: Literal["nunca", "lt6", "m6a2", "gt2"]
    frec: Literal["1", "2-3", "4+"] | None = None
    estilo: Literal["control", "mixto", "potencia"] | None = None
    mol: Literal["no", "si", "nc"]
    salud: SaludIn | None = None
    edad: Literal["adulto", "junior"]
    ppto: Literal["80", "150", "250", "max"]

    @model_validator(mode="after")
    def _coherente(self) -> "PerfilEncuesta":
        if self.exp == "nunca":
            # Quien no ha jugado nunca no tiene frecuencia ni estilo: el cuestionario los salta.
            self.frec = None
            self.estilo = None
        elif self.frec is None or self.estilo is None:
            raise ValueError("Si ya juegas, hacen falta la frecuencia y el estilo")
        if self.mol != "si":
            self.salud = None
        return self

    def sin_salud(self) -> dict[str, str]:
        """Lo que se guarda en recomendacion.perfil."""
        return self.model_dump(exclude={"mol", "salud"}, exclude_none=True)


class PalaOut(Esquema):
    modelo_id: int
    slug: str
    nombre: str


class MotivoOut(Esquema):
    respuesta: str
    explicacion: str


class AlternativaOut(PalaOut):
    etiqueta: str
    ganas: str
    pierdes: str


class RecomendacionOut(Esquema):
    """Mismo contenido que calcula frontend/src/lib/recomendador.ts, más el id guardado."""

    id: int
    fecha: datetime
    titular: str
    mejor: PalaOut
    motivos: list[MotivoOut]
    alternativas: list[AlternativaOut]
    nota: str | None = None


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
