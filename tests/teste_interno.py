#!/usr/bin/env python3
"""Teste interno de todas as funções, sem acessar a Meta nem o Reclame Aqui.

Simula as respostas dos sites no formato real e roda cada função da ferramenta.

  HOME=/pasta/vazia python3 tests/teste_interno.py
"""
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPTS = RAIZ / "plugins/lowticket/skills/lowticket/scripts"
sys.path.insert(0, str(SCRIPTS))

import comum  # noqa: E402
import minerar_meta  # noqa: E402
import minerar_reclameaqui  # noqa: E402

AGORA = int(time.time())
FALHAS, OK = [], []


def checar(cond, msg):
    print(("  ✅ " if cond else "  ❌ ") + msg)
    (OK if cond else FALHAS).append(msg)


def secao(t):
    print(f"\n{t}")


# ---------------------------------------------------------------- dados simulados
def anuncio(i, page_id, pagina, texto, link, dias=40, dup=1, video=False, titulo="", cta="Saiba mais"):
    return {
        "ad_archive_id": str(i), "page_id": str(page_id), "page_name": pagina,
        "start_date": AGORA - dias * 86400, "collation_count": dup, "is_active": True,
        "snapshot": {"body": {"text": texto}, "link_url": link, "title": titulo, "cta_text": cta,
                     "display_format": "VIDEO" if video else "IMAGE", "videos": [{}] if video else [],
                     "cards": [], "page_like_count": 1200},
    }


def payload(ads, total):
    corpo = {"data": {"ad_library_main": {"search_results_connection": {
        "count": total, "edges": [{"node": {"collated_results": ads}}]}}}}
    return "for (;;);" + json.dumps(corpo)


MARIANA = ("📚 Cansado de perder tempo procurando o que realmente importa em apostilas, PDFs e materiais enormes?\n\n"
           "Com +100 mapas mentais de Nutrição, você pode revisar os principais conteúdos de forma muito mais visual, "
           "prática e organizada. 🧠✨\n\nIdeal para:\n📌 Faculdade\n📌 Revisões rápidas\n📌 Provas e avaliações\n\n"
           "Tudo organizado para você encontrar a informação com muito mais facilidade.\n\n"
           "👇 Quer conhecer o material por dentro? Clique no link e saiba mais.")
SOFIA = ("Müde davon, alles zu versuchen und trotzdem keine sichtbaren Ergebnisse beim Abnehmen zu erzielen?\n\n"
         "Mit Slim Jara gewinnen Sie die Kontrolle zurück:\nReduzieren Sie Ihren Appetit, steigern Sie Ihre Energie im "
         "Alltag und bleiben Sie fokussiert auf Ihre Ziele.\n\n✨ Unterstützt einen aktiven Stoffwechsel\n"
         "✨ Hilft, Heißhungerattacken zu reduzieren\n✨ Fördert mehr Selbstvertrauen und Wohlbefinden\n\n"
         "Warten Sie nicht länger auf den perfekten Moment – beginnen Sie jetzt.\n\n"
         "👉 Klicken Sie hier und starten Sie noch heute in ein neues Lebensgefühl.")

LOWTICKET = [
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
    anuncio(8, 506, "Ana Paula Receitas", "+300 receitas fit em PDF. Acesso imediato por apenas R$ 17. Saiba mais",
            "https://receitas.lovable.app/", dias=50, dup=2),
]
NUTRA_DE = [
    anuncio(11, 601, "Gesundheit Heute", "Dieser einfache Pferdetrick vor dem Schlafen... Sehen Sie sich das Video an, "
            "bevor es gelöscht wird!", "https://gesund-news.de/vsl/pferd", dias=60, dup=9, video=True),
    anuncio(12, 601, "Gesundheit Heute", "Ärzte sind sprachlos: der Pferde-Trick. Video ansehen",
            "https://www.digistore24.com/redir/123/aff", dias=35, dup=4, video=True),
    anuncio(13, 602, "Amazon.de", "Pferdesalbe 500ml – kostenloser Versand", "https://www.amazon.de/x"),
    anuncio(14, 603, "Reiterhof Müller", "Reitstunden für Kinder, jetzt buchen", "https://reiterhof-mueller.de",
            cta="Jetzt buchen"),
    anuncio(15, 604, "Sofia fischer", SOFIA, "https://aktivlebenheute.de/", dias=33, dup=5, video=True,
            titulo="Starten Sie jetzt Ihre Transformation mit Slim Jara!"),
    anuncio(16, 605, "MediaMarkt", "Neue Fernseher – jetzt im Angebot, warten Sie nicht länger",
            "https://www.mediamarkt.de/tv"),
    anuncio(17, 606, "Riesen Konzern", "Gelatine Trick Video", "https://gesund-artikel.de/article/x", dias=90, dup=3,
            video=True),
]
NUTRA_FR = [
    anuncio(21, 701, "Santé Découvertes", "Ce n'est pas la gélatine elle-même : voici ce qui se cache vraiment derrière "
            "l'astuce de la gélatine rose. Regardez la vidéo.", "https://sante-decouvertes.fr/article/gelatine-rose",
            dias=31, dup=7, video=True, titulo="L'énigme est résolue !"),
]
TOTAIS_PAGINA = {"501": 14, "502": 3, "506": 6, "601": 27, "604": 9, "606": 2500, "701": 41}


class BibliotecaFalsa:
    """Imita a Biblioteca: devolve os anúncios do país pedido, conta ativos por página."""
    bloquear = False
    poucos_na_exata = False

    def __init__(self, *a, **k):
        self.urls = []

    def abrir(self, url, max_anuncios=0):
        self.urls.append(url)
        if BibliotecaFalsa.bloquear:
            return [], None, "Tente novamente mais tarde", True
        if "view_all_page_id=" in url:
            pid = url.split("view_all_page_id=")[1].split("&")[0]
            return [], TOTAIS_PAGINA.get(pid), "", False
        if "country=DE" in url:
            ads = NUTRA_DE
        elif "country=FR" in url:
            ads = NUTRA_FR
        elif "vazio" in url:
            ads = [LOWTICKET[4], LOWTICKET[5]]
        else:
            ads = LOWTICKET
        if BibliotecaFalsa.poucos_na_exata and "keyword_exact_phrase" in url:
            ads = ads[:1]
        objs = comum.parse_payload(payload(ads, len(ads)))
        return list(comum.extrair_anuncios(objs)), comum.extrair_total(objs), "", False

    def fechar(self):
        pass


def rodar(args):
    bib = BibliotecaFalsa()
    minerar_meta.Biblioteca = lambda *a, **k: bib
    sys.argv = ["minerar_meta.py"] + args
    out, err = io.StringIO(), io.StringIO()
    codigo = 0
    with redirect_stdout(out), redirect_stderr(err):
        try:
            minerar_meta.main()
        except SystemExit as e:
            codigo = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    texto = out.getvalue()
    pasta = next((l.split("PASTA: ")[1].strip() for l in texto.splitlines() if l.startswith("PASTA: ")), "")
    linhas = []
    if "\n[" in texto:
        try:
            linhas = json.loads(texto[texto.index("\n[") + 1:])
        except Exception:
            pass
    return {"texto": texto, "log": err.getvalue(), "pasta": Path(pasta) if pasta else None, "linhas": linhas,
            "bib": bib, "codigo": codigo}


def sh(*args, **kw):
    r = subprocess.run(["bash", str(SCRIPTS / "run.sh"), *args], capture_output=True, text=True, **kw)
    return r.stdout + r.stderr


# ---------------------------------------------------------------- testes
def t_leitura():
    secao("1) Leitura dos dados da Meta")
    objs = comum.parse_payload(payload(LOWTICKET, 812))
    ads = list(comum.extrair_anuncios(objs))
    checar(len(ads) == 8, f"lê os 8 anúncios do JSON (leu {len(ads)})")
    checar(comum.extrair_total(objs) == 812, "lê o total de resultados")
    a1 = next(a for a in ads if a["ad_id"] == "1")
    checar(a1["cta"] == "Saiba mais" and "+100 Mapas" in a1["titulo_link"], "lê botão e título do link")
    checar(a1["duplicados"] == 6 and a1["dias"] if "dias" in a1 else a1["duplicados"] == 6, "lê duplicados")
    html = '<script type="application/json">' + payload(NUTRA_DE, 7)[9:] + "</script>"
    checar(len(list(comum.extrair_anuncios(comum.parse_html(html)))) == 7, "lê anúncios embutidos no HTML")
    linhas = "\n".join(json.dumps({"x": i}) for i in range(3))
    checar(len(comum.parse_payload(linhas)) == 3, "lê respostas com vários JSONs por linha")
    checar(comum.total_do_texto("~1,2 mil resultados") == 1200, "entende '~1,2 mil resultados'")
    checar(comum.total_do_texto("~37 results") == 37, "entende '~37 results'")
    checar(comum.precos("De R$ 97 por apenas 19,90") == [97.0, 19.9], "lê preços da copy")
    checar(comum.plataforma("https://www.digistore24.com/redir/1") == "Digistore24", "detecta Digistore24")
    checar(comum.plataforma("https://pay.kiwify.com.br/x") == "Kiwify", "detecta Kiwify")
    checar(comum._dominio_base("https://www.amazon.co.uk/x")[1] == "amazon", "entende domínios .co.uk / .de")


def t_lowticket():
    secao("2) Mineração LOW TICKET (palavra 'pack', nicho geral)")
    r = rodar(["--palavra", "pack", "--nicho", "geral"])
    nomes = [l["pagina"] for l in r["linhas"]]
    checar(r["codigo"] == 0 and r["pasta"] and r["pasta"].exists(), "termina sem erro e cria a pasta")
    checar({"Mariana Oliveira", "Ateliê da Ju", "Ana Paula Receitas"} <= set(nomes), f"mantém low ticket ({nomes})")
    checar(not {"Alibaba.com", "Shopee Brasil", "Bella Moda"} & set(nomes), "descarta Alibaba, Shopee e loja de roupa")
    m = next((l for l in r["linhas"] if l["pagina"] == "Mariana Oliveira"), {})
    checar(m.get("ativos_pagina") == 14, "conta ativos da página (14)")
    checar(all(s in m.get("sinais", "") for s in ("ESCALA", "LUCRATIVO", "TESTANDO")), f"sinais: {m.get('sinais')}")
    checar(r["linhas"] and r["linhas"][0]["pagina"] == "Mariana Oliveira", "Mariana em 1º no ranking")
    a = next((l for l in r["linhas"] if l["pagina"] == "Ateliê da Ju"), {})
    checar("LOW TICKET" in a.get("sinais", "") and "19,90" in a.get("precos", ""), "preço R$ 19,90 e sinal LOW TICKET")
    checar(a.get("plataforma") == "Kiwify", "plataforma Kiwify no ranking")
    checar("view_all_page_id=501" in (m.get("link_biblioteca") or ""), "link da biblioteca da página")
    checar(m.get("por_que_lowticket"), "explica por que é low ticket")
    buscas = [u for u in r["bib"].urls if "q=" in u]
    checar(len(buscas) == 3 and "keyword_exact_phrase" in buscas[0] and "country=BR" in buscas[0],
           "geral: 'pack' exata + 'pack pdf' + 'pack digital', no Brasil")
    for arq in ("ranking.md", "ranking.csv", "anuncios.json", "descartadas.md"):
        checar(r["pasta"] and (r["pasta"] / arq).exists(), f"gera {arq}")
    desc = (r["pasta"] / "descartadas.md").read_text(encoding="utf-8") if r["pasta"] else ""
    checar("Alibaba" in desc and "grande empresa" in desc, "descartadas.md com o motivo")
    checar("DESCARTADAS: 3" in r["texto"], "resumo: 3 descartadas")

    secao("3) Low ticket com nicho (culinária)")
    r = rodar(["--palavra", "pack", "--nicho", "culinaria"])
    buscas = [u for u in r["bib"].urls if "q=" in u]
    checar(len(buscas) == 3 and "pack%20receitas" in buscas[0], "combina a palavra com os termos do nicho")

    secao("4) Várias palavras, sem filtro, nenhum resultado e bloqueio")
    r = rodar(["--palavra", "pack", "--palavra", "kit completo"])
    checar(len([u for u in r["bib"].urls if "q=" in u]) == 6, "duas palavras = 6 buscas no nicho geral")
    r = rodar(["--palavra", "pack", "--sem-filtro"])
    checar(len(r["linhas"]) == 6, f"--sem-filtro mantém as 6 páginas ({len(r['linhas'])})")
    r = rodar(["--palavra", "vazio"])
    checar(r["codigo"] == 4 and "NENHUM_LOWTICKET" in r["texto"] and "DESCARTADAS" in r["texto"],
           "sem low ticket: avisa NENHUM_LOWTICKET com exemplos")
    BibliotecaFalsa.bloquear = True
    r = rodar(["--palavra", "pack"])
    BibliotecaFalsa.bloquear = False
    checar(r["codigo"] == 3 and "NENHUM_ANUNCIO" in r["texto"] and "BLOQUEIO" in r["log"], "bloqueio da Meta: para e avisa")


def t_nutra():
    secao("5) Mineração NUTRA na Alemanha (truque do cavalo, 2 variações)")
    r = rodar(["--modo", "nutra", "--pais", "DE", "--nicho", "ed", "--rotulo", "Truque do cavalo",
               "--palavra", "Pferdetrick", "--palavra", "Pferde-Trick"])
    nomes = [l["pagina"] for l in r["linhas"]]
    buscas = [u for u in r["bib"].urls if "q=" in u]
    checar(all("country=DE" in u for u in r["bib"].urls), "todas as buscas na Alemanha")
    checar(any("Pferdetrick" in u for u in buscas) and any("Pferde-Trick" in u for u in buscas), "as 2 variações em alemão")
    checar("Gesundheit Heute" in nomes and "Sofia fischer" in nomes, f"mantém as ofertas de nutra ({nomes})")
    checar(not {"Amazon.de", "Reiterhof Müller", "MediaMarkt"} & set(nomes), "descarta Amazon.de, haras e MediaMarkt")
    checar("Riesen Konzern" not in nomes, "descarta página com 2.500 ativos (empresa grande)")
    g = next((l for l in r["linhas"] if l["pagina"] == "Gesundheit Heute"), {})
    checar(g.get("ativos_pagina") == 27 and "VSL" in g.get("sinais", "") and "Digistore24" in g.get("plataforma", ""),
           f"Gesundheit Heute: 27 ativos · {g.get('sinais')} · {g.get('plataforma')}")
    s = next((l for l in r["linhas"] if l["pagina"] == "Sofia fischer"), {})
    checar(s.get("produto") == "Slim Jara", f"lê o nome do produto ({s.get('produto')})")
    checar(s.get("tipo_provavel") == "advertorial", f"tipo provável pelo domínio ({s.get('tipo_provavel')})")
    checar("LOW TICKET" not in g.get("sinais", ""), "não marca LOW TICKET no nutra")
    checar(r["pasta"] and "_nutra_DE_ed_Truque-do-cavalo" in r["pasta"].name, "pasta com modo, país, categoria e mecanismo")
    desc = (r["pasta"] / "descartadas.md").read_text(encoding="utf-8") if r["pasta"] else ""
    checar("empresa grande" in desc and "Amazon" in desc, "descartadas.md explica Amazon e a empresa grande")

    secao("6) Nutra na França (advertorial) e reforço quando vem pouco resultado")
    BibliotecaFalsa.poucos_na_exata = True
    r = rodar(["--modo", "nutra", "--pais", "FR", "--nicho", "emagrecimento", "--palavra", "astuce de la gélatine"])
    BibliotecaFalsa.poucos_na_exata = False
    tipos = [u for u in r["bib"].urls if "q=" in u]
    checar(any("keyword_unordered" in u for u in tipos), "frase exata com pouco resultado → busca de novo com todas as palavras")
    f = r["linhas"][0] if r["linhas"] else {}
    checar(f.get("pagina") == "Santé Découvertes" and f.get("tipo_provavel") == "advertorial",
           f"advertorial francês reconhecido ({f.get('tipo_provavel')})")


def t_filtros():
    secao("7) Filtros com os seus exemplos")
    cfg, _ = comum.carregar_config()
    fl = comum.carregar_filtros()

    def lt(txt, pag="", link=""):
        return comum.classificar_lowticket({"pagina": pag, "link": link, "texto": txt, "titulo_link": "", "cta": ""}, fl, cfg)

    def nu(txt, pag="", link="", tit=""):
        return comum.classificar_nutra({"pagina": pag, "link": link, "texto": txt, "titulo_link": tit, "videos": 0,
                                        "formato": "IMAGE", "curtidas": 0}, fl, cfg)
    p, _, _ = lt(MARIANA, "Mariana Oliveira", "https://nutricao.guiapractico.com/")
    checar(p >= cfg["min_score_lowticket"], f"Mariana (low ticket): {p} pontos")
    p, _, si = lt(MARIANA, "Studio X", "https://qualquer.com.br")
    checar(p >= cfg["min_score_lowticket"], f"mesma copy sem ajuda do domínio/nome: {p} pontos")
    p, _, _ = lt("✅ Tênis esportivo\n✅ Frete grátis\n✅ 12x sem juros", "Loja Fit")
    checar(p < cfg["min_score_lowticket"], f"loja de tênis descartada ({p})")
    p, _, si = nu(SOFIA, "Sofia fischer", "https://aktivlebenheute.de/", "Starten Sie jetzt Ihre Transformation mit Slim Jara!")
    checar(p >= 10 and any("gancho de dor" in x for x in si) and any("Slim Jara" in x for x in si), f"Sofia (nutra DE): {p} pontos")
    p, _, _ = nu("Neue Fernseher – jetzt im Angebot, warten Sie nicht länger", "MediaMarkt")
    checar(p < cfg["min_score_nutra"], f"MediaMarkt não passa no nutra ({p})")
    p, _, _ = nu("Try this baking soda trick 30 seconds before bed. Doctors are speechless. Watch the video")
    checar(p >= cfg["min_score_nutra"], f"copy de nutra em inglês ({p})")
    _, m, _ = nu("qualquer", "x", "https://www.amazon.de/x")
    checar("grande empresa" in m, "Amazon.de na lista negra do nutra")
    checar(comum.nome_produto({"texto": "Neue Fernseher im Angebot", "titulo_link": "Fernseher Angebot"}) == "",
           "não confunde substantivo alemão com produto")
    checar(comum.tipo_landing({"link": "https://www.digistore24.com/x", "titulo_link": ""}, fl) == "plataforma/checkout",
           "tipo provável: plataforma/checkout")
    checar(comum.tipo_landing({"link": "https://x.com/quiz/1", "titulo_link": ""}, fl) == "quiz", "tipo provável: quiz")
    checar(comum.tipo_landing({"link": "https://x.com/vsl/a", "titulo_link": ""}, fl) == "VSL", "tipo provável: VSL")


def t_config():
    secao("8) Configurações do usuário")
    pasta = comum.pasta_config()
    cfg_u = json.loads((pasta / "config.json").read_text(encoding="utf-8"))
    checar(set(cfg_u) == {"_como_funciona"}, "config do usuário começa só com a explicação (sem copiar padrões)")
    (pasta / "config.json").write_text(json.dumps({"preco_max": 37, "pais": "PT"}), encoding="utf-8")
    cfg, _ = comum.carregar_config()
    checar(cfg["preco_max"] == 37 and cfg["pais"] == "PT" and cfg["min_score_nutra"] == 3,
           "valor do usuário vale e os novos padrões continuam chegando")
    (pasta / "config.json").write_text("{}", encoding="utf-8")

    fu = json.loads((pasta / "filtros.json").read_text(encoding="utf-8"))
    fu["lista_negra"].append("Minha Concorrente")
    fu["padroes_nutra"].append({"nome": "meu padrão", "peso": 2, "regex": "segredo da vov[oó]"})
    fu["padroes_nutra"].append({"nome": "manifestação / dinheiro", "peso": 9, "regex": "(.*)"})  # versão antiga/errada
    fu["removidos"].append("pdf")
    (pasta / "filtros.json").write_text(json.dumps(fu, ensure_ascii=False), encoding="utf-8")
    fl = comum.carregar_filtros()
    checar("Minha Concorrente" in fl["lista_negra"] and "alibaba" in fl["lista_negra"], "lista negra: fábrica + usuário")
    checar(any(p["nome"] == "meu padrão" for p in fl["padroes_nutra"]), "padrão ensinado pelo usuário entra")
    man = next(p for p in fl["padroes_nutra"] if p["nome"] == "manifestação / dinheiro")
    checar(man["peso"] == 1 and man["regex"] != "(.*)", "correções de fábrica vencem cópias antigas do usuário")
    checar("pdf" not in [t.lower() for t in fl["termos_infoproduto"]], "'removidos' desliga item de fábrica")

    nu = json.loads((pasta / "nutra.json").read_text(encoding="utf-8"))
    nu["paises"].append({"codigo": "CH", "nome": "Suíça", "bandeira": "🇨🇭", "idioma": "alemão"})
    nu["categorias"].append({"id": "ed", "principais": [], "outras": ["Truque da beterraba"]})
    nu["categorias"].append({"id": "memoria", "nome": "Memória", "emoji": "🧠", "principais": ["Truque do café"], "outras": []})
    nu["removidos"] = ["Anaconda natural"]
    (pasta / "nutra.json").write_text(json.dumps(nu, ensure_ascii=False), encoding="utf-8")
    n = comum.carregar_nutra()
    ed = next(c for c in n["categorias"] if c["id"] == "ed")
    checar(any(p["codigo"] == "CH" for p in n["paises"]) and len(n["paises"]) == 9, "país novo (Suíça) somado aos 8")
    checar("Truque da beterraba" in ed["outras"] and "Truque do cavalo" in ed["principais"], "mecanismo novo somado ao ED")
    checar("Anaconda natural" not in ed["outras"], "'removidos' tira mecanismo de fábrica")
    checar(any(c["id"] == "memoria" for c in n["categorias"]), "categoria nova (Memória)")
    tot = sum(len(c["principais"]) + len(c["outras"]) for c in n["categorias"])
    checar(tot >= 100 and all(len(c["principais"]) <= 8 for c in n["categorias"]), f"{tot} mecanismos, até 8 principais por categoria")


def t_reclameaqui():
    secao("9) Reclame Aqui")
    nomes = minerar_reclameaqui.nomes_produto("Comprei o Pack Receitas Fit e não recebi. Curso de Crochê Iniciante não liberou")
    checar(nomes == ["pack receitas fit", "curso de crochê iniciante"], f"extrai nomes de produto ({nomes})")

    def coletar_falso(slug, paginas, log):
        if slug == "kiwify":
            return [{"titulo": "Pack Receitas Fit não chegou", "texto": "Comprei o Pack Receitas Fit e nada", "data": "",
                     "link": "https://www.reclameaqui.com.br/kiwify/x/"},
                    {"titulo": "Reembolso", "texto": "Pedi reembolso do Pack Receitas Fit", "data": "", "link": ""}]
        if slug == "hotmart":
            return [{"titulo": "Curso de Crochê Iniciante", "texto": "não liberou o curso de crochê iniciante", "data": "", "link": ""}]
        return []
    minerar_reclameaqui.coletar = coletar_falso
    sys.argv = ["minerar_reclameaqui.py", "--nicho", "geral"]
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(io.StringIO()):
        minerar_reclameaqui.main()
    txt = out.getvalue()
    dados = json.loads(txt[txt.index("\n[") + 1:])
    top = dados[0] if dados else {}
    checar(top.get("produto") == "pack receitas fit" and top.get("mencoes") == 2, f"ranking por menções ({top.get('produto')})")
    checar("Kiwify" in top.get("plataformas", "") and "facebook.com/ads/library" in top.get("buscar_na_biblioteca", ""),
           "mostra a plataforma e o link pronto para a biblioteca")
    pasta = Path(next(l.split("PASTA: ")[1] for l in txt.splitlines() if l.startswith("PASTA: ")))
    checar((pasta / "ranking.md").exists() and (pasta / "produtos.json").exists(), "gera ranking.md e produtos.json")
    minerar_reclameaqui.coletar = lambda *a: []
    sys.argv = ["minerar_reclameaqui.py"]
    out = io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            minerar_reclameaqui.main()
        cod = 0
    except SystemExit as e:
        cod = e.code
    checar(cod == 3 and "NENHUMA_RECLAMACAO" in out.getvalue(), "Reclame Aqui fora do ar: avisa e sugere o método 2")


def t_comandos():
    secao("10) Comandos do run.sh, diagnóstico e setup")
    checar("SETUP_PENDENTE" in sh("status"), "status antes do setup: SETUP_PENDENTE")
    checar("SETUP_PENDENTE" in sh("meta", "--palavra", "x"), "minerar sem setup: pede a opção 1")
    venv = Path(os.environ["HOME"]) / ".lowticket/.venv/bin"
    venv.mkdir(parents=True, exist_ok=True)
    (venv / "python").write_text("#!/bin/sh\n"); (venv / "python").chmod(0o755)
    checar("SETUP_PENDENTE" in sh("status"), "ambiente sem navegador baixado continua SETUP_PENDENTE")
    (Path(os.environ["HOME"]) / ".lowticket/.navegador_ok").write_text("")
    checar("PRONTO" in sh("status"), "com navegador instalado: PRONTO")
    cfg = json.loads(sh("config"))
    checar({"config", "nichos", "nutra"} <= set(cfg) and cfg["config"]["min_score_lowticket"] == 5, "config mostra tudo combinado")
    fl = json.loads(sh("filtros"))
    checar(len(fl["padroes_nutra"]) >= 16 and len(fl["padroes_copy"]) >= 9, "filtros mostra todos os padrões combinados")
    t = sh("testar", "Müde davon? ✨ Unterstützt den Stoffwechsel ✨ Hilft beim Abnehmen 👉 Klicken Sie hier", "--modo", "nutra")
    checar("lista de benefícios" in t, "lista com ✨ reconhecida mesmo com a legenda numa linha só")
    t = sh("testar", MARIANA, "--pagina", "Mariana Oliveira")
    checar("LOW TICKET" in t, "testar (low ticket)")
    t = sh("testar", SOFIA, "--modo", "nutra", "--pagina", "Sofia fischer", "--link", "https://aktivlebenheute.de/")
    checar("NUTRA" in t, "testar --modo nutra")
    checar("DESCARTADO: grande empresa" in sh("testar", "x", "--link", "https://www.alibaba.com/x"), "testar: lista negra")
    checar("uso:" in sh("qualquercoisa"), "comando desconhecido mostra o uso")
    r = rodar(["--diagnostico"])
    checar("META_OK anuncios_lidos=" in r["texto"] and "bloqueado=False" in r["texto"], "diagnóstico da biblioteca")
    for f in ("run.sh", "setup.sh"):
        ok = subprocess.run(["bash", "-n", str(SCRIPTS / f)]).returncode == 0
        checar(ok, f"{f} sem erro de sintaxe")
    v = subprocess.run(["claude", "plugin", "validate", str(RAIZ)], capture_output=True, text=True)
    checar("Validation passed" in (v.stdout + v.stderr), "plugin validado pelo Claude Code")


def main():
    for t in (t_leitura, t_lowticket, t_nutra, t_filtros, t_config, t_reclameaqui, t_comandos):
        try:
            t()
        except Exception as e:  # um erro numa seção não esconde as outras
            import traceback
            traceback.print_exc()
            checar(False, f"{t.__name__} quebrou: {e}")
    print(f"\n{len(OK)} ok · {len(FALHAS)} falha(s)")
    if FALHAS:
        print("FALHAS:\n  - " + "\n  - ".join(FALHAS))
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
