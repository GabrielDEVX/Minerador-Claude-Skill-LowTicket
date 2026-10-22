#!/usr/bin/env python3
"""Opção 3: mede uma oferta minerada pelos critérios de escala e dá uma nota objetiva.

Lê a pasta de uma mineração (anuncios.json + ranking.csv) e calcula, para a página escolhida:
dias rodando, anúncios ativos, criativos e variações, preço, plataforma e concorrência
(quantas outras páginas da mesma mineração vendem algo parecido).

  python3 analisar.py --ultima                       # lista as melhores páginas da última mineração
  python3 analisar.py --ultima --pagina "Mariana Oliveira"
  python3 analisar.py --pasta ~/mineracao/2026-10-21_..._pack --pagina 501
"""
import argparse
import csv
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

from comum import _sem_acento, carregar_config, fmt_preco, plataforma, precos

PARADAS = set("""de da do das dos e o a os as um uma para por com sem em no na nos nas que seu sua seus suas voce
mais muito como ja so ate the and for with your you mit und der die das für sie ihre le la les des pour avec vous votre
el los las del con tu""".split())


def pastas_mineracao(cfg):
    base = Path(cfg["pasta_saida"])
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir() and (p / "anuncios.json").exists()], key=lambda p: p.stat().st_mtime)


def palavras_chave(texto):
    ws = re.findall(r"[a-z0-9+]{4,}", _sem_acento(texto))
    return {w for w in ws if w not in PARADAS}


def nota(valor, ruim, otimo):
    """0 a 10, linear entre 'ruim' e 'ótimo'."""
    if otimo == ruim:
        return 10.0
    return round(max(0.0, min(10.0, (valor - ruim) / (otimo - ruim) * 10)), 1)


def analisar_pagina(anuncios, ranking, alvo, cfg):
    def casa(a):
        return alvo in (a.get("page_id"), a.get("pagina")) or _sem_acento(alvo) == _sem_acento(a.get("pagina") or "")
    ads = [a for a in anuncios if casa(a)]
    if not ads:
        return None
    pid = ads[0].get("page_id") or ads[0].get("pagina")
    linha = next((r for r in ranking if r.get("page_id") == pid or r.get("pagina") == ads[0].get("pagina")), {})
    agora = time.time()
    dias = [int((agora - a["inicio_ts"]) / 86400) for a in ads if a.get("inicio_ts")]
    dias_max = max(dias or [0])
    ativos = int(linha.get("ativos_pagina") or 0) or len(ads)
    videos = [a for a in ads if a.get("videos") or a.get("formato") == "VIDEO"]
    variacoes = len(videos) + sum(max(0, int(a.get("duplicados") or 1) - 1) for a in videos)
    duplicados = sum(int(a.get("duplicados") or 1) for a in ads)
    todos_precos = sorted({p for a in ads for p in precos(a.get("texto", "") + " " + a.get("titulo_link", ""))})
    low = [p for p in todos_precos if cfg["preco_min"] <= p <= cfg["preco_max"]]
    plats = sorted({plataforma(a.get("link")) for a in ads} - {""})

    # concorrência: outras páginas da mesma mineração com copy parecida
    chave = Counter()
    for a in ads:
        chave.update(palavras_chave(a.get("texto", "") + " " + a.get("titulo_link", "")))
    principais = {w for w, _ in chave.most_common(12)}
    concorrentes = {}
    for a in anuncios:
        outro = a.get("page_id") or a.get("pagina")
        if outro == pid:
            continue
        comum_ = principais & palavras_chave(a.get("texto", "") + " " + a.get("titulo_link", ""))
        if len(comum_) >= 4:
            concorrentes[a.get("pagina") or outro] = max(concorrentes.get(a.get("pagina") or outro, 0), len(comum_))

    notas = {
        "dias_rodando": nota(dias_max, 3, cfg["min_dias_lucrativo"] * 2),
        "anuncios_ativos": nota(math.log1p(ativos), math.log1p(1), math.log1p(cfg["min_ativos_escala"] * 6)),
        "criativos_e_variacoes": nota(variacoes + len(ads), 1, 15),
        "preco_low_ticket": 10.0 if low else (5.0 if not todos_precos else 2.0),
        # pouca concorrência é melhor, mas zero pode ser nicho sem demanda: o ideal fica em 1 a 3
        "concorrencia": 6.0 if not concorrentes else (10.0 if len(concorrentes) <= 3 else nota(-len(concorrentes), -15, -4)),
    }
    if cfg.get("_modo") == "nutra":
        notas.pop("preco_low_ticket")
    pesos = {"dias_rodando": 3, "anuncios_ativos": 3, "criativos_e_variacoes": 2, "preco_low_ticket": 1, "concorrencia": 1}
    total = round(sum(notas[k] * pesos[k] for k in notas) / sum(pesos[k] for k in notas), 1)
    veredito = "MODELAR" if total >= 7 else ("OBSERVAR" if total >= 4.5 else "DESCARTAR")
    top = sorted(ads, key=lambda a: (int(a.get("duplicados") or 1), a.get("inicio_ts") and -a["inicio_ts"]), reverse=True)
    return {
        "pagina": ads[0].get("pagina"),
        "page_id": pid,
        "link_biblioteca": linha.get("link_biblioteca", ""),
        "metricas": {
            "dias_rodando_max": dias_max,
            "anuncios_ativos": ativos,
            "anuncios_nesta_mineracao": len(ads),
            "criativos_em_video": len(videos),
            "variacoes_de_video": variacoes,
            "duplicados_total": duplicados,
            "precos_na_copy": [fmt_preco(p, cfg.get("pais", "BR")) for p in todos_precos],
            "plataforma": ", ".join(plats),
            "concorrentes_parecidos": len(concorrentes),
            "nomes_concorrentes": sorted(concorrentes, key=concorrentes.get, reverse=True)[:5],
            "landing": (top[0].get("link") if top else ""),
            "produto": next((a.get("produto") for a in ads if a.get("produto")), ""),
            "tipo_provavel": next((a.get("tipo_landing") for a in ads if a.get("tipo_landing")), ""),
        },
        "notas": notas,
        "nota_final": total,
        "veredito": veredito,
        "copies_top": [{"copy": a.get("texto", "")[:700], "titulo_link": a.get("titulo_link", ""),
                        "duplicados": a.get("duplicados"), "anuncio": f"https://www.facebook.com/ads/library/?id={a.get('ad_id')}"}
                       for a in top[:3]],
        "verificar_manual": ["order bump e upsell no checkout (abrir o anúncio no celular e ir até o checkout, sem comprar)",
                             "o que a página de vendas promete e como entrega o produto"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta")
    ap.add_argument("--ultima", action="store_true")
    ap.add_argument("--pagina", help="nome ou page_id")
    a = ap.parse_args()
    cfg, _ = carregar_config()
    if a.pasta:
        pasta = Path(a.pasta).expanduser()
    else:
        todas = pastas_mineracao(cfg)
        if not todas:
            print("SEM_MINERACAO: nenhuma mineração da Biblioteca encontrada. Rode a opção 2 antes.")
            sys.exit(3)
        pasta = todas[-1]
    anuncios = json.loads((pasta / "anuncios.json").read_text(encoding="utf-8"))
    ranking = []
    if (pasta / "ranking.csv").exists():
        with open(pasta / "ranking.csv", encoding="utf-8") as f:
            ranking = list(csv.DictReader(f))
    cfg["_modo"] = "nutra" if "_nutra_" in pasta.name else "lowticket"
    print(f"MINERACAO: {pasta}")
    if not a.pagina:
        print("PAGINAS:")
        print(json.dumps([{"#": i + 1, "pagina": r.get("pagina"), "page_id": r.get("page_id"), "sinais": r.get("sinais")}
                          for i, r in enumerate(ranking[:15])], ensure_ascii=False, indent=1))
        return
    res = analisar_pagina(anuncios, ranking, a.pagina, cfg)
    if not res:
        print(f"PAGINA_NAO_ENCONTRADA: '{a.pagina}' não está nesta mineração.")
        sys.exit(3)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
