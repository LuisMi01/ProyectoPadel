"""Tests de humo: no necesitan base de datos."""

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import get_settings
from app.jobs import GRUPOS
from app.main import app

client = TestClient(app)


def test_rutas_de_la_arquitectura_registradas():
    rutas = set(app.openapi()["paths"])
    for esperada in [
        "/recomendaciones",
        "/recomendaciones/{recomendacion_id}/explicacion",
        "/recomendaciones/{recomendacion_id}/explicacion/flujo",
        "/recomendaciones/{recomendacion_id}/valoracion",
        "/tienda/{oferta_id}",
        "/eventos",
        "/acceso/enlace",
        "/acceso/verificar",
        "/acceso/cerrar",
        "/perfil",
        "/palas-guardadas",
        "/historial",
        "/alertas",
        "/internas/estado",
        "/internas/catalogo",
    ]:
        assert esperada in rutas, esperada


def test_cuenta_requiere_sesion():
    assert client.get("/perfil").status_code == 401


def test_catalogo_interno_exige_token_si_esta_configurado(monkeypatch):
    monkeypatch.setattr(get_settings(), "token_interno", SecretStr("secreto"))
    assert client.get("/internas/catalogo").status_code == 401
    assert client.get("/internas/catalogo", headers={"X-Token-Interno": "otro"}).status_code == 401


def test_encuesta_invalida_da_422():
    assert client.post("/recomendaciones", json={"camino": "otro"}).status_code == 422


def test_la_api_no_acepta_datos_de_salud():
    perfil = {"camino": "cambio", "exp": "gt2", "frec": "2-3", "estilo": "mixto",
              "edad": "adulto", "ppto": "250", "palas": [1]}  # fmt: skip
    for salud in ({"mol": "si"}, {"salud": {"zona": "Codo", "momento": "Casi siempre"}}):
        assert client.post("/recomendaciones", json={**perfil, **salud}).status_code == 422


def test_grupos_de_tareas():
    assert set(GRUPOS) == {"daily", "weekly", "monthly"}
    diarias = [t.__name__ for t in GRUPOS["daily"]]
    # La copia va antes de la importación, que es la tarea que más cambia la base de datos.
    assert diarias.index("backup_db") < diarias.index("import_feed")
