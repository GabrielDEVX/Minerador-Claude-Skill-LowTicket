#!/usr/bin/env python3
"""Minera produtos low ticket pelas reclamações das plataformas no Reclame Aqui.

Lógica: produto que vende muito gera reclamação. Lemos as reclamações recentes de
Kiwify, Hotmart, Cakto etc., puxamos os nomes de produtos citados e ranqueamos.

  python minerar_reclameaqui.py --nicho culinaria --paginas 3
  python minerar_reclameaqui.py --palavra pack
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from comum import UA, carregar_config, iter_dicts

PRODUTO_RE = re.compile(
    r"\b(?:curso|ebook|e-book|pack|mega pack|kit|combo|mentoria|método|metodo|planilha|apostila|"
    r"desafio|guia|treinamento|protocolo|programa|livro|receitas?)\s+(?:d[oae]s?\s+|de\s+)?"
    r"([A-ZÀ-Ú0-9\"'+][\wÀ-ú0-9+&\-\" ]{2,40})",
    re.I,
)
PARAR = re.compile(r"\s+(?:e\s+n[aã]o|n[aã]o|que|mas|pois|porque|por|para|pelo|pela|comprei|paguei|ap[oó]s|com)\b.*$", re.I)


def nomes_produto(texto):
    out = []
    for m in PRODUTO_RE.finditer(texto or ""):
        nome = PARAR.sub("", m.group(0)).strip(" .,-\"'")
        if 6 <= len(nome) <= 50:
            out.append(nome.lower())
    return out


def coletar(slug, paginas, log):
    from playwright.sync_api import sync_playwright
    itens = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(locale="pt-BR", user_agent=UA)
        page = ctx.new_page()
        respostas = []
        page.on("response", lambda r: respostas.append(r)
                if "reclameaqui" in r.url and "json" in (r.headers.get("content-type") or "") else None)
        for n in range(1, paginas + 1):
            url = f"https://www.reclameaqui.com.br/empresa/{slug}/lista-reclamacoes/" + (f"?pagina={n}" if n > 1 else "")
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3500)
            except Exception as e:
                log(f"  {slug}: erro ao abrir ({e})")
                break
            if resp and resp.status >= 400:
                log(f"  {slug}: HTTP {resp.status} (slug errado ou bloqueio)")
                break
            # 1) JSON da rede
            while respostas:
                r = respostas.pop(0)
                try:
                    data = r.json()
                except Exception:
                    continue
                for d in iter_dicts(data):
                    if isinstance(d.get("title"), str) and ("description" in d or "status" in d):
                        chave = str(d.get("id") or d["title"])
                        itens.setdefault(chave, {
                            "titulo": d["title"],
                            "texto": re.sub(r"<[^>]+>", " ", str(d.get("description") or ""))[:800],
                            "data": str(d.get("created") or d.get("creationDate") or "")[:10],
                            "link": f"https://www.reclameaqui.com.br/{slug}/{d['url']}/" if d.get("url") else "",
                        })
            # 2) fallback pelo HTML
            for a in page.query_selector_all(f'a[href*="/{slug}/"]'):
                try:
                    href = a.get_attribute("href") or ""
                    txt = (a.inner_text() or "").strip()
                except Exception:
                    continue
                if len(txt) < 15 or "lista-reclamacoes" in href or "/empresa/" in href:
                    continue
                link = href if href.startswith("http") else "https://www.reclameaqui.com.br" + href
                itens.setdefault(link, {"titulo": txt.split("\n")[0], "texto": txt, "data": "", "link": link})
        b.close()
    return list(itens.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nicho", default="geral")
    ap.add_argument("--palavra", default="")
    ap.add_argument("--paginas", type=int, default=3, help="páginas de reclamações por plataforma")
    ap.add_argument("--gateways", default="", help="ex: Kiwify,Hotmart (padrão: todas)")
    a = ap.parse_args()
    cfg, nichos = carregar_config()
    log = lambda *x: print(*x, file=sys.stderr, flush=True)

    gws = nichos["gateways_reclameaqui"]
    if a.gateways:
        escolha = {g.strip().lower() for g in a.gateways.split(",")}
        gws = {k: v for k, v in gws.items() if k.lower() in escolha}
    termos = next((n["termos"] for n in nichos["nichos"] if n["id"] == a.nicho), [])
    filtros = [t.lower() for t in termos] + ([a.palavra.lower()] if a.palavra else [])

    produtos = Counter()
    exemplos = defaultdict(list)
    plataformas = defaultdict(set)
    total = 0
    for nome, slug in gws.items():
        log(f"lendo reclamações: {nome}")
        try:
            recl = coletar(slug, a.paginas, log)
        except Exception as e:
            log(f"  falhou: {e}")
            continue
        log(f"  {len(recl)} reclamações")
        total += len(recl)
        for r in recl:
            corpo = f"{r['titulo']} {r['texto']}"
            if filtros and not any(f in corpo.lower() for f in filtros):
                continue
            for prod in set(nomes_produto(corpo)):
                produtos[prod] += 1
                plataformas[prod].add(nome)
                if len(exemplos[prod]) < 2 and r["link"]:
                    exemplos[prod].append(r["link"])

    if not total:
        print("NENHUMA_RECLAMACAO: o Reclame Aqui não respondeu (bloqueio ou slugs errados). "
              "Use o método 2 (biblioteca de anúncios).")
        sys.exit(3)

    linhas = []
    for prod, n in produtos.most_common(40):
        linhas.append({
            "produto": prod,
            "mencoes": n,
            "plataformas": ", ".join(sorted(plataformas[prod])),
            "buscar_na_biblioteca": "https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                                    f"&country={cfg['pais']}&q={quote(prod)}&search_type=keyword_unordered&media_type=all",
            "reclamacoes": " ".join(exemplos[prod]),
        })

    data = datetime.now().strftime("%Y-%m-%d_%Hh%M")
    pasta = Path(cfg["pasta_saida"]) / f"{data}_reclameaqui_{a.nicho}"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "produtos.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# Reclame Aqui · produtos mais citados", "", "| # | produto | menções | plataformas | biblioteca |", "|---|---|---|---|---|"]
    for i, l in enumerate(linhas, 1):
        md.append(f"| {i} | {l['produto']} | {l['mencoes']} | {l['plataformas']} | {l['buscar_na_biblioteca']} |")
    (pasta / "ranking.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"PASTA: {pasta}")
    print(f"RECLAMACOES_LIDAS: {total} · PRODUTOS: {len(linhas)}")
    print(json.dumps(linhas[:20], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
