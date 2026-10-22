#!/usr/bin/env python3
"""Minera a Biblioteca de Anúncios da Meta em segundo plano (navegador invisível).

Exemplos:
  python minerar_meta.py --palavra "pack"
  python minerar_meta.py --palavra "9,90" --nicho culinaria
  python minerar_meta.py --diagnostico
"""
import argparse
import csv
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

from comum import (UA, carregar_config, carregar_filtros, classificar_lowticket, classificar_nutra,
                   extrair_anuncios, extrair_total, fmt_preco, nome_produto, parse_html, parse_payload, plataforma,
                   precos, tipo_landing, tipo_oferta, total_do_texto)

BASE = "https://www.facebook.com/ads/library/"


def url_busca(q, pais, exata):
    if exata:
        return (f"{BASE}?active_status=active&ad_type=all&country={pais}"
                f"&q={quote(chr(34) + q + chr(34))}&search_type=keyword_exact_phrase&media_type=all")
    return (f"{BASE}?active_status=active&ad_type=all&country={pais}"
            f"&q={quote(q)}&search_type=keyword_unordered&media_type=all")


def url_pagina(page_id, pais):
    return f"{BASE}?active_status=active&ad_type=all&country={pais}&view_all_page_id={page_id}"


def url_anuncio(ad_id):
    return f"{BASE}?id={ad_id}"


class Biblioteca:
    def __init__(self, visivel=False, pausa=2.5, log=print):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.launch(headless=not visivel)
        self.ctx = self.browser.new_context(locale="pt-BR", user_agent=UA,
                                           viewport={"width": 1366, "height": 900})
        self.pausa = pausa
        self.log = log

    def fechar(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()

    def _fechar_cookies(self, page):
        for txt in ["Recusar cookies opcionais", "Decline optional cookies",
                    "Permitir apenas cookies essenciais", "Only allow essential cookies"]:
            try:
                btn = page.get_by_role("button", name=txt)
                if btn.count():
                    btn.first.click(timeout=2000)
                    page.wait_for_timeout(800)
                    return
            except Exception:
                pass

    def abrir(self, url, max_anuncios=0):
        """Abre a URL, rola até max_anuncios e devolve (anuncios, total, texto_da_pagina, bloqueado)."""
        page = self.ctx.new_page()
        respostas = []
        page.on("response", lambda r: respostas.append(r) if "/api/graphql" in r.url else None)
        anuncios = {}
        total = None

        def absorver(objs):
            nonlocal total
            for ad in extrair_anuncios(objs):
                anuncios.setdefault(ad["ad_id"], ad)
            t = extrair_total(objs)
            if t is not None:
                total = t

        def processar_respostas():
            while respostas:
                r = respostas.pop(0)
                try:
                    absorver(parse_payload(r.text()))
                except Exception:
                    pass

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
            self._fechar_cookies(page)
            absorver(parse_html(page.content()))
            processar_respostas()

            parado = 0
            while max_anuncios and len(anuncios) < max_anuncios and parado < 4:
                antes = len(anuncios)
                page.mouse.wheel(0, 5000)
                page.wait_for_timeout(int(self.pausa * 1000))
                processar_respostas()
                parado = parado + 1 if len(anuncios) == antes else 0

            texto = page.inner_text("body")[:20000]
        finally:
            page.close()

        baixo = texto.lower()
        bloqueado = (not anuncios) and any(s in baixo for s in [
            "tente novamente mais tarde", "try again later", "você está temporariamente bloqueado",
            "you're temporarily blocked", "faça login para continuar", "log in to continue"])
        if total is None:
            total = total_do_texto(texto)
        return list(anuncios.values()), total, texto, bloqueado


def filtrar_lowticket(anuncios, filtros, cfg, modo="lowticket"):
    """Mantém só páginas com cara de low ticket (ou de nutra). Devolve (mantidos, descartadas{pagina: motivo})."""
    classificar = classificar_nutra if modo == "nutra" else classificar_lowticket
    minimo = cfg["min_score_nutra"] if modo == "nutra" else cfg["min_score_lowticket"]
    rotulo = "oferta de nutra" if modo == "nutra" else "infoproduto"
    por_pagina = defaultdict(list)
    for ad in anuncios:
        pts, motivo, sinais = classificar(ad, filtros, cfg)
        ad["lt_pontos"], ad["lt_motivo"], ad["lt_sinais"] = pts, motivo, sinais
        ad["tipo_landing"] = tipo_landing(ad, filtros)
        ad["produto"] = nome_produto(ad)
        por_pagina[ad["page_id"] or ad["pagina"]].append(ad)
    mantidos, descartadas = [], {}
    for pid, ads in por_pagina.items():
        nome = ads[0]["pagina"] or pid
        bloqueio = next((a["lt_motivo"] for a in ads if a["lt_motivo"]), "")
        if bloqueio:
            descartadas[nome] = bloqueio
            continue
        melhor = max(a["lt_pontos"] for a in ads)
        if melhor < minimo:
            descartadas[nome] = f"não parece {rotulo} (pontos {melhor})"
            continue
        mantidos.extend(ads)
    return mantidos, descartadas


def montar_buscas(palavra, nicho, nichos_cfg, modo="lowticket", pais="BR"):
    if modo == "nutra":
        return [(palavra, True)]          # mecanismo já vem traduzido: frase exata
    # fora do Brasil, os termos de nicho do arquivo (PT) não valem: a palavra já vem
    # traduzida pelo Claude, então usamos a estratégia genérica (palavra + pdf/digital).
    nicho_obj = None if pais != "BR" else next((n for n in nichos_cfg["nichos"] if n["id"] == nicho), None)
    if not nicho_obj or not nicho_obj["termos"]:
        return [(palavra, True), (f"{palavra} pdf", False), (f"{palavra} digital", False)]
    return [(f"{palavra} {t}", False) for t in nicho_obj["termos"][:3]]


_FILTROS_CACHE = None


def filtros_cache():
    global _FILTROS_CACHE
    if _FILTROS_CACHE is None:
        _FILTROS_CACHE = carregar_filtros()
    return _FILTROS_CACHE


def analisar(anuncios, cfg, contagens, modo="lowticket"):
    agora = time.time()
    paginas = defaultdict(list)
    for ad in anuncios:
        ad["dias"] = int((agora - ad["inicio_ts"]) / 86400) if ad["inicio_ts"] else 0
        paginas[ad["page_id"] or ad["pagina"]].append(ad)

    linhas = []
    for pid, ads in paginas.items():
        ativos = contagens.get(pid)
        dias_max = max(a["dias"] for a in ads)
        com_video = [a for a in ads if a["videos"] or a["formato"] == "VIDEO"]
        variacoes_video = len(com_video) + sum(max(0, a["duplicados"] - 1) for a in com_video)
        todos_precos = [p for a in ads for p in precos(a["texto"])]
        low = sorted({p for p in todos_precos if cfg["preco_min"] <= p <= cfg["preco_max"]})
        dominios = sorted({urlparse(a["link"]).netloc.replace("www.", "") for a in ads if a["link"]})
        top = max(ads, key=lambda a: (a["duplicados"], a["dias"]))
        melhor_lt = max(ads, key=lambda a: a.get("lt_pontos", 0))

        sinais = []
        if (ativos or len(ads)) >= cfg["min_ativos_escala"]:
            sinais.append("ESCALA")
        if dias_max >= cfg["min_dias_lucrativo"]:
            sinais.append("LUCRATIVO")
        if variacoes_video >= 2:
            sinais.append("TESTANDO VÍDEOS")
        plats = sorted({plataforma(a["link"]) for a in ads} - {""})
        if modo == "nutra":
            if plats or any("landing de VSL" in s for a in ads for s in a.get("lt_sinais", [])):
                sinais.append("VSL")
        elif low:
            sinais.append("LOW TICKET")

        score = (10 * len(sinais) + 3 * math.log1p(ativos or len(ads)) + 2 * math.log1p(dias_max)
                 + 2 * math.log1p(sum(a["duplicados"] for a in ads)))
        linhas.append({
            "pagina": top["pagina"],
            "page_id": pid,
            "ativos_pagina": ativos if ativos is not None else "",
            "anuncios_na_busca": len(ads),
            "dias_max": dias_max,
            "variacoes_video": variacoes_video,
            "precos": " / ".join(fmt_preco(p, cfg.get("pais", "BR")) for p in low) or (
                " / ".join(fmt_preco(p, cfg.get("pais", "BR")) for p in sorted(set(todos_precos))[:3])),
            "sinais": ", ".join(sinais),
            "plataforma": ", ".join(plats),
            "tipo_provavel": max(([a.get("tipo_landing") for a in ads if a.get("tipo_landing")] or [""]),
                                 key=lambda t: sum(1 for a in ads if a.get("tipo_landing") == t)),
            "produto": next((a["produto"] for a in ads if a.get("produto")), ""),
            "score": round(score, 1),
            "link_biblioteca": url_pagina(pid, cfg["pais"]) if pid.isdigit() else "",
            "anuncio_top": url_anuncio(top["ad_id"]),
            "thumb": top.get("thumb", ""),
            "thumb_local": "",
            "tipo_oferta": tipo_oferta(top, filtros_cache()),
            "tem_legenda": bool(top.get("tem_legenda")),
            "legenda": (top.get("legenda") or "")[:200].replace("\n", " "),
            "landing": top["link"],
            "dominios": ", ".join(dominios[:3]),
            "copy_top": top["texto"][:160].replace("\n", " "),
            "por_que_lowticket": "; ".join(melhor_lt.get("lt_sinais") or []),
        })
    linhas.sort(key=lambda r: r["score"], reverse=True)
    return linhas


def baixar_thumbs(linhas, pasta, quantos, log):
    """Baixa a miniatura do criativo das top N páginas para {pasta}/criativos/."""
    if quantos <= 0:
        return
    import urllib.request
    destino = pasta / "criativos"
    destino.mkdir(parents=True, exist_ok=True)
    baixadas = 0
    for r in linhas[:quantos]:
        url = r.get("thumb")
        if not url:
            continue
        nome = "".join(c if c.isalnum() else "-" for c in (r.get("pagina") or "x"))[:30] + "_" + str(r.get("page_id"))[:10] + ".jpg"
        arq = destino / nome
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                arq.write_bytes(resp.read())
            r["thumb_local"] = str(arq)
            baixadas += 1
        except Exception as e:
            log(f"  miniatura de {r.get('pagina')} indisponível ({e})")
        time.sleep(0.3)
    log(f"miniaturas baixadas: {baixadas}")


def salvar(linhas, anuncios, pasta, cabecalho, meta=None):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "anuncios.json").write_text(json.dumps(anuncios, ensure_ascii=False, indent=1), encoding="utf-8")
    if linhas:
        with open(pasta / "ranking.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
            w.writeheader()
            w.writerows(linhas)
    cols = ["#", "pagina", "ativos_pagina", "dias_max", "variacoes_video", "precos", "plataforma", "sinais",
            "link_biblioteca"]
    md = [f"# {cabecalho}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for i, r in enumerate(linhas, 1):
        md.append("| " + " | ".join([str(i)] + [str(r[c]).replace("|", "/") for c in cols[1:]]) + " |")
    (pasta / "ranking.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    try:
        import relatorio
        relatorio.gerar(linhas, pasta, meta or {"titulo": cabecalho})
    except Exception as e:
        print(f"(relatório visual não gerado: {e})", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--palavra", action="append", help="pode repetir (variações da mesma busca)")
    ap.add_argument("--modo", choices=["lowticket", "nutra"], default="lowticket")
    ap.add_argument("--pais", help="código do país (US, DE, FR…); padrão: config")
    ap.add_argument("--rotulo", default="", help="nome da busca para a pasta/relatório (ex.: mecanismo em PT)")
    ap.add_argument("--nicho", default="geral")
    ap.add_argument("--max", type=int)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--visivel", action="store_true", help="mostra o navegador (só para depurar)")
    ap.add_argument("--diagnostico", action="store_true")
    ap.add_argument("--sem-filtro", action="store_true", help="não aplica o filtro de low ticket")
    ap.add_argument("--thumbs", type=int, default=15, help="baixa a miniatura dos N primeiros criativos (0 = nenhum)")
    a = ap.parse_args()
    cfg, nichos = carregar_config()
    if a.pais:
        cfg["pais"] = a.pais.upper()
    log = lambda *x: print(*x, file=sys.stderr, flush=True)

    try:
        bib = Biblioteca(visivel=a.visivel, pausa=cfg["pausa_rolagem_seg"], log=log)
    except Exception as e:
        print(f"ERRO_NAVEGADOR: {e}\nRode a opção 1 (setup e diagnóstico).")
        sys.exit(2)

    try:
        if a.diagnostico:
            ads, total, texto, bloq = bib.abrir(url_busca("pack", cfg["pais"], True), max_anuncios=10)
            print(f"META_OK anuncios_lidos={len(ads)} total={total} bloqueado={bloq}")
            if ads:
                ex = ads[0]
                print(f"exemplo: {ex['pagina']} | {url_anuncio(ex['ad_id'])} | link={ex['link'][:80]}")
            elif not bloq:
                print("AVISO: a página abriu mas nenhum anúncio foi lido. Trecho da página:\n" + texto[:500])
            return

        if not a.palavra:
            sys.exit("Informe --palavra")
        max_ads = a.max or cfg["max_anuncios"]
        buscas = [b for p in a.palavra for b in montar_buscas(p, a.nicho, nichos, a.modo, cfg["pais"])]
        por_busca = max(30, max_ads // len(buscas))
        todos = {}
        for q, exata in buscas:
            log(f"buscando: {q!r} ({'frase exata' if exata else 'todas as palavras'})")
            ads, total, _, bloq = bib.abrir(url_busca(q, cfg["pais"], exata), max_anuncios=por_busca)
            log(f"  {len(ads)} anúncios lidos (total na busca: {total})")
            if bloq:
                log("  BLOQUEIO da Meta detectado — parando e salvando o que já foi coletado.")
                break
            if a.modo == "nutra" and exata and len(ads) < 10 and not bloq:
                log(f"  poucos resultados na frase exata — buscando {q!r} com todas as palavras")
                extra, _, _, bloq = bib.abrir(url_busca(q, cfg["pais"], False), max_anuncios=por_busca)
                log(f"  +{len(extra)} anúncios")
                ads += extra
            for ad in ads:
                ad["busca"] = q
                todos.setdefault(ad["ad_id"], ad)

        anuncios = list(todos.values())
        if not anuncios:
            print("NENHUM_ANUNCIO: a busca não retornou anúncios (ou a Meta bloqueou). "
                  "Tente outra palavra ou rode a opção 1 para diagnosticar.")
            sys.exit(3)

        lidos = len(anuncios)
        descartadas = {}
        if cfg.get("filtro_lowticket", True) and not a.sem_filtro:
            anuncios, descartadas = filtrar_lowticket(anuncios, carregar_filtros(), cfg, a.modo)
            log(f"filtro {a.modo}: {len(anuncios)} de {lidos} anúncios mantidos, {len(descartadas)} páginas descartadas")
            if not anuncios:
                if a.modo == "nutra":
                    print(f"NENHUM_NUTRA: {lidos} anúncios lidos, mas nenhum com cara de oferta de nutra (VSL/advertorial). "
                          "Tente outra variação do mecanismo ou outro país.")
                else:
                    print(f"NENHUM_LOWTICKET: {lidos} anúncios lidos, mas nenhum com cara de infoproduto low ticket. "
                          "Tente uma palavra mais específica (ex.: 'pack pdf', 'mapas mentais', 'apostila') ou outro nicho.")
                print("DESCARTADAS: " + json.dumps(dict(list(descartadas.items())[:15]), ensure_ascii=False))
                sys.exit(4)

        # conta os ativos das páginas mais promissoras
        pre = analisar(anuncios, cfg, {}, a.modo)
        contagens = {}
        for r in pre[: cfg["paginas_para_contar"]]:
            if not r["page_id"].isdigit():
                continue
            log(f"contando anúncios ativos: {r['pagina']}")
            _, total, _, bloq = bib.abrir(url_pagina(r["page_id"], cfg["pais"]), max_anuncios=0)
            if bloq:
                log("  bloqueio — parei a contagem.")
                break
            if total is not None:
                contagens[r["page_id"]] = total

        grandes = {pid for pid, n in contagens.items() if n > cfg.get("max_ativos_pagina", 800)}
        if grandes and not a.sem_filtro:
            for ad in anuncios:
                if ad["page_id"] in grandes:
                    descartadas[ad["pagina"]] = f"{contagens[ad['page_id']]} anúncios ativos (provável empresa grande)"
            anuncios = [ad for ad in anuncios if ad["page_id"] not in grandes]

        linhas = analisar(anuncios, cfg, contagens, a.modo)
        try:
            import historico
            linhas = historico.registrar(linhas, cfg["pais"])
        except Exception as e:
            log(f"(radar não atualizado: {e})")
        data = datetime.now().strftime("%Y-%m-%d_%Hh%M")
        nome_busca = a.rotulo or a.palavra[0]
        slug = "".join(c if c.isalnum() else "-" for c in nome_busca).strip("-")[:40] or "busca"
        pasta = Path(cfg["pasta_saida"]) / f"{data}_{a.modo}_{cfg['pais']}_{a.nicho}_{slug}"
        baixar_thumbs(linhas, pasta, a.thumbs, log)
        meta = {"modo": a.modo, "titulo": nome_busca, "pais": cfg["pais"], "nicho": a.nicho,
                "subtitulo": f"{a.modo} · {a.nicho} · {cfg['pais']} · " + " / ".join(a.palavra)}
        salvar(linhas, anuncios, pasta, f"Mineração {a.modo}: '{nome_busca}' ({' / '.join(a.palavra)}) · "
                                        f"{a.nicho} · {cfg['pais']}", meta)
        if descartadas:
            (pasta / "descartadas.md").write_text("# Páginas descartadas pelo filtro low ticket\n\n" + "\n".join(
                f"- {p}: {m}" for p, m in descartadas.items()) + "\n", encoding="utf-8")

        print(f"PASTA: {pasta}")
        print(f"RELATORIO: {pasta / 'relatorio.html'}")
        print(f"ANUNCIOS_LIDOS: {lidos} · {a.modo.upper()}: {len(anuncios)} · PAGINAS: {len(linhas)} · DESCARTADAS: {len(descartadas)}")
        if descartadas:
            print("EXEMPLOS_DESCARTADOS: " + json.dumps(dict(list(descartadas.items())[:8]), ensure_ascii=False))
        print(json.dumps(linhas[: a.top], ensure_ascii=False, indent=1))
    finally:
        bib.fechar()


if __name__ == "__main__":
    main()
