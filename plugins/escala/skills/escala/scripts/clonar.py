#!/usr/bin/env python3
"""Opcao 'Clonar oferta': cria a ficha do produto ja pre-preenchida a partir de uma
oferta minerada (analise), para ir direto ao entregavel + pagina + criativos.

Nao copia a copy do concorrente: pre-enche so dados (preco, plataforma, nicho, cores)
e guarda as copies de referencia para o Claude se inspirar no ANGULO, com palavras proprias.

  python3 clonar.py --pasta <pasta_mineracao> --pagina "Nome" --nome "Meu Produto"
  python3 clonar.py --ultima --pagina "Nome" --nome "Meu Produto"
"""
import argparse
import json
import sys
from pathlib import Path

import analisar as A
from comum import carregar_config
from produtos import MODELO_PRODUTO, pasta_produtos, slugify

CORES_NICHO = {
    "saude": {"primaria": "#2f8a55", "escuro": "#15372a", "creme": "#f4f2ec"},
    "emagrecimento": {"primaria": "#2f8a55", "escuro": "#15372a", "creme": "#f4f2ec"},
    "culinaria": {"primaria": "#d9622b", "escuro": "#3a1d12", "creme": "#f7f1ea"},
    "beleza": {"primaria": "#c43b7a", "escuro": "#361226", "creme": "#f7eef3"},
    "educacao": {"primaria": "#2f6fd0", "escuro": "#13233f", "creme": "#eef2f8"},
    "renda": {"primaria": "#1f9d57", "escuro": "#0f2a1c", "creme": "#eef5f0"},
    "esoterico": {"primaria": "#7c3aed", "escuro": "#241244", "creme": "#f1edf8"},
    "artesanato": {"primaria": "#c9842b", "escuro": "#3a2a12", "creme": "#f7f2e8"},
    "design": {"primaria": "#6d28d9", "escuro": "#1f1138", "creme": "#f1eef8"},
}


def preco_num(txt):
    try:
        return float(str(txt).replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
    except Exception:
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta")
    ap.add_argument("--ultima", action="store_true")
    ap.add_argument("--pagina", required=True)
    ap.add_argument("--nome", required=True, help="nome do SEU produto (não o do concorrente)")
    a = ap.parse_args()
    cfg, _ = carregar_config()

    if a.pasta:
        pasta = Path(a.pasta).expanduser()
    else:
        todas = A.pastas_mineracao(cfg)
        if not todas:
            print("SEM_MINERACAO: rode a opção 2 antes.")
            sys.exit(3)
        pasta = todas[-1]
    anuncios = json.loads((pasta / "anuncios.json").read_text(encoding="utf-8"))
    import csv
    ranking = []
    if (pasta / "ranking.csv").exists():
        with open(pasta / "ranking.csv", encoding="utf-8") as f:
            ranking = list(csv.DictReader(f))
    cfg["_modo"] = "nutra" if "_nutra_" in pasta.name else "lowticket"
    res = A.analisar_pagina(anuncios, ranking, a.pagina, cfg)
    if not res:
        print(f"PAGINA_NAO_ENCONTRADA: '{a.pagina}' não está nesta mineração.")
        sys.exit(3)

    m = res["metricas"]
    # nicho a partir do nome da pasta (…_lowticket_BR_<nicho>_… ou _nutra_DE_<cat>_…)
    partes = pasta.name.split("_")
    nicho = partes[4] if len(partes) > 4 else "geral"
    precos = [preco_num(p) for p in m.get("precos_na_copy", []) if preco_num(p) > 0]
    low = sorted([p for p in precos if cfg["preco_min"] <= p <= cfg["preco_max"]])
    preco = low[0] if low else (min(precos) if precos else 0)
    ancora = max(precos) if precos and max(precos) > preco else 0

    slug = slugify(a.nome)
    base = pasta_produtos() / slug
    base.mkdir(parents=True, exist_ok=True)
    prod = dict(MODELO_PRODUTO)
    prod.update({
        "nome": a.nome, "slug": slug, "modo": cfg["_modo"], "nicho": nicho,
        "preco": preco, "preco_ancora": ancora,
        "checkout": m.get("plataforma", ""),
        "cores": CORES_NICHO.get(nicho, MODELO_PRODUTO["cores"]),
        "referencias": [{"pagina": res["pagina"], "landing": m.get("landing", ""),
                         "tipo": m.get("tipo_provavel", ""), "anuncio": res.get("link_biblioteca", ""),
                         "copies_angulo": [c.get("copy", "")[:500] for c in res.get("copies_top", [])]}],
        "analise": {"nota": res["nota_final"], "veredito": res["veredito"],
                    "dias_rodando": m.get("dias_rodando_max"), "ativos": m.get("anuncios_ativos"),
                    "concorrentes": m.get("concorrentes_parecidos")},
    })
    (base / "produto.json").write_text(json.dumps(prod, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"CLONADO: {base / 'produto.json'}")
    print(f"SLUG: {slug}")
    print(json.dumps({"nicho": nicho, "preco": preco, "preco_ancora": ancora,
                      "plataforma": m.get("plataforma", ""), "nota": res["nota_final"],
                      "veredito": res["veredito"], "landing_referencia": m.get("landing", ""),
                      "tipo_referencia": m.get("tipo_provavel", "")}, ensure_ascii=False, indent=1))
    print("FALTA_PREENCHER: promessa, publico, dor_principal, mecanismo, order_bumps, bonus "
          "(o Claude completa e depois gera conteudo.json, funil.json e criativos).")


if __name__ == "__main__":
    main()
