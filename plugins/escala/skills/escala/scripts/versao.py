#!/usr/bin/env python3
"""Mostra a versao instalada e avisa se ha uma mais nova no catalogo ja baixado."""
import json, os, sys
from pathlib import Path

AQUI = Path(__file__).resolve()


def ler_versao(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8")).get("version", "")
    except Exception:
        return ""


def tupla(v):
    try:
        return tuple(int(x) for x in v.split("."))
    except Exception:
        return (0,)


def main():
    instalada = ler_versao(AQUI.parents[3] / ".claude-plugin" / "plugin.json")
    catalogo = ""
    cat = Path(os.path.expanduser("~/.claude/plugins/marketplaces/legacy-mentoring/plugins/escala/.claude-plugin/plugin.json"))
    if cat.exists():
        catalogo = ler_versao(cat)
    print(f"INSTALADA: {instalada}")
    if catalogo:
        print(f"CATALOGO: {catalogo}")
        if tupla(catalogo) > tupla(instalada):
            print("ATUALIZACAO_DISPONIVEL")


if __name__ == "__main__":
    main()
