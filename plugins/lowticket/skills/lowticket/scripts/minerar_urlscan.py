#!/usr/bin/env python3
"""Encontra ofertas pelo urlscan.io: páginas que carregam um rastreador (padrão: UTMify).

Usa a busca pública do urlscan.io (uma consulta por vez, respeitando o limite de uso).
Não abre as páginas: só lê o que o urlscan.io já registrou (URL, título, data e print).

  python3 minerar_urlscan.py --dias 30
  python3 minerar_urlscan.py --dias 7 --nicho culinaria
  python3 minerar_urlscan.py --rastreador utmify.com.br --rastreador outro.com
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

from comum import (_sem_acento, carregar_config, carregar_filtros, classificar_lowticket, plataforma, precos,
                   fmt_preco)

API = "https://urlscan.io/api/v1/search/"
UA = "CentralLowTicket/1.3 (+https://github.com/GabrielDEVX/Minerador-Claude-Skill-LowTicket)"
IGNORAR = {"utmify.com.br", "utmify.com", "google.com", "facebook.com", "instagram.com", "wa.me", "whatsapp.com",
           "linktr.ee", "youtube.com", "tiktok.com", "urlscan.io", "localhost"}


def montar_query(rastreadores, dias):
    alvo = " OR ".join(f"domain:{r}" for r in rastreadores)
    fora = " AND ".join(f"NOT page.domain:{r}" for r in rastreadores)
    return f"({alvo}) AND {fora} AND date:>now-{int(dias)}d"


def buscar(query, tamanho, chave="", paginas=1, log=print):
    """Chama a busca do urlscan.io. Devolve (resultados, aviso)."""
    resultados, depois = [], None
    for n in range(paginas):
        url = f"{API}?q={quote(query)}&size={int(tamanho)}"
        if depois:
            url += "&search_after=" + quote(",".join(str(x) for x in depois))
        req = urllib.request.Request(url, headers={"User-Agent": UA, **({"API-Key": chave} if chave else {})})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                dados = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return resultados, "LIMITE: o urlscan.io limitou as buscas por agora (HTTP 429). Espere alguns minutos " \
                                   "ou configure uma chave grátis do urlscan.io nas configurações."
            if e.code in (401, 403):
                return resultados, f"ACESSO_NEGADO: o urlscan.io recusou a busca (HTTP {e.code}). Confira a chave da API."
            return resultados, f"ERRO_URLSCAN: HTTP {e.code}"
        except Exception as e:
            return resultados, f"SEM_CONEXAO: não consegui falar com o urlscan.io ({e})."
        lote = dados.get("results") or []
        resultados += lote
        log(f"  página {n + 1}: {len(lote)} scans")
        if not dados.get("has_more") or not lote:
            break
        depois = lote[-1].get("sort")
        time.sleep(2)
    return resultados, ""


def agrupar(resultados, cfg, filtros, termos_nicho, palavra):
    por_dominio = defaultdict(list)
    for r in resultados:
        page, task = r.get("page") or {}, r.get("task") or {}
        dom = (page.get("domain") or urlparse(page.get("url") or task.get("url") or "").netloc or "").lower()
        dom = dom[4:] if dom.startswith("www.") else dom
        if not dom or any(dom == i or dom.endswith("." + i) for i in IGNORAR):
            continue
        por_dominio[dom].append(r)

    linhas, descartados = [], {}
    for dom, scans in por_dominio.items():
        scans.sort(key=lambda r: (r.get("task") or {}).get("time") or "", reverse=True)
        ult = scans[0]
        page, task = ult.get("page") or {}, ult.get("task") or {}
        titulos = [t for t in dict.fromkeys((s.get("page") or {}).get("title") or "" for s in scans) if t]
        urls = list(dict.fromkeys((s.get("page") or {}).get("url") or (s.get("task") or {}).get("url") or "" for s in scans))
        texto = " · ".join(titulos[:3]) + " " + " ".join(urls[:5])
        busca = _sem_acento(texto)
        if termos_nicho and not any(_sem_acento(t) in busca for t in termos_nicho):
            continue
        if palavra and _sem_acento(palavra) not in busca:
            continue
        ad = {"pagina": "", "link": urls[0] if urls else f"https://{dom}/", "texto": " · ".join(titulos[:3]),
              "titulo_link": "", "curtidas": 0, "cta": ""}
        pts, motivo, sinais = classificar_lowticket(ad, filtros, cfg)
        if motivo:
            descartados[dom] = motivo
            continue
        plats = sorted({plataforma(u) for u in urls} - {""})
        ps = sorted({p for t in titulos for p in precos(t)})
        uuid = ult.get("_id") or task.get("uuid") or ""
        linhas.append({
            "dominio": dom,
            "titulo": (titulos[0] if titulos else "")[:90],
            "ultimo_scan": (task.get("time") or "")[:10],
            "scans": len(scans),
            "urls": urls[:5],
            "plataforma": ", ".join(plats),
            "precos": " / ".join(fmt_preco(p) for p in ps[:3]),
            "pontos_lowticket": pts,
            "sinais": "; ".join(sinais),
            "urlscan": f"https://urlscan.io/result/{uuid}/" if uuid else "",
            "print": f"https://urlscan.io/screenshots/{uuid}.png" if uuid else "",
            "buscar_na_biblioteca": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                                    f"&country={cfg['pais']}&q={quote(dom)}&search_type=keyword_unordered&media_type=all",
        })
    linhas.sort(key=lambda l: (l["scans"], l["pontos_lowticket"], l["ultimo_scan"]), reverse=True)
    return linhas, descartados


def baixar_prints(linhas, pasta, quantos, log):
    if quantos <= 0:
        return
    destino = pasta / "prints"
    destino.mkdir(parents=True, exist_ok=True)
    for l in linhas[:quantos]:
        if not l["print"]:
            continue
        arq = destino / (l["dominio"].replace(".", "_") + ".png")
        try:
            req = urllib.request.Request(l["print"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                arq.write_bytes(r.read())
            l["print_local"] = str(arq)
        except Exception as e:
            log(f"  print de {l['dominio']} indisponível ({e})")
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=30, help="só scans dos últimos N dias")
    ap.add_argument("--nicho", default="geral")
    ap.add_argument("--palavra", default="", help="filtra domínios cujo título/URL contém a palavra")
    ap.add_argument("--rastreador", action="append", help="domínio do rastreador (padrão: config)")
    ap.add_argument("--tamanho", type=int, default=100)
    ap.add_argument("--paginas", type=int, default=1)
    ap.add_argument("--prints", type=int, default=8, help="baixa o print do urlscan dos N primeiros (0 = nenhum)")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    cfg, nichos = carregar_config()
    log = lambda *x: print(*x, file=sys.stderr, flush=True)

    rastreadores = a.rastreador or cfg.get("rastreadores_urlscan") or ["utmify.com.br"]
    termos = next((n["termos"] for n in nichos["nichos"] if n["id"] == a.nicho), [])
    query = montar_query(rastreadores, a.dias)
    log(f"buscando no urlscan.io: {query}")
    resultados, aviso = buscar(query, a.tamanho, cfg.get("urlscan_api_key", ""), a.paginas, log)
    if aviso and not resultados:
        print(aviso)
        sys.exit(3)
    if not resultados:
        print(f"NENHUM_SCAN: o urlscan.io não tem scans com {', '.join(rastreadores)} nos últimos {a.dias} dias. "
              "Tente um período maior.")
        sys.exit(3)

    linhas, descartados = agrupar(resultados, cfg, carregar_filtros(), termos, a.palavra)
    data = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    pasta = Path(cfg["pasta_saida"]) / f"{data}_urlscan_{a.nicho}_{a.dias}d"
    pasta.mkdir(parents=True, exist_ok=True)
    baixar_prints(linhas, pasta, a.prints, log)
    (pasta / "dominios.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    md = [f"# urlscan.io · páginas com {', '.join(rastreadores)} · últimos {a.dias} dias · nicho {a.nicho}", "",
          "| # | domínio | título | último scan | scans | plataforma | biblioteca | urlscan |", "|---|---|---|---|---|---|---|---|"]
    for i, l in enumerate(linhas, 1):
        md.append(f"| {i} | {l['dominio']} | {l['titulo'].replace('|', '/')} | {l['ultimo_scan']} | {l['scans']} | "
                  f"{l['plataforma']} | {l['buscar_na_biblioteca']} | {l['urlscan']} |")
    (pasta / "ranking.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if descartados:
        (pasta / "descartadas.md").write_text("# Domínios descartados\n\n" + "\n".join(
            f"- {d}: {m}" for d, m in descartados.items()) + "\n", encoding="utf-8")

    print(f"PASTA: {pasta}")
    print(f"SCANS_LIDOS: {len(resultados)} · DOMINIOS: {len(linhas)} · DESCARTADOS: {len(descartados)}")
    if aviso:
        print(aviso)
    print(json.dumps(linhas[: a.top], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
