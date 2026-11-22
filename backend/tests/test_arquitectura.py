"""El dominio no depende de frameworks ni de otras capas de la aplicación."""

import ast
from pathlib import Path

DOMINIO = Path(__file__).resolve().parents[1] / "app" / "domain"
PROHIBIDOS = (
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "app.adapters",
    "app.api",
    "app.core",
    "app.db",
    "app.jobs",
    "app.models",
    "app.schemas",
    "app.services",
)


def _importaciones(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.add(nodo.module)
    return nombres


def test_dominio_sin_dependencias_externas():
    archivos = sorted(DOMINIO.glob("*.py"))
    assert archivos
    for archivo in archivos:
        for nombre in _importaciones(archivo):
            assert not nombre.startswith(PROHIBIDOS), f"{archivo.name} importa {nombre}"
