"""Funciones puras del dominio y de los adaptadores: no necesitan base de datos."""

import gzip
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.adapters.feeds import leer_feed
from app.domain import normalizacion
from app.domain.afiliacion import enlace_afiliado
from app.domain.enlaces import estado_enlace
from app.domain.fichas import MAX_TEXTO, limpiar_ficha, texto_producto
from app.domain.historico import serie_minimos
from app.jobs import periodo
from app.schemas import PerfilEncuesta

# --- Normalización de feeds --------------------------------------------------------------


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("279,95 €", Decimal("279.95")),
        ("1.299,00", Decimal("1299.00")),
        ("1,299.00", Decimal("1299.00")),
        ("279.95", Decimal("279.95")),
        ("1.299", Decimal("1299.00")),
        ("EUR 79.9", Decimal("79.90")),
        (129.95, Decimal("129.95")),
        ("", None),
        ("gratis", None),
        ("0", None),
        (None, None),
    ],
)
def test_precio(entrada, esperado):
    assert normalizacion.precio(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [(None, True), ("in stock", True), ("Agotado", False), ("0", False), ("3", True), (0, False)],
)
def test_disponible(entrada, esperado):
    assert normalizacion.disponible(entrada) is esperado


def test_ean():
    assert normalizacion.ean("8435-1234-5678-9") == "8435123456789"
    assert normalizacion.ean("012345678905") == "0012345678905"  # UPC-12 a EAN-13
    assert normalizacion.ean("abc") is None


def test_parecido():
    assert normalizacion.parecido("Pala BULLPADEL Vertex-04 '25", "Bullpadel Vertex 04 25") > 0.9
    assert normalizacion.parecido("Bullpadel Vertex 04", "Head Delta Pro") < 0.5


@pytest.mark.parametrize(
    ("titulo", "categoria", "esperado"),
    [
        ("Pala Bullpadel Vertex 04", None, True),
        ("Bullpadel Vertex 04 2026", None, True),  # sin la palabra «pala»: ante la duda, pasa
        ("Pala Nox AT10 con funda", None, True),
        ("Paletero Bullpadel Hack", None, False),
        ("Zapatillas Asics Gel Padel", None, False),
        ("Bote de pelotas Head", None, False),
        ("Bullpadel Vertex 04", "Pádel > Palas", True),
        ("Bullpadel Vertex 04", "Palas junior", True),
        ("Protector Bullpadel", "Accesorios > Protectores de pala", False),
        ("Asics Gel", "Zapatillas", False),
    ],
)
def test_parece_pala(titulo, categoria, esperado):
    assert normalizacion.parece_pala(titulo, categoria) is esperado


def test_leer_feed_csv_comprimido_con_punto_y_coma():
    csv = "id;nombre;precio;enlace;ean;stock\n1;Pala A;99,90 €;https://t.es/a;8435123456789;5\n"
    csv += ";Sin referencia;10;https://t.es/x;;1\n"
    campos = {
        "referencia": "id",
        "titulo": "nombre",
        "precio": "precio",
        "url": "enlace",
        "ean": "ean",
        "disponible": "stock",
    }
    productos = leer_feed(gzip.compress(csv.encode()), "csv", campos)
    assert len(productos) == 1
    p = productos[0]
    assert (p.referencia, p.precio, p.url, p.ean, p.disponible) == (
        "1",
        Decimal("99.90"),
        "https://t.es/a",
        "8435123456789",
        True,
    )


def test_leer_feed_json_envuelto():
    contenido = b'{"products": [{"sku": "x1", "name": "Pala X", "price": 120, "inStock": false}]}'
    campos = {"referencia": "sku", "titulo": "name", "precio": "price", "disponible": "inStock"}
    [p] = leer_feed(contenido, "json", campos)
    assert (p.referencia, p.precio, p.disponible, p.url) == ("x1", Decimal("120.00"), False, None)


# --- Enlaces de las ofertas ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [(200, "ok"), (301, "ok"), (404, "rota"), (410, "rota"), (403, "dudosa"), (429, "dudosa"),
     (500, "dudosa"), (None, "dudosa")],
)  # fmt: skip
def test_estado_enlace(codigo, esperado):
    assert estado_enlace(codigo) == esperado


# --- Fichas de palas nuevas --------------------------------------------------------------------


def test_texto_producto_junta_titulo_marca_y_columnas_del_feed():
    datos = {
        "titulo": "Pala Zeta Rayo",
        "marca": "Zeta",
        "original": {"peso": "365 g", "stock": 3, "vacia": " ", "lista": ["no"]},
    }
    assert texto_producto(datos) == "titulo: Pala Zeta Rayo\nmarca: Zeta\npeso: 365 g\nstock: 3"
    assert len(texto_producto({"titulo": "x" * (MAX_TEXTO * 2)})) == MAX_TEXTO


def test_limpiar_ficha_descarta_lo_imposible():
    ficha = limpiar_ficha({"forma": "lagrima", "temporada": 2026, "peso_min": 370, "peso_max": 355})
    assert (ficha["forma"], ficha["temporada"], ficha["peso_min"], ficha["peso_max"]) == (
        "lagrima", 2026, 355, 370,
    )  # fmt: skip
    rara = limpiar_ficha({"temporada": 1890, "peso_min": 36, "peso_max": "365"})
    assert (rara["temporada"], rara["peso_min"], rara["peso_max"]) == (None, None, None)


# --- Afiliación ------------------------------------------------------------------------------


def test_enlace_afiliado_con_plantilla():
    plantilla = "https://red.example/go?aff={id_afiliado}&ref={subid}&u={url}"
    url = enlace_afiliado("https://tienda.es/pala?c=1&d={x}", plantilla, "123", "42")
    assert (
        url
        == "https://red.example/go?aff=123&ref=42&u=https%3A%2F%2Ftienda.es%2Fpala%3Fc%3D1%26d%3D%7Bx%7D"
    )


def test_enlace_afiliado_sin_plantilla_es_la_url():
    assert enlace_afiliado("https://tienda.es/pala", None, None, "42") == "https://tienda.es/pala"


# --- Histórico ------------------------------------------------------------------------------


def test_serie_minimos():
    ahora = datetime(2026, 11, 18, tzinfo=UTC)
    hace = lambda dias: ahora - timedelta(days=dias)  # noqa: E731
    cambios = [
        (hace(200), 1, 140.0),  # antes de la ventana: precio al empezarla
        (hace(60), 2, 130.0),
        (hace(30), 1, 120.0),
        (hace(30), 2, 125.0),  # mismo día: vale el mínimo al final del día
        (hace(10), 1, 120.0),  # sin cambio de mínimo: no añade punto
    ]
    assert serie_minimos(cambios, ahora) == [
        {"hace": 90, "precio": 140.0},
        {"hace": 60, "precio": 130.0},
        {"hace": 30, "precio": 120.0},
    ]


def test_serie_minimos_vacia():
    assert serie_minimos([], datetime.now(UTC)) == []


# --- Cuestionario ------------------------------------------------------------------------------

BASE = {
    "camino": "cambio",
    "exp": "gt2",
    "frec": "2-3",
    "estilo": "mixto",
    "mol": "no",
    "edad": "adulto",
    "ppto": "250",
}


def test_perfil_sin_haber_jugado_no_tiene_frecuencia_ni_estilo():
    perfil = PerfilEncuesta(**{**BASE, "exp": "nunca"})
    assert perfil.frec is None and perfil.estilo is None


@pytest.mark.parametrize("exp", ["lt6", "m6a2", "gt2"])
def test_perfil_exige_frecuencia_y_estilo_si_ya_juega(exp):
    assert PerfilEncuesta(**{**BASE, "exp": exp}).estilo == "mixto"
    with pytest.raises(ValidationError):
        PerfilEncuesta(**{**BASE, "exp": exp, "frec": None})


def test_perfil_salud_solo_con_molestias_y_consentimiento():
    salud = {"zona": "Codo", "momento": "Casi siempre", "consentimiento": True}
    assert PerfilEncuesta(**BASE, salud=salud).salud is None  # mol = no: se descarta
    con = PerfilEncuesta(**{**BASE, "mol": "si"}, salud=salud)
    assert con.salud is not None
    assert "mol" not in con.sin_salud() and "salud" not in con.sin_salud()
    with pytest.raises(ValidationError):
        PerfilEncuesta(**{**BASE, "mol": "si"}, salud={**salud, "consentimiento": False})


# --- Tareas programadas ------------------------------------------------------------------------


def test_periodos():
    dia = datetime(2026, 11, 18, 5, tzinfo=UTC)
    assert periodo("daily", dia) == "2026-11-18"
    assert periodo("weekly", dia) == "2026-W47"
    assert periodo("monthly", dia) == "2026-11"
