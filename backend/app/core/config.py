"""Configuración leída de variables de entorno (o de backend/.env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    entorno: str = "local"
    database_url: str = "postgresql+psycopg://padel:padel@localhost:5432/padel"
    cors_origins: list[str] = ["http://localhost:4321"]
    sesion_dias: int = 30
    token_acceso_minutos: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
