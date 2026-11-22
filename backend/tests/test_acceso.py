"""Crear cuenta, iniciar y cerrar sesión: flujo completo contra PostgreSQL real."""

import re
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.core import correo
from app.db.session import get_db
from app.main import app
from app.models import Sesion, TokenAcceso, Usuario

WEB = "http://localhost:4321"  # web_url y origen permitido por defecto


@pytest.fixture
def correos():
    with correo.capturar_correos() as lista:
        yield lista


@pytest.fixture
def cliente(db, correos):
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app, headers={"Origin": WEB})
    finally:
        app.dependency_overrides.clear()


def pedir_enlace(cliente, correos, email="ana@example.com") -> str:
    """Pide un enlace y devuelve el token que llega en el correo."""
    r = cliente.post("/acceso/enlace", json={"email": email})
    assert r.status_code == 202, r.text
    enlace = re.search(r"https?://\S+", correos[-1].texto).group(0)
    assert enlace.startswith(f"{WEB}/acceso/verificar/?token=")
    return enlace.split("token=", 1)[1]


def entrar(cliente, correos, email="ana@example.com"):
    token = pedir_enlace(cliente, correos, email)
    return cliente.post("/acceso/verificar", json={"token": token})


def test_crear_cuenta_entrar_y_salir(cliente, correos, db):
    assert cliente.get("/perfil").status_code == 401

    token = pedir_enlace(cliente, correos, "  Ana@Example.COM ")
    assert correos[-1].para == "ana@example.com"
    # En la base de datos solo está el hash, nunca el token.
    guardado = db.scalar(select(TokenAcceso.hash))
    assert guardado != token and len(guardado) == 64

    r = cliente.post("/acceso/verificar", json={"token": token})
    assert r.status_code == 204
    cookie = r.headers["set-cookie"].lower()
    assert "sesion=" in cookie and "httponly" in cookie and "samesite=lax" in cookie

    perfil = cliente.get("/perfil")
    assert perfil.status_code == 200
    assert perfil.json()["email"] == "ana@example.com"

    assert cliente.post("/acceso/cerrar").status_code == 204
    assert cliente.get("/perfil").status_code == 401
    assert db.scalar(select(func.count()).select_from(Sesion)) == 0


def test_volver_a_entrar_no_duplica_la_cuenta(cliente, correos, db):
    assert entrar(cliente, correos).status_code == 204
    cliente.cookies.clear()
    assert entrar(cliente, correos, "ANA@example.com").status_code == 204
    assert db.scalar(select(func.count()).select_from(Usuario)) == 1


def test_el_enlace_solo_sirve_una_vez(cliente, correos):
    token = pedir_enlace(cliente, correos)
    assert cliente.post("/acceso/verificar", json={"token": token}).status_code == 204
    assert cliente.post("/acceso/verificar", json={"token": token}).status_code == 400


def test_al_entrar_caducan_los_otros_enlaces(cliente, correos):
    primero = pedir_enlace(cliente, correos)
    segundo = pedir_enlace(cliente, correos)
    assert cliente.post("/acceso/verificar", json={"token": segundo}).status_code == 204
    assert cliente.post("/acceso/verificar", json={"token": primero}).status_code == 400


def test_enlace_caducado(cliente, correos, db):
    token = pedir_enlace(cliente, correos)
    db.execute(update(TokenAcceso).values(expira=datetime.now(UTC) - timedelta(seconds=1)))
    assert cliente.post("/acceso/verificar", json={"token": token}).status_code == 400


def test_token_inventado(cliente):
    assert cliente.post("/acceso/verificar", json={"token": "no-existe"}).status_code == 400


def test_limite_de_enlaces_por_hora(cliente, correos):
    for _ in range(5):
        assert cliente.post("/acceso/enlace", json={"email": "ana@example.com"}).status_code == 202
    r = cliente.post("/acceso/enlace", json={"email": "ana@example.com"})
    assert r.status_code == 429
    assert len(correos) == 5  # el sexto no se envía
    # El límite es por correo: otra persona puede pedir el suyo.
    assert cliente.post("/acceso/enlace", json={"email": "luis@example.com"}).status_code == 202


def test_si_falla_el_correo_no_queda_token(cliente, db, monkeypatch):
    def fallar(_):
        raise correo.ErrorCorreo

    monkeypatch.setattr(correo, "enviar", fallar)
    r = cliente.post("/acceso/enlace", json={"email": "ana@example.com"})
    assert r.status_code == 503
    assert db.scalar(select(func.count()).select_from(TokenAcceso)) == 0


def test_cerrar_sesion_en_todos_los_dispositivos(cliente, correos, db):
    assert entrar(cliente, correos).status_code == 204
    movil = TestClient(app, headers={"Origin": WEB})
    token = pedir_enlace(cliente, correos)
    assert movil.post("/acceso/verificar", json={"token": token}).status_code == 204
    assert movil.get("/perfil").status_code == 200

    assert cliente.post("/acceso/cerrar-todas").status_code == 204
    assert movil.get("/perfil").status_code == 401
    assert cliente.get("/perfil").status_code == 401


def test_borrar_cuenta(cliente, correos, db):
    assert entrar(cliente, correos).status_code == 204
    assert cliente.delete("/perfil").status_code == 204
    assert cliente.get("/perfil").status_code == 401
    assert db.scalar(select(func.count()).select_from(Usuario)) == 0
    assert db.scalar(select(func.count()).select_from(Sesion)) == 0  # ON DELETE CASCADE


def test_sesion_caducada(cliente, correos, db):
    assert entrar(cliente, correos).status_code == 204
    db.execute(update(Sesion).values(expira=datetime.now(UTC) - timedelta(seconds=1)))
    assert cliente.get("/perfil").status_code == 401
