#!/usr/bin/env python3
"""Cérebro: memória que aprende sozinha a cada mineração.

Guarda em ~/.lowticket/cerebro.json o que a ferramenta foi descobrindo:
- domínios e plataformas que aparecem como oferta de verdade (passam a ser reconhecidos sozinhos)
- páginas que vivem escalando (aparecem em várias minerações / crescendo)
- quais palavras-chave rendem mais ofertas por nicho/país

Roda automático depois de cada mineração (aprender) e tem um resumo (resumo).

  python3 cerebro.py aprender --pasta <pasta_mineracao>
  python3 cerebro.py resumo [--pais BR]
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from comum import DADOS, _dominio_base

ARQ = DADOS / "cerebro.json"
MIN_PARA_APRENDER_DOMINIO = 3   # domínio visto como oferta em N minerações distintas → vira "conhecido"


def _base():
    return {"versao": 1, "mineracoes": 0, "atualizado": "", "dominios": {}, "plataformas": {},
            "paginas": {}, "palavras": {}, "dominios_oferta": [], "vistos_mineracao": {}}


def carregar():
    if ARQ.exists():
        try:
            d = json.loads(ARQ.read_text(encoding="utf-8"))
            for k, v in _base().items():
                d.setdefault(k, v)
            return d
        except Exception:
            return _base()
    return _base()


def salvar(c):
    DADOS.mkdir(parents=True, exist_ok=True)
    c["atualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ARQ.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def dominio(link):
    try:
        host = urlparse(link).netloc.lower()
        return _dominio_base(link)[0].replace("www.", "") or host
    except Exception:
        return ""


def info_pasta(nome):
    # {data}_{modo}_{pais}_{nicho}_{slug}
    p = nome.split("_")
    modo = p[1] if len(p) > 1 else "?"
    pais = p[2] if len(p) > 2 else "?"
    nicho = p[3] if len(p) > 3 else "?"
    slug = "_".join(p[4:]) if len(p) > 4 else ""
    return modo, pais, nicho, slug


def aprender(pasta):
    pasta = Path(pasta).expanduser()
    rk = pasta / "ranking.csv"
    if not rk.exists():
        return None
    modo, pais, nicho, slug = info_pasta(pasta.name)
    with open(rk, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    if not linhas:
        return None
    c = carregar()
    if pasta.name in c["vistos_mineracao"]:          # não aprende duas vezes a mesma pasta
        return c
    c["vistos_mineracao"][pasta.name] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    c["mineracoes"] += 1
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    doms_desta = set()
    for r in linhas:
        # plataforma
        plat = (r.get("plataforma") or "").strip()
        if plat:
            for nome_plat in [p.strip() for p in plat.split(",") if p.strip()]:
                c["plataformas"][nome_plat] = c["plataformas"].get(nome_plat, 0) + 1
        # domínios da oferta
        for campo in ("landing", "dominios"):
            for pedaco in (r.get(campo) or "").split(","):
                d = dominio(pedaco.strip()) if "/" in pedaco or "." in pedaco else pedaco.strip()
                if not d or "." not in d:
                    continue
                doms_desta.add(d)
        # página recorrente
        pid = (r.get("page_id") or "").strip()
        if pid:
            reg = c["paginas"].setdefault(pid, {"nome": r.get("pagina"), "aparicoes": 0, "max_ativos": 0,
                                                "primeira": hoje, "nichos": [], "pais": pais})
            reg["nome"] = r.get("pagina") or reg["nome"]
            reg["aparicoes"] += 1
            reg["ultima"] = hoje
            try:
                reg["max_ativos"] = max(reg["max_ativos"], int(r.get("ativos_pagina") or 0))
            except ValueError:
                pass
            if nicho not in reg["nichos"]:
                reg["nichos"].append(nicho)
    # conta domínios (vistos / como oferta) e aprende os recorrentes
    for d in doms_desta:
        reg = c["dominios"].setdefault(d, {"minas": 0})
        reg["minas"] += 1
        if reg["minas"] >= MIN_PARA_APRENDER_DOMINIO and d not in c["dominios_oferta"]:
            c["dominios_oferta"].append(d)

    # desempenho da palavra-chave (por nicho/país)
    chave = f"{slug}|{nicho}|{pais}"
    pw = c["palavras"].setdefault(chave, {"buscas": 0, "ofertas_total": 0, "melhor_ativos": 0})
    pw["buscas"] += 1
    pw["ofertas_total"] += len(linhas)
    pw["melhor_ativos"] = max(pw["melhor_ativos"], max((int(r.get("ativos_pagina") or 0) for r in linhas), default=0))

    salvar(c)
    return c


def resumo(pais=None):
    c = carregar()
    paginas = [{"page_id": k, **v} for k, v in c["paginas"].items()]
    if pais:
        paginas = [p for p in paginas if p.get("pais") == pais]
    recorrentes = sorted(paginas, key=lambda p: (p.get("aparicoes", 0), p.get("max_ativos", 0)), reverse=True)[:15]
    plataformas = sorted(c["plataformas"].items(), key=lambda x: x[1], reverse=True)[:12]
    palavras = sorted(c["palavras"].items(),
                      key=lambda x: (x[1]["melhor_ativos"], x[1]["ofertas_total"]), reverse=True)[:12]
    out = {
        "mineracoes_aprendidas": c["mineracoes"],
        "paginas_conhecidas": len(c["paginas"]),
        "dominios_oferta_aprendidos": len(c["dominios_oferta"]),
        "paginas_recorrentes": [{"pagina": p.get("nome"), "aparicoes": p.get("aparicoes"),
                                 "max_ativos": p.get("max_ativos"), "nichos": p.get("nichos"),
                                 "page_id": p.get("page_id")} for p in recorrentes],
        "plataformas_mais_vistas": [{"plataforma": k, "vezes": v} for k, v in plataformas],
        "palavras_que_mais_rendem": [{"busca": k.split("|")[0], "nicho": k.split("|")[1], "pais": k.split("|")[2],
                                      "melhor_ativos": v["melhor_ativos"], "ofertas": v["ofertas_total"]}
                                     for k, v in palavras],
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("aprender"); a.add_argument("--pasta", required=True)
    r = sub.add_parser("resumo"); r.add_argument("--pais", default="")
    args = ap.parse_args()
    if args.cmd == "aprender":
        c = aprender(args.pasta)
        if c is None:
            print("SEM_DADOS: nada para aprender nesta pasta.")
            sys.exit(3)
        print(f"APRENDIDO: {c['mineracoes']} minerações no total · {len(c['paginas'])} páginas conhecidas · "
              f"{len(c['dominios_oferta'])} domínios de oferta aprendidos")
    elif args.cmd == "resumo":
        print(json.dumps(resumo(args.pais or None), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
