"""Tareas diarias: copia de seguridad, feeds de las tiendas, métricas y limpieza.

Cada tarea devuelve un resumen (se guarda en job_run.resumen) o lanza una excepción si falla.
"""

import logging
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from app.adapters.feeds import FuenteFeedHTTP
from app.adapters.llm import ExtractorFichasClaude
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import (
    Evento,
    Importacion,
    MetricaDiaria,
    RecClick,
    Recomendacion,
    Sesion,
    Tienda,
    TokenAcceso,
)
from app.services import fichas, importacion, recomendacion

log = logging.getLogger(__name__)


# --- Copia de seguridad --------------------------------------------------------


def backup_db() -> dict[str, Any]:
    """pg_dump de la base de datos a un almacenamiento S3 (Cloudflare R2); conserva N días.

    Va la primera, antes de import_feed, que es la tarea que más cambia la base de datos.
    """
    ajustes = get_settings()
    if not (ajustes.backup_s3_endpoint and ajustes.backup_s3_bucket):
        if ajustes.entorno == "local":
            return {"omitida": "sin almacenamiento configurado (entorno local)"}
        raise RuntimeError("Copia de seguridad sin configurar (BACKUP_S3_*)")
    if shutil.which("pg_dump") is None:
        raise RuntimeError("pg_dump no está instalado en el contenedor")

    import boto3  # solo hace falta en esta tarea

    url_pg = ajustes.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    nombre = f"padel-{datetime.now(UTC):%Y%m%d-%H%M}.dump"
    s3 = boto3.client(
        "s3",
        endpoint_url=ajustes.backup_s3_endpoint,
        aws_access_key_id=ajustes.backup_s3_access_key.get_secret_value()
        if ajustes.backup_s3_access_key
        else None,
        aws_secret_access_key=ajustes.backup_s3_secret_key.get_secret_value()
        if ajustes.backup_s3_secret_key
        else None,
        region_name="auto",
    )
    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, nombre)
        # Formato propio de pg_dump: comprimido y restaurable con pg_restore.
        subprocess.run(["pg_dump", "--format=custom", f"--file={ruta}", url_pg], check=True)
        tamano = os.path.getsize(ruta)
        s3.upload_file(ruta, ajustes.backup_s3_bucket, f"backups/{nombre}")

    limite = datetime.now(UTC) - timedelta(days=ajustes.backup_dias)
    antiguas = [
        o["Key"]
        for o in s3.list_objects_v2(Bucket=ajustes.backup_s3_bucket, Prefix="backups/").get(
            "Contents", []
        )
        if o["LastModified"] < limite
    ]
    for clave in antiguas:
        s3.delete_object(Bucket=ajustes.backup_s3_bucket, Key=clave)
    return {"copia": nombre, "bytes": tamano, "borradas": len(antiguas)}


# --- Feeds -----------------------------------------------------------------------


def _lanzar_recompilacion() -> bool:
    """Pide a GitHub Actions que vuelva a compilar la web con el catálogo nuevo."""
    ajustes = get_settings()
    if ajustes.github_token is None:
        return False
    respuesta = httpx.post(
        f"https://api.github.com/repos/{ajustes.github_repo}/dispatches",
        headers={
            "Authorization": f"Bearer {ajustes.github_token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
        },
        json={"event_type": "catalogo-actualizado"},
        timeout=30.0,
    )
    respuesta.raise_for_status()
    return True


def import_feed() -> dict[str, Any]:
    """Importa el feed de cada tienda configurada, cada una en su transacción."""
    with SessionLocal() as db:
        tiendas = list(db.scalars(select(Tienda.id).where(Tienda.feed_url.is_not(None))))

    resumenes: list[dict[str, Any]] = []
    fallidas: list[str] = []
    for tienda_id in tiendas:
        with SessionLocal() as db:
            tienda = db.get(Tienda, tienda_id)
            fuente = FuenteFeedHTTP(
                tienda.feed_url, tienda.feed_formato or "csv", tienda.feed_campos
            )
            try:
                productos = list(fuente.productos())
            except Exception as exc:  # la tienda afectada sigue como ayer
                log.exception("feed de %s: no se ha podido descargar", tienda.nombre)
                db.add(Importacion(tienda_id=tienda.id, productos_recibidos=0, estado="fallida"))
                db.commit()
                fallidas.append(f"{tienda.nombre}: {type(exc).__name__}")
                continue
            resumenes.append(importacion.importar_tienda(db, tienda, productos).como_dict())

    hubo_cambios = any(
        r["estado"] == "correcta" and (r["actualizados"] or r["nuevos"] or r["agotados"])
        for r in resumenes
    )
    recompilada = _lanzar_recompilacion() if hubo_cambios else False
    if fallidas:
        raise RuntimeError(f"Feeds que han fallado: {', '.join(fallidas)}")
    return {"tiendas": resumenes, "web_recompilada": recompilada}


def extract_specs() -> dict[str, Any]:
    """La IA propone la ficha de las palas nuevas para revisarla (va tras import_feed)."""
    ajustes = get_settings()
    if ajustes.anthropic_api_key is None:
        return {"omitida": "sin clave de IA"}
    extractor = ExtractorFichasClaude(
        ajustes.anthropic_api_key.get_secret_value(), ajustes.ia_modelo
    )
    with SessionLocal() as db:
        return fichas.proponer_fichas(db, extractor, ajustes.ia_fichas_max)


def pregenerate_explanations() -> dict[str, Any]:
    """Deja explicados los perfiles más repetidos con los precios de hoy (va tras import_feed)."""
    ajustes = get_settings()
    with SessionLocal() as db:
        return recomendacion.pregenerar_explicaciones(
            db, ajustes.ia_pregenerar_dias, ajustes.ia_pregenerar_max
        )


# --- Métricas ----------------------------------------------------------------------


def _metricas_del_dia(db, dia: date) -> dict[tuple[str, str], int]:
    inicio = datetime.combine(dia, time.min, tzinfo=UTC)
    fin = inicio + timedelta(days=1)
    valores: dict[tuple[str, str], int] = {}
    for tipo, total in db.execute(
        select(Evento.tipo, func.count())
        .where(Evento.fecha >= inicio, Evento.fecha < fin)
        .group_by(Evento.tipo)
    ):
        valores[(f"evento:{tipo}", "")] = total
    valores[("recomendaciones", "")] = db.scalar(
        select(func.count()).where(Recomendacion.fecha >= inicio, Recomendacion.fecha < fin)
    )
    for origen, total in db.execute(
        select(RecClick.origen, func.count())
        .where(RecClick.fecha >= inicio, RecClick.fecha < fin)
        .group_by(RecClick.origen)
    ):
        valores[("clics_tienda", origen)] = total
    return valores


def aggregate_metrics() -> dict[str, Any]:
    """Resume los últimos 7 días en metrica_diaria (se recalculan por si llegan datos tarde)."""
    hoy = datetime.now(UTC).date()
    filas = 0
    with SessionLocal() as db:
        for dias_atras in range(1, 8):
            dia = hoy - timedelta(days=dias_atras)
            for (metrica, dimension), valor in _metricas_del_dia(db, dia).items():
                orden = insert(MetricaDiaria).values(
                    fecha=dia, metrica=metrica, dimension=dimension, valor=valor
                )
                db.execute(
                    orden.on_conflict_do_update(
                        index_elements=["fecha", "metrica", "dimension"],
                        set_={"valor": orden.excluded.valor},
                    )
                )
                filas += 1
        db.commit()
    return {"filas": filas}


# --- Limpieza ------------------------------------------------------------------------


def cleanup() -> dict[str, Any]:
    """Borra sesiones y enlaces de acceso caducados y los feeds en bruto antiguos."""
    ajustes = get_settings()
    ahora = datetime.now(UTC)
    with SessionLocal() as db:
        sesiones = db.execute(delete(Sesion).where(Sesion.expira < ahora)).rowcount
        tokens = db.execute(delete(TokenAcceso).where(TokenAcceso.expira < ahora)).rowcount
        # Al borrar la importación se borran sus productos y revisiones (ON DELETE CASCADE).
        importaciones = db.execute(
            delete(Importacion).where(
                Importacion.fecha < ahora - timedelta(days=ajustes.staging_dias)
            )
        ).rowcount
        db.commit()
    return {"sesiones": sesiones, "tokens": tokens, "importaciones": importaciones}
