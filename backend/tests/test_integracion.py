"""API y servicios contra la base de datos de pruebas (ver conftest.py)."""

import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from sqlalchemy import func, select

from app.domain.modelos import ProductoFeed as Producto
from app.domain.motor import MOTOR_VERSION
from app.models import (
    Evento,
    ExplicacionCache,
    Feedback,
    Importacion,
    Oferta,
    PrecioHistorico,
    RecClick,
    Recomendacion,
    RecShown,
    RevisionPendiente,
    Sku,
    Tienda,
)
from app.services import explicaciones, importacion

CASOS = json.loads((Path(__file__).parent / "datos" / "motor_casos.json").read_text("utf-8"))

PERFIL = {
    "camino": "cambio",
    "exp": "gt2",
    "frec": "2-3",
    "estilo": "potencia",
    "mol": "no",
    "edad": "adulto",
    "ppto": "max",
}


# --- Catálogo -------------------------------------------------------------------------------


def test_exportar_catalogo_en_formato_del_frontend(cliente, catalogo):
    datos = cliente.get("/internas/catalogo").json()
    ejemplo = json.loads(
        (Path(__file__).parents[1] / "app" / "semillas" / "catalogo_ejemplo.json").read_text(
            "utf-8"
        )
    )
    assert len(datos["palas"]) == len(ejemplo["palas"])
    pala = next(p for p in datos["palas"] if p["slug"] == ejemplo["palas"][0]["slug"])
    esperada = ejemplo["palas"][0]
    for campo in ("id", "nombre", "marca", "forma", "balance", "peso", "dureza", "nivel"):
        assert pala[campo] == esperada[campo], campo
    assert {o["id"] for o in pala["ofertas"]} == {o["id"] for o in esperada["ofertas"]}
    assert pala["historico"][0]["hace"] == 90
    assert pala["historico"][-1]["precio"] == min(
        o["precio"] for o in esperada["ofertas"] if o["disponibilidad"] != "agotada"
    )


# --- Recomendación ------------------------------------------------------------------------------


@pytest.mark.parametrize("caso", CASOS[::9], ids=lambda c: json.dumps(c["respuestas"]))
def test_recomendacion_igual_que_en_el_navegador(cliente, catalogo, caso):
    perfil = dict(caso["respuestas"])
    if caso["salud"]:
        perfil["salud"] = {**caso["salud"], "consentimiento": True}
    respuesta = cliente.post("/recomendaciones", json=perfil)
    assert respuesta.status_code == 201, respuesta.text
    datos = respuesta.json()
    esperado = caso["resultado"]
    assert datos["titular"] == esperado["titular"]
    assert datos["mejor"]["slug"] == esperado["mejor"]
    assert [a["slug"] for a in datos["alternativas"]] == [
        a["slug"] for a in esperado["alternativas"]
    ]
    assert datos["motivos"] == esperado["motivos"]
    assert datos["nota"] == esperado["nota"]


def test_recomendacion_se_guarda_sin_datos_de_salud(cliente, catalogo):
    perfil = {
        **PERFIL,
        "mol": "si",
        "salud": {"zona": "Codo", "momento": "Casi siempre", "consentimiento": True},
    }
    datos = cliente.post("/recomendaciones", json=perfil).json()
    rec = catalogo.get(Recomendacion, datos["id"])
    assert "mol" not in rec.perfil and "salud" not in rec.perfil
    assert rec.perfil["estilo"] == "potencia"
    assert rec.versiones["motor"] == MOTOR_VERSION
    posiciones = catalogo.scalars(
        select(RecShown.posicion).where(RecShown.recomendacion_id == rec.id)
    ).all()
    assert sorted(posiciones) == list(range(1, len(datos["alternativas"]) + 2))


def test_sin_palas_en_el_presupuesto_da_404(cliente, catalogo):
    catalogo.execute(Oferta.__table__.update().values(precio=Decimal("999")))
    perfil = {**PERFIL, "ppto": "80"}
    assert cliente.post("/recomendaciones", json=perfil).status_code == 404


# --- Explicación -----------------------------------------------------------------------------


class ProveedorFalso:
    def __init__(self, texto: str) -> None:
        self.texto = texto
        self.llamadas = 0

    def explicar(self, hechos: str) -> str | None:
        assert "molest" not in hechos.lower()  # nunca se envían datos de salud
        self.llamadas += 1
        return self.texto


def test_explicacion_con_plantilla_sin_clave(cliente, catalogo, monkeypatch):
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: None)
    datos = cliente.post("/recomendaciones", json=PERFIL).json()
    texto = cliente.get(f"/recomendaciones/{datos['id']}/explicacion").json()["texto"]
    assert datos["mejor"]["nombre"] in texto


def test_explicacion_con_ia_se_cachea(cliente, catalogo, monkeypatch):
    datos = cliente.post("/recomendaciones", json=PERFIL).json()
    falso = ProveedorFalso(f"La {datos['mejor']['nombre']} te encaja porque buscas pegada.")
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: falso)
    for _ in range(2):
        r = cliente.get(f"/recomendaciones/{datos['id']}/explicacion")
        assert r.json()["texto"] == falso.texto
    assert falso.llamadas == 1
    assert catalogo.scalar(select(func.count()).select_from(ExplicacionCache)) == 1


def test_explicacion_de_la_ia_que_no_nombra_la_pala_se_descarta(cliente, catalogo, monkeypatch):
    datos = cliente.post("/recomendaciones", json=PERFIL).json()
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: ProveedorFalso("Texto sin la pala."))
    texto = cliente.get(f"/recomendaciones/{datos['id']}/explicacion").json()["texto"]
    assert datos["mejor"]["nombre"] in texto  # plantilla


def test_explicacion_de_recomendacion_inexistente(cliente, catalogo):
    assert cliente.get("/recomendaciones/999999/explicacion").status_code == 404


# --- Valoración y eventos ----------------------------------------------------------------------


def test_valoracion(cliente, catalogo):
    datos = cliente.post("/recomendaciones", json=PERFIL).json()
    r = cliente.post(f"/recomendaciones/{datos['id']}/valoracion", json={"puntuacion": 4})
    assert r.status_code == 204
    assert catalogo.scalar(select(Feedback.puntuacion)) == 4
    assert (
        cliente.post("/recomendaciones/999999/valoracion", json={"puntuacion": 4}).status_code
        == 404
    )


def test_evento_sin_datos_de_salud(cliente, db):
    datos = {"util": True, "mol": "si", "zona": "Codo"}
    assert cliente.post("/eventos", json={"tipo": "prueba", "datos": datos}).status_code == 202
    assert db.scalar(select(Evento.datos).where(Evento.tipo == "prueba")) == {"util": True}


# --- Salida a tienda ---------------------------------------------------------------------------


def test_salida_a_tienda_con_enlace_de_afiliado(cliente, catalogo):
    oferta = catalogo.get(Oferta, 101)
    oferta.tienda.plantilla_enlace = "https://red.example/go?aff={id_afiliado}&ref={subid}&u={url}"
    oferta.tienda.id_afiliado = "777"
    catalogo.flush()
    datos = cliente.post("/recomendaciones", json=PERFIL).json()

    r = cliente.get(f"/tienda/101?rec={datos['id']}&pos=1", follow_redirects=False)
    assert r.status_code == 307
    destino = parse_qs(urlparse(r.headers["location"]).query)
    clic = catalogo.scalar(select(RecClick).order_by(RecClick.id.desc()))
    assert destino["ref"] == [str(clic.id)]
    assert destino["aff"] == ["777"]
    assert destino["u"] == [oferta.url]
    assert (clic.recomendacion_id, clic.posicion, clic.origen) == (datos["id"], 1, "recomendacion")


def test_salida_desde_la_ficha_sin_recomendacion(cliente, catalogo):
    r = cliente.get("/tienda/101", follow_redirects=False)
    assert r.status_code == 307
    clic = catalogo.scalar(select(RecClick).order_by(RecClick.id.desc()))
    assert (clic.recomendacion_id, clic.origen) == (None, "ficha")
    assert cliente.get("/tienda/999999", follow_redirects=False).status_code == 404


# --- Importación de feeds ----------------------------------------------------------------------


def _producto(referencia, precio="100", ean=None, titulo="Pala cualquiera", disponible=True):
    return Producto(
        referencia=referencia,
        titulo=titulo,
        precio=Decimal(precio),
        url=f"https://tienda.example/{referencia}",
        disponible=disponible,
        ean=ean,
    )


def test_importacion_de_un_feed(catalogo):
    db = catalogo
    tienda = db.get(Oferta, 101).tienda
    # La oferta 101 ya es de esta tienda: se reconoce por su referencia.
    db.get(Oferta, 101).referencia = "ref-101"
    # Un SKU con EAN que la tienda todavía no vendía.
    sku_ean = db.scalar(select(Sku).where(Sku.modelo_id == 2))
    sku_ean.ean = "8435000000002"
    db.flush()
    otras = db.scalars(select(Oferta).where(Oferta.tienda_id == tienda.id, Oferta.id != 101)).all()
    for i, o in enumerate(otras):
        o.referencia = f"vieja-{i}"
    db.flush()

    precio_101 = db.get(Oferta, 101).precio
    productos = [
        _producto("ref-101", str(precio_101 - 5)),  # baja el precio
        _producto("nuevo-ean", "80", ean="8435000000002"),
        _producto("desconocida", "50", titulo="Pala que no existe"),
        Producto("sin-precio", "Pala", None, "https://tienda.example/x", True),
    ]
    # Las ofertas «vieja-*» no vienen en el feed: tienen que pasar a agotadas.
    resumen = importacion.importar_tienda(db, tienda, productos)

    assert resumen.estado == "correcta"
    assert db.get(Oferta, 101).precio == precio_101 - 5
    assert (
        db.scalar(
            select(func.count()).where(
                PrecioHistorico.oferta_id == 101, PrecioHistorico.precio == precio_101 - 5
            )
        )
        == 1
    )
    nueva = db.scalar(select(Oferta).where(Oferta.referencia == "nuevo-ean"))
    assert nueva is not None and nueva.sku_id == sku_ean.id
    assert resumen.a_revision == 1 and resumen.incompletos == 1
    assert all(db.get(Oferta, o.id).disponibilidad == "agotada" for o in otras)
    assert db.scalar(select(func.count()).select_from(RevisionPendiente)) == 1

    # Al día siguiente: la misma pala desconocida no duplica la revisión pendiente,
    # y un cambio de precio extremo no se publica.
    precio_hoy = db.get(Oferta, 101).precio
    segundo = importacion.importar_tienda(
        db,
        tienda,
        [
            _producto("ref-101", str(precio_hoy * 3)),
            _producto("desconocida", "50"),
            _producto("nuevo-ean", "80", ean="8435000000002"),
        ],
    )
    assert segundo.precio_anomalo == 1
    assert db.get(Oferta, 101).precio == precio_hoy
    motivos = db.scalars(select(RevisionPendiente.motivo)).all()
    assert sorted(motivos) == ["pala_nueva", "precio_anomalo"]


def test_feed_mucho_mas_pequeno_que_el_anterior_se_descarta(db):
    tienda = Tienda(nombre="Tienda de prueba", dominios=[])
    db.add(tienda)
    db.flush()
    db.add(Importacion(tienda_id=tienda.id, productos_recibidos=100, estado="correcta"))
    db.flush()
    resumen = importacion.importar_tienda(db, tienda, [_producto("a")])
    assert resumen.estado == "descartada"
