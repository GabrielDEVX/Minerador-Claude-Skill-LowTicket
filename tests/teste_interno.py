#!/usr/bin/env python3
"""Teste interno de ponta a ponta, sem acessar a Meta.

Simula a Biblioteca de Anúncios devolvendo respostas no formato do /api/graphql
e roda a mineração completa nos modos low ticket e nutra.

  HOME=/tmp/teste python3 tests/teste_interno.py
"""
import io
import json
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins/lowticket/skills/lowticket/scripts"
sys.path.insert(0, str(SCRIPTS))

import comum  # noqa: E402
import minerar_meta  # noqa: E402

AGORA = int(time.time())
FALHAS = []


def checar(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    if not cond:
        FALHAS.append(msg)


def anuncio(i, page_id, pagina, texto, link, dias=40, dup=1, video=False, titulo="", cta="Saiba mais"):
    return {
        "ad_archive_id": str(i), "page_id": str(page_id), "page_name": pagina,
        "start_date": AGORA - dias * 86400, "collation_count": dup, "is_active": True,
        "snapshot": {"body": {"text": texto}, "link_url": link, "title": titulo, "cta_text": cta,
                     "display_format": "VIDEO" if video else "IMAGE", "videos": [{}] if video else [],
                     "cards": [], "page_like_count": 1200},
    }


def payload(ads, total):
    """Resposta no formato da Meta (prefixo for(;;); + search_results_connection)."""
    corpo = {"data": {"ad_library_main": {"search_results_connection": {
        "count": total, "edges": [{"node": {"collated_results": ads}}]}}}}
    return "for (;;);" + json.dumps(corpo)


MARIANA = ("📚 Cansado de perder tempo procurando o que realmente importa em apostilas, PDFs e materiais enormes?\n\n"
           "Com +100 mapas mentais de Nutrição, você pode revisar os principais conteúdos de forma muito mais visual, "
           "prática e organizada. 🧠✨\n\nIdeal para:\n📌 Faculdade\n📌 Revisões rápidas\n📌 Provas e avaliações\n\n"
           "Tudo organizado para você encontrar a informação com muito mais facilidade.\n\n"
           "👇 Quer conhecer o material por dentro? Clique no link e saiba mais.")

BUSCAS = {
    "lowticket": [
        anuncio(1, 501, "Mariana Oliveira", MARIANA, "https://nutricao.guiapractico.com/", dias=45, dup=6,
                titulo="+100 Mapas Mentais de Nutrição"),
        anuncio(2, 501, "Mariana Oliveira", MARIANA.replace("Nutrição", "Anatomia"), "https://nutricao.guiapractico.com/b",
                dias=20, dup=3, video=True),
        anuncio(3, 501, "Mariana Oliveira", MARIANA, "https://nutricao.guiapractico.com/c", dias=12, dup=2, video=True),
        anuncio(4, 502, "Ateliê da Ju", "Pack com +500 moldes de amigurumi em PDF. Acesso imediato por apenas 19,90 ✅",
                "https://pay.kiwify.com.br/abc", dias=8),
        anuncio(5, 503, "Alibaba.com", "Mega pack de produtos para sua loja. Fornecedor direto da fábrica",
                "https://www.alibaba.com/product/1"),
        anuncio(6, 504, "Shopee Brasil", "Kit completo com cupom de frete grátis", "https://shopee.com.br/x"),
        anuncio(7, 505, "Bella Moda", "Kit 3 vestidos por R$ 39,90, entrega em todo Brasil, tamanhos P ao GG",
                "https://bellamoda.com.br/kit"),
    ],
    "nutra": [
        anuncio(11, 601, "Gesundheit Heute", "Dieser einfache Pferdetrick vor dem Schlafen... Sehen Sie sich das Video an, "
                "bevor es gelöscht wird!", "https://gesund-news.de/vsl/pferd", dias=60, dup=9, video=True),
        anuncio(12, 601, "Gesundheit Heute", "Ärzte sind sprachlos: der Pferde-Trick. Video ansehen",
                "https://www.digistore24.com/redir/123/aff", dias=35, dup=4, video=True),
        anuncio(13, 602, "Amazon.de", "Pferdesalbe 500ml – kostenloser Versand", "https://www.amazon.de/x"),
        anuncio(14, 603, "Reiterhof Müller", "Reitstunden für Kinder, jetzt buchen", "https://reiterhof-mueller.de",
                cta="Jetzt buchen"),
    ],
}
TOTAIS_PAGINA = {"501": 14, "502": 3, "601": 27}


class BibliotecaFalsa:
    def __init__(self, *a, **k):
        self.urls = []

    def abrir(self, url, max_anuncios=0):
        self.urls.append(url)
        if "view_all_page_id=" in url:
            pid = url.split("view_all_page_id=")[1].split("&")[0]
            return [], TOTAIS_PAGINA.get(pid), "", False
        modo = "nutra" if "country=DE" in url else "lowticket"
        objs = comum.parse_payload(payload(BUSCAS[modo], len(BUSCAS[modo])))
        return list(comum.extrair_anuncios(objs)), comum.extrair_total(objs), "", False

    def fechar(self):
        pass


def rodar(args):
    bib = BibliotecaFalsa()
    minerar_meta.Biblioteca = lambda *a, **k: bib
    sys.argv = ["minerar_meta.py"] + args
    saida = io.StringIO()
    with redirect_stdout(saida):
        try:
            minerar_meta.main()
        except SystemExit as e:
            if e.code not in (None, 0):
                print(f"SAIU_COM {e.code}")
    texto = saida.getvalue()
    pasta = next((l.split("PASTA: ")[1].strip() for l in texto.splitlines() if l.startswith("PASTA: ")), "")
    corpo = texto[texto.index("["):] if "[" in texto else "[]"
    try:
        linhas = json.loads(corpo)
    except Exception:
        linhas = []
    return texto, Path(pasta) if pasta else None, linhas, bib


def main():
    print("\n1) Leitura do formato da Meta")
    objs = comum.parse_payload(payload(BUSCAS["lowticket"], 812))
    ads = list(comum.extrair_anuncios(objs))
    checar(len(ads) == 7, f"lê os 7 anúncios do JSON da Meta (leu {len(ads)})")
    checar(comum.extrair_total(objs) == 812, "lê o total de resultados")
    a1 = next(a for a in ads if a["ad_id"] == "1")
    checar(a1["cta"] == "Saiba mais" and "+100 Mapas" in a1["titulo_link"], "lê botão e título do link")
    html = '<script type="application/json">' + payload(BUSCAS["nutra"], 4)[9:] + "</script>"
    checar(len(list(comum.extrair_anuncios(comum.parse_html(html)))) == 4, "lê anúncios embutidos no HTML")
    checar(comum.total_do_texto("~1,2 mil resultados") == 1200, "entende '~1,2 mil resultados'")

    print("\n2) Mineração LOW TICKET de ponta a ponta (palavra 'pack', nicho geral)")
    texto, pasta, linhas, bib = rodar(["--palavra", "pack", "--nicho", "geral"])
    nomes = [l["pagina"] for l in linhas]
    checar(pasta is not None and pasta.exists(), "cria a pasta do resultado")
    checar("Mariana Oliveira" in nomes and "Ateliê da Ju" in nomes, f"mantém as páginas de low ticket ({nomes})")
    checar(not {"Alibaba.com", "Shopee Brasil", "Bella Moda"} & set(nomes), "descarta Alibaba, Shopee e loja de roupa")
    m = next((l for l in linhas if l["pagina"] == "Mariana Oliveira"), {})
    checar(m.get("ativos_pagina") == 14, f"conta ativos da página (14 → {m.get('ativos_pagina')})")
    checar(all(s in m.get("sinais", "") for s in ("ESCALA", "LUCRATIVO", "TESTANDO")),
           f"sinais da Mariana: {m.get('sinais')}")
    checar(linhas and linhas[0]["pagina"] == "Mariana Oliveira", "Mariana fica em 1º no ranking")
    a = next((l for l in linhas if l["pagina"] == "Ateliê da Ju"), {})
    checar("LOW TICKET" in a.get("sinais", "") and "19,90" in a.get("precos", ""), f"preço e sinal do Ateliê: {a.get('precos')}")
    checar(a.get("plataforma") == "Kiwify", "detecta Kiwify")
    checar("view_all_page_id=501" in (m.get("link_biblioteca") or ""), "gera link da biblioteca da página")
    buscas = [u for u in bib.urls if "q=" in u]
    checar(len(buscas) == 3 and "keyword_exact_phrase" in buscas[0], "geral busca 'pack' (exata) + 'pack pdf' + 'pack digital'")
    if pasta:
        for arq in ("ranking.md", "ranking.csv", "anuncios.json", "descartadas.md"):
            checar((pasta / arq).exists(), f"gera {arq}")
        desc = (pasta / "descartadas.md").read_text(encoding="utf-8") if (pasta / "descartadas.md").exists() else ""
        checar("Alibaba" in desc and "grande empresa" in desc, "descartadas.md explica o motivo")
    checar("DESCARTADAS: 3" in texto, "resumo mostra 3 descartadas")

    print("\n3) Mineração NUTRA de ponta a ponta (Alemanha, truque do cavalo em alemão)")
    texto, pasta, linhas, bib = rodar(["--modo", "nutra", "--pais", "DE", "--nicho", "ed", "--rotulo", "Truque do cavalo",
                                        "--palavra", "Pferdetrick", "--palavra", "Pferde-Trick"])
    nomes = [l["pagina"] for l in linhas]
    buscas = [u for u in bib.urls if "q=" in u]
    checar(all("country=DE" in u for u in bib.urls), "todas as buscas no país DE")
    checar(any("Pferdetrick" in u for u in buscas) and any("Pferde-Trick" in u for u in buscas), "busca as 2 variações em alemão")
    checar(nomes == ["Gesundheit Heute"], f"mantém só a oferta de nutra ({nomes})")
    g = linhas[0] if linhas else {}
    checar(g.get("ativos_pagina") == 27, "conta 27 ativos da página")
    checar("VSL" in g.get("sinais", "") and "Digistore24" in g.get("plataforma", ""), f"sinais {g.get('sinais')} · {g.get('plataforma')}")
    checar("LOW TICKET" not in g.get("sinais", ""), "não marca LOW TICKET no modo nutra")
    checar(pasta is not None and "_nutra_DE_ed_Truque-do-cavalo" in str(pasta), f"pasta nomeada: {pasta.name if pasta else ''}")
    if pasta:
        desc = (pasta / "descartadas.md").read_text(encoding="utf-8")
        checar("Amazon" in desc and "Reiterhof" in desc, "descarta Amazon.de e o haras")

    print("\n4) Sem filtro")
    texto, pasta, linhas, _ = rodar(["--palavra", "pack", "--sem-filtro"])
    checar(len(linhas) == 5, f"--sem-filtro mantém todas as 5 páginas ({len(linhas)})")

    print("\n5) Configurações e dados do nutra")
    cfg, _ = comum.carregar_config()
    nu = comum.carregar_nutra()
    checar(cfg["min_score_nutra"] == 3 and cfg["min_score_lowticket"] == 5, "config tem os mínimos novos")
    checar(len(nu["paises"]) == 8 and len(nu["categorias"]) == 7, "8 países e 7 categorias de nutra")
    total = sum(len(c["principais"]) + len(c["outras"]) for c in nu["categorias"])
    checar(total >= 100, f"{total} mecanismos de nutra")
    checar(all(len(c["principais"]) <= 8 for c in nu["categorias"]), "no máximo 8 principais por categoria no menu")
    ed = next(c for c in nu["categorias"] if c["id"] == "ed")
    checar("Truque do cavalo" in ed["principais"] and "Truque do bicarbonato" in ed["principais"], "cavalo e bicarbonato em destaque no ED")

    print(f"\n{'TUDO OK' if not FALHAS else f'{len(FALHAS)} FALHA(S)'}")
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
