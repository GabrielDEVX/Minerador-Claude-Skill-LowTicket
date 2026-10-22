#!/usr/bin/env python3
"""Versao instalada x versao mais recente no GitHub.

Sem argumentos: mostra INSTALADA, ULTIMA (do GitHub) e, se houver nova, ATUALIZACAO_DISPONIVEL.
Com --curto: imprime uma linha so (OK | DESATUALIZADA <inst> <ult> | OFFLINE), para o run.sh decidir
se deixa minerar.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve()
RAW = ("https://raw.githubusercontent.com/GabrielDEVX/Minerador-Claude-Skill-LowTicket-Nutra/"
       "main/plugins/escala/.claude-plugin/plugin.json")
CMD_ATUALIZAR = "claude plugin marketplace update legacy-mentoring"


def ler_versao(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8")).get("version", "")
    except Exception:
        return ""


def tupla(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0,)


def versao_instalada():
    return ler_versao(AQUI.parents[3] / ".claude-plugin" / "plugin.json")


def versao_github(timeout=6):
    """Versao mais recente no GitHub. '' se nao conseguiu checar (offline)."""
    try:
        req = urllib.request.Request(RAW, headers={"User-Agent": "CentralEscala"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")).get("version", "")
    except Exception:
        return ""


def main():
    curto = "--curto" in sys.argv
    inst = versao_instalada()
    ult = versao_github(timeout=4 if curto else 6)
    if curto:
        if not ult:
            print("OFFLINE")                       # nao deu para checar: nao bloqueia
        elif tupla(ult) > tupla(inst):
            print(f"DESATUALIZADA {inst} {ult}")
        else:
            print("OK")
        return
    print(f"INSTALADA: {inst}")
    if not ult:
        print("SEM_CHECAGEM: nao consegui checar o GitHub agora (sem internet?).")
        return
    print(f"ULTIMA: {ult}")
    if tupla(ult) > tupla(inst):
        print("ATUALIZACAO_DISPONIVEL")
        print(f"COMANDO: {CMD_ATUALIZAR}")
    else:
        print("ATUALIZADA")


if __name__ == "__main__":
    main()
