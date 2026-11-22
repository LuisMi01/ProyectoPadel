#!/usr/bin/env python3
"""Genera los agentes de Codex (.codex/agents/*.toml) desde los de Claude Code (.claude/agents/*.md).

La fuente única son los .md: edita solo esos y ejecuta este script.

    python scripts/sincronizar-agentes.py              # regenera .codex/agents
    python scripts/sincronizar-agentes.py --comprobar  # CI: falla si no están al día

Solo usa la biblioteca estándar (Python 3.11+).
"""

import re
import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / ".claude" / "agents"
DESTINO = RAIZ / ".codex" / "agents"
AVISO = "# Generado por scripts/sincronizar-agentes.py desde .claude/agents/{}.md: no editar a mano.\n"


def a_toml(md: Path) -> str:
    texto = md.read_text(encoding="utf-8")
    partes = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not partes:
        sys.exit(f"✗ {md.name}: falta la cabecera --- name/description ---")
    cabecera, cuerpo = partes.groups()
    campos = dict(re.findall(r"^(\w+): (.*)$", cabecera, re.M))
    nombre, descripcion = campos.get("name"), campos.get("description")
    if not nombre or not descripcion:
        sys.exit(f"✗ {md.name}: la cabecera necesita name y description")

    # En Codex la guía del proyecto es AGENTS.md; en Claude Code, CLAUDE.md.
    cuerpo = cuerpo.strip().replace("CLAUDE.md", "AGENTS.md")
    if "'''" in cuerpo:
        sys.exit(f"✗ {md.name}: el cuerpo no puede contener ''' (rompe el TOML)")

    toml = (
        AVISO.format(nombre)
        + f"name = {toml_cadena(nombre)}\n"
        + f"description = {toml_cadena(descripcion)}\n"
        + f"developer_instructions = '''\n{cuerpo}\n'''\n"
    )
    tomllib.loads(toml)  # valida que el resultado es TOML correcto
    return toml


def toml_cadena(valor: str) -> str:
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows no es UTF-8 por defecto
    comprobar = "--comprobar" in sys.argv
    esperados = {f"{md.stem}.toml": a_toml(md) for md in sorted(ORIGEN.glob("*.md"))}
    actuales = {p.name: p.read_text(encoding="utf-8") for p in DESTINO.glob("*.toml")}

    distintos = sorted(n for n, t in esperados.items() if actuales.get(n) != t)
    sobrantes = sorted(set(actuales) - set(esperados))

    if comprobar:
        if distintos or sobrantes:
            for n in distintos:
                print(f"✗ .codex/agents/{n} no coincide con .claude/agents/{n[:-5]}.md")
            for n in sobrantes:
                print(f"✗ .codex/agents/{n} no tiene .md de origen")
            print("Ejecuta: python scripts/sincronizar-agentes.py  y haz commit del resultado.")
            return 1
        print(f"✓ {len(esperados)} agentes sincronizados")
        return 0

    DESTINO.mkdir(parents=True, exist_ok=True)
    for n in distintos:
        (DESTINO / n).write_text(esperados[n], encoding="utf-8", newline="\n")
        print(f"→ .codex/agents/{n}")
    for n in sobrantes:
        (DESTINO / n).unlink()
        print(f"✗ .codex/agents/{n} (borrado: no tiene .md de origen)")
    if not distintos and not sobrantes:
        print("✓ Ya estaban sincronizados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
