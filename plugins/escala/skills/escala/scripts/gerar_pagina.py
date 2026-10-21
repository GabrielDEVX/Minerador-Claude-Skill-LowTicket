#!/usr/bin/env python3
"""Opcao 5: monta a pagina de vendas em HTML a partir de funil.json.

O Claude escreve a copy (headline, secoes, bullets, FAQ, bumps) em funil.json;
este script so preenche o template e salva em produtos/{slug}/pagina/index.html.

  python3 gerar_pagina.py {slug}
"""
import json
import sys
from pathlib import Path

from produtos import caminho, pasta_produtos, validar

RAIZ = Path(__file__).resolve().parent.parent
TEMPLATE = RAIZ / "templates" / "pagina.html"


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bloco_secoes(secoes):
    out = []
    for s in secoes or []:
        h = f'<section><h2>{esc(s.get("titulo"))}</h2>'
        if s.get("texto"):
            for p in str(s["texto"]).split("\n\n"):
                h += f'<p style="margin-bottom:12px">{esc(p)}</p>'
        if s.get("bullets"):
            h += '<ul class="bul">' + "".join(f"<li>{esc(b)}</li>" for b in s["bullets"]) + "</ul>"
        if s.get("depoimentos"):
            for d in s["depoimentos"]:
                h += (f'<div class="dep"><div class="nm">{esc(d.get("nome"))} '
                      f'<span class="st">{"★" * int(d.get("estrelas", 5))}</span></div>{esc(d.get("texto"))}</div>')
        out.append(h + "</section>")
    return "\n".join(out)


def bloco_bumps(bumps):
    if not bumps:
        return ""
    out = []
    for b in bumps:
        preco = b.get("preco")
        pt = f'R$ {preco:.2f}'.replace(".", ",") if isinstance(preco, (int, float)) else esc(preco)
        out.append(f'<div class="bump"><div><b>+ {esc(b.get("nome"))}</b>'
                   f'<small style="color:var(--mut)">{esc(b.get("descricao", ""))}</small></div>'
                   f'<span class="p">{pt}</span></div>')
    return "".join(out)


def bloco_faq(faq):
    return "".join(f'<details><summary>{esc(f.get("p"))}</summary><p>{esc(f.get("r"))}</p></details>'
                   for f in (faq or []))


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
    cor = cores.get("primaria", "#7c3aed")

    def moeda(v, padrao=""):
        if isinstance(v, (int, float)):
            return ("R$ %.2f" % v).replace(".", ",")
        return esc(v or padrao)

    checkout = funil.get("link_checkout") or produto.get("link_checkout") or "#"
    video = ""
    if pv.get("video_thumb") or pv.get("video"):
        thumb = pv.get("video_thumb")
        inner = f'<img src="{esc(thumb)}" alt="">' if thumb else '<span style="color:#fff">▶ seu vídeo aqui</span>'
        video = f'<div class="vid">{inner}</div>'

    html = TEMPLATE.read_text(encoding="utf-8")
    subs = {
        "__COR__": cor, "__COR2__": cores.get("secundaria", cor),
        "__TITULO__": esc(produto.get("nome")),
        "__SELO__": esc(pv.get("selo", "OFERTA ESPECIAL")),
        "__HEADLINE__": esc(pv.get("headline")).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>"),
        "__SUBHEAD__": esc(pv.get("subhead", "")),
        "__VIDEO__": video,
        "__CHECKOUT__": esc(checkout),
        "__CTA__": esc(pv.get("cta", "QUERO AGORA")),
        "__CTA_SUB__": esc(pv.get("cta_sub", "acesso imediato")),
        "__SECOES__": bloco_secoes(pv.get("secoes")),
        "__TITULO_OFERTA__": esc(pv.get("titulo_oferta", "Garanta o seu agora")),
        "__DE__": ("de " + moeda(produto.get("preco_ancora"))) if produto.get("preco_ancora") else "",
        "__POR__": moeda(produto.get("preco"), "R$ --"),
        "__BUMPS__": bloco_bumps(produto.get("order_bumps")),
        "__GARANTIA_TITULO__": esc(pv.get("garantia_titulo", f"Garantia de {produto.get('garantia_dias', 7)} dias")),
        "__GARANTIA_TEXTO__": esc(pv.get("garantia_texto", "Se não gostar, devolvemos o seu dinheiro.")),
        "__FAQ__": bloco_faq(pv.get("faq")),
        "__RODAPE__": esc(pv.get("rodape", produto.get("nome", ""))),
    }
    for k, v in subs.items():
        html = html.replace(k, v)

    destino = pasta_produtos() / slug / "pagina"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(html, encoding="utf-8")
    print(f"PAGINA: {destino / 'index.html'}")
    print(f"SECOES: {len(pv.get('secoes', []))} · BUMPS: {len(produto.get('order_bumps', []))} · FAQ: {len(pv.get('faq', []))}")
    if checkout == "#":
        print("AVISO: sem link de checkout (preencha 'link_checkout' no funil.json ou 'link_checkout' no produto.json)")


if __name__ == "__main__":
    main()
