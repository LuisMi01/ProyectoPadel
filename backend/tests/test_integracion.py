"""API y servicios contra la base de datos de pruebas (ver conftest.py)."""

import json
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from sqlalchemy import func, select

from app.adapters.catalogo_sql import RepositorioCatalogoSQL
from app.domain.modelos import ProductoFeed as Producto
from app.domain.modelos import Respuestas, Salud
from app.domain.motor import recomendar
from app.domain.puertos import ExplicacionFallida
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
from app.services import enlaces, explicaciones, fichas, importacion, recomendacion

PERFIL = {
    "camino": "cambio",
    "exp": "gt2",
    "frec": "2-3",
    "estilo": "potencia",
    "edad": "adulto",
    "ppto": "max",
}


def _registrar(cliente, db, perfil=PERFIL, salud: Salud | None = None) -> dict:
    """Hace lo que la web: calcula la recomendación y manda a la API lo que ha enseñado."""
    respuestas = Respuestas(**perfil, mol="si" if salud else "no")
    res = recomendar(respuestas, salud, RepositorioCatalogoSQL(db).palas())
    ids = [res.mejor.id, *(a.pala.id for a in res.alternativas)]
    respuesta = cliente.post("/recomendaciones", json={**perfil, "palas": ids})
    assert respuesta.status_code == 201, respuesta.text
    return {**respuesta.json(), "palas": ids, "mejor": res.mejor.nombre}


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


def test_se_guarda_lo_que_enseno_el_navegador_sin_datos_de_salud(cliente, catalogo):
    # Con molestias, el navegador enseña otras palas; a la API solo le llegan las palas.
    datos = _registrar(cliente, catalogo, salud=Salud("Codo", "Casi siempre"))
    sin_molestias = recomendar(Respuestas(**PERFIL), None, RepositorioCatalogoSQL(catalogo).palas())
    assert datos["palas"][0] != sin_molestias.mejor.id

    rec = catalogo.get(Recomendacion, datos["id"])
    assert rec.perfil == PERFIL
    assert rec.versiones == {"calculada_en": "navegador"}
    enseñadas = catalogo.scalars(
        select(RecShown.modelo_id)
        .where(RecShown.recomendacion_id == rec.id)
        .order_by(RecShown.posicion)
    ).all()
    assert enseñadas == datos["palas"]


def test_pala_que_no_esta_en_el_catalogo_da_422(cliente, catalogo):
    respuesta = cliente.post("/recomendaciones", json={**PERFIL, "palas": [999999]})
    assert respuesta.status_code == 422


# --- Explicación -----------------------------------------------------------------------------


class ProveedorFalso:
    def __init__(self, texto: str) -> None:
        self.texto = texto
        self.llamadas = 0

    def explicar(self, hechos: str) -> str | None:
        assert "molest" not in hechos.lower()  # nunca se envían datos de salud
        self.llamadas += 1
        return self.texto

    def redactar(self, hechos: str) -> Iterator[str]:
        texto = self.explicar(hechos) or ""
        mitad = len(texto) // 2
        yield texto[:mitad]
        yield texto[mitad:]


def test_explicacion_con_plantilla_sin_clave(cliente, catalogo, monkeypatch):
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: None)
    datos = _registrar(cliente, catalogo)
    texto = cliente.get(f"/recomendaciones/{datos['id']}/explicacion").json()["texto"]
    assert datos["mejor"] in texto


def test_explicacion_con_ia_se_cachea(cliente, catalogo, monkeypatch):
    datos = _registrar(cliente, catalogo)
    falso = ProveedorFalso(f"La {datos['mejor']} te encaja porque buscas pegada.")
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: falso)
    for _ in range(2):
        r = cliente.get(f"/recomendaciones/{datos['id']}/explicacion")
        assert r.json()["texto"] == falso.texto
    assert falso.llamadas == 1
    assert catalogo.scalar(select(func.count()).select_from(ExplicacionCache)) == 1


def test_explicacion_de_la_ia_que_no_nombra_la_pala_se_descarta(cliente, catalogo, monkeypatch):
    datos = _registrar(cliente, catalogo)
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: ProveedorFalso("Texto sin la pala."))
    texto = cliente.get(f"/recomendaciones/{datos['id']}/explicacion").json()["texto"]
    assert datos["mejor"] in texto  # plantilla


def _eventos(cliente, recomendacion_id: int) -> list[tuple[str, dict]]:
    respuesta = cliente.get(f"/recomendaciones/{recomendacion_id}/explicacion/flujo")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/event-stream")
    eventos = []
    for bloque in respuesta.text.strip().split("\n\n"):
        evento, datos = (linea.split(": ", 1)[1] for linea in bloque.split("\n"))
        eventos.append((evento, json.loads(datos)))
    return eventos


def test_explicacion_en_flujo_con_ia(cliente, catalogo, monkeypatch):
    datos = _registrar(cliente, catalogo)
    falso = ProveedorFalso(f"La {datos['mejor']} te encaja porque buscas pegada.")
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: falso)

    eventos = _eventos(cliente, datos["id"])
    assert [e for e, _ in eventos] == ["texto", "texto", "fin"]
    assert "".join(d["t"] for e, d in eventos if e == "texto") == falso.texto
    assert eventos[-1][1] == {"texto": falso.texto, "origen": "ia"}
    # La segunda vez sale de la caché, entera y sin llamar a la IA.
    assert _eventos(cliente, datos["id"]) == [("fin", {"texto": falso.texto, "origen": "cache"})]
    assert falso.llamadas == 1


def test_explicacion_en_flujo_que_no_vale_acaba_en_plantilla(cliente, catalogo, monkeypatch):
    datos = _registrar(cliente, catalogo)
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: ProveedorFalso("Texto sin la pala."))
    fin = _eventos(cliente, datos["id"])[-1]
    assert fin[0] == "fin" and fin[1]["origen"] == "plantilla"
    assert datos["mejor"] in fin[1]["texto"]
    assert catalogo.scalar(select(func.count()).select_from(ExplicacionCache)) == 0


def test_explicacion_en_flujo_cortada_acaba_en_plantilla(cliente, catalogo, monkeypatch):
    class ProveedorQueSeCorta(ProveedorFalso):
        def redactar(self, hechos: str) -> Iterator[str]:
            yield "La pala que "
            raise ExplicacionFallida

    datos = _registrar(cliente, catalogo)
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: ProveedorQueSeCorta(""))
    eventos = _eventos(cliente, datos["id"])
    assert [e for e, _ in eventos] == ["texto", "fin"]
    assert eventos[-1][1]["origen"] == "plantilla"


def test_explicacion_en_flujo_sin_clave(cliente, catalogo, monkeypatch):
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: None)
    datos = _registrar(cliente, catalogo)
    [(evento, fin)] = _eventos(cliente, datos["id"])
    assert (evento, fin["origen"]) == ("fin", "sin_ia")
    assert datos["mejor"] in fin["texto"]


class ProveedorEco(ProveedorFalso):
    """Nombra la primera pala de los hechos, como haría la IA."""

    def explicar(self, hechos: str) -> str | None:
        super().explicar(hechos)
        return f"La {hechos.split(chr(10) + '1. ')[1].split(' (')[0]} te encaja."


def test_pregenerar_explica_los_perfiles_mas_repetidos(cliente, catalogo, monkeypatch):
    eco = ProveedorEco("")
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: eco)
    repetido = [_registrar(cliente, catalogo) for _ in range(2)]
    _registrar(cliente, catalogo, {**PERFIL, "estilo": "control"})

    resumen = recomendacion.pregenerar_explicaciones(catalogo, dias=7, maximo=1)

    assert resumen == {
        "perfiles": 1,
        "ya_en_cache": 0,
        "generadas": 1,
        "fallidas": 0,
        "tope_alcanzado": "no",
    }
    # Quien pide la explicación de ese perfil la recibe de la caché, sin otra llamada.
    texto = cliente.get(f"/recomendaciones/{repetido[0]['id']}/explicacion").json()["texto"]
    assert repetido[0]["mejor"] in texto
    assert eco.llamadas == 1
    # Al día siguiente, con los mismos precios, no se repite.
    assert recomendacion.pregenerar_explicaciones(catalogo, 7, 1)["ya_en_cache"] == 1
    assert eco.llamadas == 1


def test_pregenerar_sin_clave_de_ia_no_hace_nada(cliente, catalogo, monkeypatch):
    monkeypatch.setattr(explicaciones, "_proveedor", lambda: None)
    _registrar(cliente, catalogo)
    resumen = recomendacion.pregenerar_explicaciones(catalogo, 7, 100)
    assert resumen == {"omitida": "sin clave de IA"}


def test_explicacion_de_recomendacion_inexistente(cliente, catalogo):
    assert cliente.get("/recomendaciones/999999/explicacion").status_code == 404
    assert cliente.get("/recomendaciones/999999/explicacion/flujo").status_code == 404


# --- Valoración y eventos ----------------------------------------------------------------------


def test_valoracion(cliente, catalogo):
    datos = _registrar(cliente, catalogo)
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
    datos = _registrar(cliente, catalogo)

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


# --- Comprobación de enlaces -------------------------------------------------------------------


class ComprobadorFalso:
    def __init__(self, rota: str) -> None:
        self.rota, self.codigo_rota, self.vistas = rota, 404, []

    def codigo(self, url: str) -> int | None:
        self.vistas.append(url)
        return self.codigo_rota if url == self.rota else 200


def _ofertas_publicadas(cliente) -> set[int]:
    catalogo = cliente.get("/internas/catalogo").json()
    return {o["id"] for p in catalogo["palas"] for o in p["ofertas"]}


def test_oferta_sin_pagina_dos_semanas_seguidas_se_oculta(cliente, catalogo):
    oferta = catalogo.get(Oferta, 101)
    oferta.url = "https://tienda.example/pala-retirada"
    catalogo.flush()
    falso = ComprobadorFalso(oferta.url)

    primera = enlaces.comprobar_ofertas(catalogo, falso)
    assert (primera["rotas"], primera["ocultadas"]) == (1, 0)
    assert 101 in _ofertas_publicadas(cliente)  # una semana puede ser un fallo pasajero

    segunda = enlaces.comprobar_ofertas(catalogo, falso)
    assert segunda["ocultadas"] == 1
    assert 101 not in _ofertas_publicadas(cliente)
    assert all(
        101 not in {o.id for o in p.ofertas} for p in RepositorioCatalogoSQL(catalogo).palas()
    )

    # Un bloqueo de la tienda no cuenta como fallo; cuando la página vuelve, la oferta reaparece.
    falso.codigo_rota = 403
    assert enlaces.comprobar_ofertas(catalogo, falso)["dudosas"] == 1
    assert catalogo.get(Oferta, 101).enlace_fallos == 2
    falso.rota = ""
    assert enlaces.comprobar_ofertas(catalogo, falso)["recuperadas"] == 1
    assert 101 in _ofertas_publicadas(cliente)
    # Se comprueba la página del producto, nunca el enlace de afiliado.
    assert all(u.startswith("https://") and "{subid}" not in u for u in falso.vistas)


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


def _tienda(db, nombre: str) -> Tienda:
    tienda = Tienda(nombre=nombre, dominios=[])
    db.add(tienda)
    db.flush()
    return tienda


def test_lo_que_no_es_pala_no_va_a_revision(db):
    tienda = _tienda(db, "Tienda de todo")
    productos = [
        Producto("z1", "Asics Gel Padel Pro", Decimal("90"), "https://t.example/z1", True,
                 categoria="Zapatillas"),
        Producto("p1", "Paletero Zeta Tour", Decimal("40"), "https://t.example/p1", True),
        Producto("n1", "Pala Zeta Rayo 2026", Decimal("199"), "https://t.example/n1", True,
                 categoria="Palas"),
    ]  # fmt: skip
    resumen = importacion.importar_tienda(db, tienda, productos)
    assert (resumen.no_pala, resumen.a_revision) == (2, 1)
    assert db.scalar(select(func.count()).select_from(RevisionPendiente)) == 1


def test_la_misma_pala_nueva_desde_varias_tiendas_se_revisa_una_vez(db):
    def pala(ref: str, titulo: str, ean: str | None = None) -> Producto:
        return Producto(ref, titulo, Decimal("199"), f"https://t.example/{ref}", True, ean=ean)

    primera, segunda = _tienda(db, "Tienda A"), _tienda(db, "Tienda B")
    importacion.importar_tienda(db, primera, [pala("a1", "Pala Zeta Rayo", "8435000000099"),
                                             pala("a2", "Pala Zeta Brisa")])  # fmt: skip
    # Misma pala por EAN (con otro título) y por nombre (sin EAN), y una que sí es distinta.
    resumen = importacion.importar_tienda(
        db, segunda, [pala("b1", "Zeta Rayo 2026", "8435000000099"),
                      pala("b2", "PALA de pádel Zeta Brisa"), pala("b3", "Pala Zeta Trueno")],
    )  # fmt: skip
    assert (resumen.ya_en_revision, resumen.a_revision) == (2, 1)
    assert db.scalar(select(func.count()).select_from(RevisionPendiente)) == 3


# --- Fichas de palas nuevas --------------------------------------------------------------------


class ExtractorFalso:
    def __init__(self, ficha: dict | None) -> None:
        self.ficha, self.textos = ficha, []

    def extraer(self, texto: str) -> dict | None:
        self.textos.append(texto)
        return self.ficha


def test_la_ia_propone_la_ficha_de_las_palas_nuevas(catalogo):
    db = catalogo
    tienda = Tienda(nombre="Tienda con novedades", dominios=[])
    db.add(tienda)
    db.flush()
    nueva = Producto(
        "nov-1", "Pala Zeta Rayo 2026", Decimal("199"), "https://tienda.example/rayo", True,
        marca="Zeta", datos={"descripcion": "Forma diamante, 360-375 g, núcleo EVA Hard"},
    )  # fmt: skip
    importacion.importar_tienda(db, tienda, [nueva])

    falso = ExtractorFalso({"marca": "Zeta", "nombre": "Rayo", "temporada": 1999,
                            "forma": "diamante", "peso_min": 375, "peso_max": 360})  # fmt: skip
    assert fichas.proponer_fichas(db, ExtractorFalso(None), 10) == {
        "pendientes": 1, "propuestas": 0, "fallidas": 1,
    }  # fmt: skip
    assert fichas.proponer_fichas(db, falso, 10)["propuestas"] == 1

    # La IA recibe lo que publica la tienda, también la descripción original.
    assert "Forma diamante, 360-375 g" in falso.textos[0]
    revision = db.scalar(select(RevisionPendiente).where(RevisionPendiente.motivo == "pala_nueva"))
    ficha = revision.propuesta["ficha"]
    assert (ficha["forma"], ficha["peso_min"], ficha["peso_max"]) == ("diamante", 360, 375)
    assert ficha["temporada"] is None  # un año imposible se descarta
    assert revision.estado == "pendiente"  # sigue esperando a que alguien la apruebe
    # Al día siguiente no se vuelve a pedir.
    assert fichas.proponer_fichas(db, falso, 10)["pendientes"] == 0
