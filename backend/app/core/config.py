"""Configuración leída de variables de entorno (o de backend/.env)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    entorno: str = "local"
    database_url: str = "postgresql+psycopg://padel:padel@localhost:5432/padel"
    cors_origins: list[str] = ["http://localhost:4321"]
    sesion_dias: int = 30
    token_acceso_minutos: int = 15

    # Protege los endpoints /internas/* que usa el build del frontend. Sin valor, quedan abiertos
    # (solo tiene sentido en local).
    token_interno: SecretStr | None = None

    # Explicaciones con IA. Sin clave se usa siempre la plantilla.
    anthropic_api_key: SecretStr | None = None
    ia_modelo: str = "claude-haiku-5-5"
    ia_llamadas_diarias_max: int = 500  # tope de gasto: explicaciones nuevas por día

    # Importación de feeds (jobs.daily.import_feed).
    feed_minimo_respecto_anterior: float = 0.5  # menos productos que esto x el anterior: descartar
    precio_cambio_maximo: float = 0.6  # cambios mayores (60 %) van a revisión antes de publicarse
    staging_dias: int = 30  # días que se conservan los feeds en bruto

    # Recompilar la web tras importar (GitHub repository_dispatch). Sin token no se lanza.
    github_repo: str = "LuisMi01/ProyectoPadel"
    github_token: SecretStr | None = None

    # Copia de seguridad diaria (jobs.daily.backup_db) en un almacenamiento S3 (Cloudflare R2).
    backup_s3_endpoint: str | None = None
    backup_s3_bucket: str | None = None
    backup_s3_access_key: SecretStr | None = None
    backup_s3_secret_key: SecretStr | None = None
    backup_dias: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
