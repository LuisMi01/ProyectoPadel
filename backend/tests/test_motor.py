"""El motor de Python da el mismo resultado que el recomendador del frontend.

tests/datos/motor_casos.json tiene casos calculados con frontend/src/lib/recomendador.ts sobre el
catálogo de ejemplo (app/semillas/catalogo_ejemplo.json): respuestas, detalle de salud y resultado.
Si cambian las reglas en un lado, este test obliga a cambiarlas en el otro.
"""

import json
from pathlib import Path

import pytest

from app.adapters.catalogo_json import palas_ejemplo
from app.domain.modelos import Respuestas, Salud
from app.domain.motor import recomendar

CASOS = json.loads((Path(__file__).parent / "datos" / "motor_casos.json").read_text("utf-8"))
CATALOGO = palas_ejemplo()


def _resultado(respuestas: dict, salud: dict | None) -> dict | None:
    detalle = Salud(salud["zona"], salud["momento"]) if salud else None
    res = recomendar(Respuestas(**respuestas), detalle, CATALOGO)
    if res is None:
        return None
    return {
        "titular": res.titular,
        "mejor": res.mejor.slug,
        "afinidad": res.afinidad,
        "motivos": [{"respuesta": m.respuesta, "explicacion": m.explicacion} for m in res.motivos],
        "alternativas": [
            {
                "slug": a.pala.slug,
                "etiqueta": a.etiqueta,
                "ganas": a.ganas,
                "pierdes": a.pierdes,
                "afinidad": a.afinidad,
            }
            for a in res.alternativas
        ],
        "nota": res.nota,
    }


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: json.dumps(c["respuestas"]))
def test_mismo_resultado_que_el_frontend(caso):
    assert _resultado(caso["respuestas"], caso["salud"]) == caso["resultado"]


def test_sin_palas_dentro_del_tope_devuelve_none():
    caras = [p for p in CATALOGO if min(o.precio for o in p.ofertas) > 100]
    assert recomendar(Respuestas(exp="gt2", ppto="100", edad="adulto"), None, caras) is None


@pytest.mark.parametrize("frec", ["1", "2-3", "4+"])
@pytest.mark.parametrize("ppto", ["150", "250", "max"])
def test_con_menos_de_6_meses_nunca_se_recomienda_un_diamante(frec, ppto):
    r = Respuestas(camino="cambio", exp="lt6", frec=frec, estilo="potencia", mol="no",
                   edad="adulto", ppto=ppto)  # fmt: skip
    res = recomendar(r, None, CATALOGO)
    assert res is not None
    assert res.mejor.forma == "lagrima"


def test_junior_solo_recibe_palas_junior():
    res = recomendar(
        Respuestas(camino="primera", exp="nunca", edad="junior", ppto="max"), None, CATALOGO
    )
    assert res is not None
    assert res.mejor.junior
    assert all(a.pala.junior for a in res.alternativas)


def test_con_molestias_hay_nota_y_sin_molestias_no():
    base = {"camino": "cambio", "exp": "gt2", "frec": "2-3", "estilo": "potencia", "edad": "adulto"}
    con = recomendar(
        Respuestas(**base, mol="si", ppto="max"), Salud("Codo", "Casi siempre"), CATALOGO
    )
    sin = recomendar(Respuestas(**base, mol="no", ppto="max"), None, CATALOGO)
    assert con is not None and con.nota
    assert sin is not None and sin.nota is None
    # Con molestias nunca se recomienda un diamante.
    assert con.mejor.forma != "diamante"
