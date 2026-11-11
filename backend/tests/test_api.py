"""Tests de humo: no necesitan base de datos."""

from fastapi.testclient import TestClient

from app.jobs import GRUPOS
from app.main import app

client = TestClient(app)


def test_rutas_de_la_arquitectura_registradas():
    rutas = set(app.openapi()["paths"])
    for esperada in [
        "/recomendaciones",
        "/recomendaciones/{recomendacion_id}/explicacion",
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


def test_endpoint_pendiente_devuelve_501():
    assert client.get("/internas/catalogo").status_code == 501


def test_evento_se_acepta():
    assert client.post("/eventos", json={"tipo": "encuesta_iniciada"}).status_code == 202


def test_encuesta_invalida_da_422():
    assert client.post("/recomendaciones", json={"camino": "otro"}).status_code == 422


def test_grupos_de_tareas():
    assert set(GRUPOS) == {"daily", "weekly", "monthly"}
