"""Configuración leída de variables de entorno (o de backend/.env)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    entorno: str = "local"
    database_url: str = "postgresql+psycopg://padel:padel@localhost:5432/padel"
    cors_origins: list[str] = ["http://localhost:4321"]

    # --- Acceso y sesión (docs/ACCESO.md) ----------------------------------------
    # URL pública de la web: el enlace del correo apunta a {web_url}/acceso/verificar/?token=…
    web_url: str = "http://localhost:4321"
    nombre_web: str = "palaideal"
    sesion_dias: int = 30
    token_acceso_minutos: int = 15
    # Enlaces que se pueden pedir en una hora para un mismo correo y desde una misma IP.
    # El límite por IP evita que alguien use la API para enviar correos a miles de direcciones.
    enlaces_por_hora: int = 5
    enlaces_por_hora_ip: int = 20
    # Lax basta si la web y la API comparten dominio (palaideal.es y api.palaideal.es).
    # Si están en dominios distintos hace falta "none" (y HTTPS), pero muchos navegadores
    # bloquean esas cookies de terceros: mejor servir la API en un subdominio de la web.
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_dominio: str | None = None

    # --- Correo ---------------------------------------------------------------------
    # consola: escribe el correo en el log (desarrollo). smtp: lo envía de verdad.
    correo_modo: Literal["consola", "smtp"] = "consola"
    correo_remitente: str = "palaideal <no-responder@palaideal.es>"
    smtp_host: str = ""
    smtp_puerto: int = 587
    smtp_usuario: str = ""
    smtp_password: SecretStr = SecretStr("")
    # starttls (puerto 587), ssl (puerto 465) o ninguno (solo para servidores locales).
    smtp_seguridad: Literal["starttls", "ssl", "ninguno"] = "starttls"

    @property
    def es_local(self) -> bool:
        return self.entorno == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
