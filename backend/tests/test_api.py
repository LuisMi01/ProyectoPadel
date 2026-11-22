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


def test_peticion_desde_otra_web_se_rechaza():
    r = client.post(
        "/eventos", json={"tipo": "x"}, headers={"Origin": "https://web-maliciosa.example"}
    )
    assert r.status_code == 403
    permitido = client.post(
        "/eventos", json={"tipo": "x"}, headers={"Origin": "http://localhost:4321"}
    )
    assert permitido.status_code == 202
    # Las lecturas no cambian datos: no se filtran por origen.
    assert (
        client.get("/perfil", headers={"Origin": "https://web-maliciosa.example"}).status_code
        == 401
    )


def test_correo_de_acceso_escapa_el_html():
    from app.services.plantillas_correo import enlace_de_acceso

    c = enlace_de_acceso("a@b.es", 'https://x.es/?token=a"b<c', "palaideal", 15)
    assert "token=a&quot;b&lt;c" in c.html and "<c" not in c.html
    assert 'https://x.es/?token=a"b<c' in c.texto and "15 minutos" in c.texto


def test_grupos_de_tareas():
    assert set(GRUPOS) == {"daily", "weekly", "monthly"}


def test_envio_por_smtp(monkeypatch):
    """Con CORREO_MODO=smtp se usa STARTTLS, login y un mensaje con texto y HTML."""
    from pydantic import SecretStr

    from app.core import correo
    from app.core.config import get_settings

    llamadas = []

    class ServidorFalso:
        def __init__(self, host, puerto, timeout):
            llamadas.append(("conectar", host, puerto))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def starttls(self, context):
            llamadas.append(("starttls",))

        def login(self, usuario, clave):
            llamadas.append(("login", usuario, clave))

        def send_message(self, mensaje):
            llamadas.append(("enviar", mensaje))

    ajustes = get_settings().model_copy(
        update={
            "correo_modo": "smtp",
            "smtp_host": "smtp.example.com",
            "smtp_usuario": "api",
            "smtp_password": SecretStr("secreto"),
        }
    )
    monkeypatch.setattr(correo, "get_settings", lambda: ajustes)
    monkeypatch.setattr(correo.smtplib, "SMTP", ServidorFalso)

    correo.enviar(correo.Correo("ana@example.com", "Asunto", "texto plano", "<p>html</p>"))

    assert llamadas[:3] == [
        ("conectar", "smtp.example.com", 587),
        ("starttls",),
        ("login", "api", "secreto"),
    ]
    mensaje = llamadas[3][1]
    assert mensaje["To"] == "ana@example.com" and mensaje["Subject"] == "Asunto"
    tipos = [p.get_content_type() for p in mensaje.iter_parts()]
    assert tipos == ["text/plain", "text/html"]


def test_fallo_smtp_se_convierte_en_error_de_correo(monkeypatch):
    import smtplib

    import pytest

    from app.core import correo
    from app.core.config import get_settings

    def no_conecta(*_a, **_k):
        raise smtplib.SMTPConnectError(421, "no")

    ajustes = get_settings().model_copy(update={"correo_modo": "smtp", "smtp_host": "x"})
    monkeypatch.setattr(correo, "get_settings", lambda: ajustes)
    monkeypatch.setattr(correo.smtplib, "SMTP", no_conecta)
    with pytest.raises(correo.ErrorCorreo):
        correo.enviar(correo.Correo("a@b.es", "s", "t", "h"))
