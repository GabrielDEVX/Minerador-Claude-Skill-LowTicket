#!/usr/bin/env python3
"""Compara o mesmo mecanismo de nutra em varios paises numa rodada.

Nao refaz a mineracao: le as pastas ja geradas (uma por pais, mesmo mecanismo/categoria)
e monta uma tabela de onde a oferta esta mais quente.

  python3 comparar_nutra.py --pastas pasta_US pasta_DE pasta_FR
"""
import argparse, csv, json, sys
from pathlib import Path


def ler(pasta):
    p = Path(pasta).expanduser()
    linhas = []
    if (p / "ranking.csv").exists():
        with open(p / "ranking.csv", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    pais = next((x for x in p.name.split("_") if len(x) == 2 and x.isalpha()), "?").upper()
    ativos = sum(int(l.get("ativos_pagina") or 0) for l in linhas)
    com_vsl = [l for l in linhas if "VSL" in (l.get("sinais") or "")]
    escala = [l for l in linhas if "ESCALA" in (l.get("sinais") or "")]
    top = max(linhas, key=lambda l: int(l.get("ativos_pagina") or 0), default={})
    return {"pais": pais, "pasta": str(p), "paginas": len(linhas), "paginas_vsl": len(com_vsl),
            "paginas_escala": len(escala), "ativos_total": ativos,
            "top_pagina": top.get("pagina", ""), "top_ativos": top.get("ativos_pagina", ""),
            "top_biblioteca": top.get("link_biblioteca", "")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pastas", nargs="+", required=True)
    a = ap.parse_args()
    linhas = [ler(p) for p in a.pastas]
    linhas.sort(key=lambda r: (r["paginas_escala"], r["ativos_total"]), reverse=True)
    print(json.dumps(linhas, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
