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


def test_peticion_desde_otra_web_se_rechaza():
    r = client.post(
        "/eventos", json={"tipo": "x"}, headers={"Origin": "https://web-maliciosa.example"}
    )
    assert r.status_code == 403
    # Desde la web pasa el filtro y llega a la validación (422), sin tocar la base de datos.
    permitido = client.post(
        "/recomendaciones", json={"camino": "otro"}, headers={"Origin": "http://localhost:4321"}
    )
    assert permitido.status_code == 422
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


def test_hash_ip_agrupa_ipv6_por_bloque_64():
    from app.services.acceso import hash_ip

    assert hash_ip("2001:db8:1:2::1") == hash_ip("2001:db8:1:2:ffff::9")  # mismo /64
    assert hash_ip("2001:db8:1:2::1") != hash_ip("2001:db8:1:3::1")
    assert hash_ip("203.0.113.1") != hash_ip("203.0.113.2")
    assert hash_ip(None) is None
    assert "203.0.113.1" not in hash_ip("203.0.113.1")


def test_correo_en_consola_fuera_de_local_da_error(monkeypatch):
    """Si en producción se olvida CORREO_MODO=smtp, se nota (503) en vez de fingir el envío."""
    import pytest

    from app.core import correo
    from app.core.config import get_settings

    ajustes = get_settings().model_copy(update={"entorno": "produccion", "correo_modo": "consola"})
    monkeypatch.setattr(correo, "get_settings", lambda: ajustes)
    with pytest.raises(correo.ErrorCorreo):
        correo.enviar(correo.Correo("a@b.es", "s", "enlace secreto", "h"))
