#!/usr/bin/env python3
"""Opcao 5: monta a pagina de vendas em HTML (layout validado) a partir de funil.json.

O Claude escreve a copy e aponta as imagens em funil.json; este script preenche o
template e salva em produtos/{slug}/pagina/index.html. Imagens locais sao copiadas
para pagina/img/. Secoes so aparecem quando ha dados para elas.

  python3 gerar_pagina.py {slug}
"""
import json
import re
import shutil
import sys
from pathlib import Path

from produtos import caminho, pasta_produtos, validar

RAIZ = Path(__file__).resolve().parent.parent
TEMPLATE = RAIZ / "templates" / "pagina.html"


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def moeda(v, padrao=""):
    if isinstance(v, (int, float)):
        return ("R$ %.2f" % v).replace(".", ",")
    return esc(v or padrao)


class Imagens:
    """Copia imagens locais para pagina/img/ e devolve o caminho relativo; mantem URLs http."""
    def __init__(self, base, destino):
        self.base, self.destino, self.faltando = base, destino, []

    def __call__(self, v):
        if not v:
            return ""
        if re.match(r"^https?://", v):
            return v
        origem = Path(v).expanduser()
        if not origem.is_absolute():
            origem = self.base / v
        if not origem.exists():
            self.faltando.append(v)
            return ""
        (self.destino / "img").mkdir(exist_ok=True)
        shutil.copy2(origem, self.destino / "img" / origem.name)
        return "img/" + origem.name


def img_ou_ph(src, classe, rotulo="imagem"):
    return f'<img src="{esc(src)}" class="{classe}" alt="">' if src else f'<div class="{classe} ph">{rotulo}</div>'


def sec_por_dentro(pv, img):
    d = pv.get("por_dentro")
    if not d:
        return ""
    imgs = [img(x) for x in (d.get("imagens") or [])][:4]
    while len(imgs) < 4 and (d.get("imagens") or imgs):
        imgs.append("")
    prev = "".join(img_ou_ph(s, "", "página") for s in imgs) if imgs else ""
    prev = f'<div class="prev">{prev}</div>' if prev else ""
    bullets = "".join(f'<li><span class="i">✓</span>{esc(b)}</li>' for b in (d.get("bullets") or []))
    bl = f'<ul class="chk">{bullets}</ul>' if bullets else ""
    return (f'<div class="claro"><div class="wrap"><section>'
            f'<h2>{esc(d.get("titulo", "Veja o material por dentro."))}</h2>'
            f'{f"<p class=subt>{esc(d.get(chr(34)+"subtitulo"+chr(34), d.get("subtitulo","")))}</p>" if d.get("subtitulo") else ""}'
            f'{prev}{bl}</section></div></div>')


def sec_para_voce(pv):
    d = pv.get("para_voce")
    if not d or not d.get("itens"):
        return ""
    selo = f'<div style="text-align:center"><span class="sel">{esc(d.get("selo","pra quem é"))}</span></div>'
    itens = "".join(f'<div class="it"><span class="i">✓</span><span>{esc(i)}</span></div>' for i in d["itens"])
    return (f'<div class="esc"><div class="wrap"><section>{selo}'
            f'<h2>{esc(d.get("titulo", "Esses mapas são para você que..."))}</h2>'
            f'<div class="g2">{itens}</div></section></div></div>')


def sec_bonus(pv):
    d = pv.get("bonus")
    if not d or not d.get("itens"):
        return ""
    return None  # preenchido fora (precisa do copiador de imagem) -> ver montar


def bloco_bonus(d, img):
    selo = f'<div style="text-align:center"><span class="sel">{esc(d.get("selo","bônus exclusivos"))}</span></div>'
    cards = []
    for i, b in enumerate(d["itens"], 1):
        de = moeda(b.get("de"))
        cards.append(
            f'<div class="bcard">{img_ou_ph(img(b.get("img")), "", "bônus")}'
            f'<span class="et">BÔNUS {i:02d}</span><b>{esc(b.get("nome"))}</b>'
            f'<div class="pr">{f"<span class=de>{de}</span>" if de else ""}<span class="inc">Incluso</span></div></div>')
    total = ""
    if d.get("total"):
        total = (f'<div class="total">Valor total dos bônus: <b>{moeda(d.get("total"))}</b>'
                 f'{f" — mais os mapas mentais, avaliados em <b>{moeda(d.get(chr(34)+"valor_mapas"+chr(34)))}</b>" if d.get("valor_mapas") else ""}</div>')
    return (f'<div class="esc"><div class="wrap"><section>{selo}'
            f'<h2>{esc(d.get("titulo","Quem escolhe o plano completo leva bônus junto."))}</h2>'
            f'{f"<p class=subt>{esc(d.get(chr(34)+"subtitulo"+chr(34)))}</p>" if d.get("subtitulo") else ""}'
            f'<div class="bgrid">{"".join(cards)}</div>{total}</section></div></div>')


def plano(p, checkout, dest=False):
    if not p:
        return ""
    psel = f'<span class="psel">{esc(p.get("selo"))}</span>' if p.get("selo") else ""
    de = moeda(p.get("de"))
    por = moeda(p.get("por")) if not isinstance(p.get("por"), str) else esc(p.get("por"))
    por_html = f'<span>R$ </span>{por.replace("R$ ","").replace("R$","")}' if por else "R$ --"
    bullets = "".join(f"<li>{esc(b)}</li>" for b in (p.get("bullets") or []))
    link = p.get("link_checkout") or checkout or "#"
    return (f'<div class="plano{" dest" if dest else ""}">{psel}'
            f'<h3>{esc(p.get("nome"))}</h3><ul class="mini">{bullets}</ul>'
            f'{f"<div class=de>{de}</div>" if de else ""}'
            f'<div class="por">{por_html}</div>'
            f'<div class="obs">{esc(p.get("obs","pagamento único · acesso imediato"))}</div>'
            f'<a href="{esc(link)}" class="cta">{esc(p.get("cta","QUERO AGORA"))}</a></div>')


def sec_faq(pv):
    faq = pv.get("faq")
    if not faq:
        return ""
    itens = "".join(f'<details><summary>{esc(f.get("p"))}</summary><p>{esc(f.get("r"))}</p></details>' for f in faq)
    return (f'<div class="claro"><div class="wrap"><section>'
            f'<div style="text-align:center"><span class="sel" style="color:var(--mut)">perguntas frequentes</span></div>'
            f'<h2>O que você precisa saber antes de acessar.</h2>'
            f'<div class="faq">{itens}</div></section></div></div>')


def main():
    if len(sys.argv) < 2:
        sys.exit("informe o slug do produto")
    slug = sys.argv[1]
    erros = validar(slug, "produto") + validar(slug, "funil")
    if erros:
        sys.exit("INVALIDO:\n  - " + "\n  - ".join(erros))
    produto = json.loads(caminho(slug, "produto").read_text(encoding="utf-8"))
    funil = json.loads(caminho(slug, "funil").read_text(encoding="utf-8"))
    pv = funil.get("pagina_vendas", {})
    cores = produto.get("cores") or {}
    verde = cores.get("primaria", "#2f8a55")
    escuro = cores.get("escuro") or cores.get("fundo", "#15372a")
    creme = cores.get("creme", "#f4f2ec")

    from produtos import dir_produto
    destino = dir_produto(slug) / "pagina"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    img = Imagens(dir_produto(slug), destino)

    checkout = funil.get("link_checkout") or produto.get("link_checkout") or "#"

    # hero
    selo = f'<span class="sel">{esc(pv.get("selo"))}</span>' if pv.get("selo") else ""
    mock = pv.get("mockup")
    mock_html = img_ou_ph(img(mock), "mock", "mockup do produto") if (mock or True) else ""
    mock_html = f'<img src="{esc(img(mock))}" class="mock" alt="">' if img(mock) else '<div class="mock ph">mockup do produto</div>'
    stats = pv.get("stats") or []
    stats_html = ""
    if stats:
        stats_html = '<div class="stats">' + "".join(
            f'<div><b>{esc(s.get("n"))}</b><span>{esc(s.get("t",""))}</span></div>' for s in stats[:4]) + "</div>"

    # planos
    planos_cfg = pv.get("planos") or {}
    bas = planos_cfg.get("basico")
    comp = planos_cfg.get("completo")
    if not bas and not comp:
        # fallback: um plano só, do produto
        comp = {"nome": produto.get("nome"), "por": produto.get("preco"), "de": produto.get("preco_ancora"),
                "bullets": produto.get("diferenciais") or [], "cta": pv.get("cta", "QUERO AGORA"), "selo": "oferta"}
    planos_html = plano(bas, checkout) + plano(comp, checkout, dest=True)

    bonus = bloco_bonus(pv["bonus"], img) if pv.get("bonus", {}).get("itens") else ""

    html = TEMPLATE.read_text(encoding="utf-8")
    subs = {
        "__COR__": verde, "__ESCURO__": escuro, "__CREME__": creme,
        "__TITULO__": esc(produto.get("nome")),
        "__SELO__": selo,
        "__HEADLINE__": esc(pv.get("headline")).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>"),
        "__SUBHEAD__": esc(pv.get("subhead", "")),
        "__MOCKUP__": mock_html,
        "__STATS__": stats_html,
        "__POR_DENTRO__": sec_por_dentro(pv, img),
        "__PARA_VOCE__": sec_para_voce(pv),
        "__BONUS__": bonus,
        "__PLANOS_SELO__": f'<span class="sel" style="color:var(--mut)">{esc(planos_cfg.get("selo","escolha seu plano"))}</span>',
        "__PLANOS_TITULO__": esc(planos_cfg.get("titulo", pv.get("titulo_oferta", "Acesse hoje."))),
        "__PLANOS_SUBT__": esc(planos_cfg.get("subtitulo", "")),
        "__PLANOS__": planos_html,
        "__GARANTIA_TITULO__": esc(pv.get("garantia_titulo", f"Garantia de {produto.get('garantia_dias', 7)} dias")),
        "__GARANTIA_TEXTO__": esc(pv.get("garantia_texto", "Se não gostar, devolvemos o seu dinheiro.")),
        "__FAQ__": sec_faq(pv),
        "__CTA_FINAL_SELO__": '<span class="sel">pronto para começar</span>',
        "__CTA_FINAL__": esc(pv.get("cta_final", pv.get("headline", "Garanta o seu agora."))),
        "__CTA_FINAL_BOTAO__": esc(pv.get("cta_final_botao", pv.get("cta", "QUERO AGORA"))),
        "__CTA_SUB__": esc(pv.get("cta_sub", "acesso imediato")),
        "__CHECKOUT__": esc((comp or {}).get("link_checkout") or checkout),
        "__RODAPE__": esc(pv.get("rodape", produto.get("nome", ""))),
    }
    for k, v in subs.items():
        html = html.replace(k, v)
    (destino / "index.html").write_text(html, encoding="utf-8")

    print(f"PAGINA: {destino / 'index.html'}")
    print(f"BONUS: {len(pv.get('bonus', {}).get('itens', []))} · PLANOS: {sum(1 for x in (bas, comp) if x)} · FAQ: {len(pv.get('faq', []))}")
    if checkout == "#":
        print("AVISO: sem link de checkout (preencha 'link_checkout' no funil.json)")
    if img.faltando:
        print("IMAGENS_FALTANDO: " + json.dumps(sorted(set(img.faltando)), ensure_ascii=False))


if __name__ == "__main__":
    main()
