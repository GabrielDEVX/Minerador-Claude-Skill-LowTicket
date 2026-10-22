#!/usr/bin/env python3
"""Pasta e ficha de cada produto (base das opções 3 a 7).

Cada produto mora em ~/mineracao/produtos/{slug}/ e tem um produto.json com os dados
que o entregável, o funil, os criativos e a campanha usam.

  python3 produtos.py novo "Mapas Mentais de Nutrição"
  python3 produtos.py listar
  python3 produtos.py mostrar mapas-mentais-de-nutricao
  python3 produtos.py validar mapas-mentais-de-nutricao [produto|conteudo|funil]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from comum import carregar_config


def pasta_produtos():
    cfg, _ = carregar_config()
    p = Path(cfg["pasta_saida"]) / "produtos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def slugify(nome):
    s = "".join(c for c in unicodedata.normalize("NFD", nome.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60] or "produto"


MODELO_PRODUTO = {
    "nome": "",
    "slug": "",
    "modo": "lowticket",
    "nicho": "",
    "promessa": "",
    "publico": "",
    "dor_principal": "",
    "mecanismo": "",
    "formato": "infoapp",
    "preco": 0,
    "preco_ancora": 0,
    "checkout": "",
    "link_checkout": "",
    "order_bumps": [],
    "upsell": {},
    "downsell": {},
    "diferenciais": [],
    "bonus": [],
    "garantia_dias": 7,
    "cores": {"primaria": "#7c3aed", "fundo": "#0f0f14"},
    "referencias": [],
    "analise": {},
}

# campos obrigatórios por arquivo (o resto é opcional)
OBRIGATORIOS = {
    "produto": ["nome", "slug", "promessa", "publico", "preco", "formato"],
    "conteudo": ["titulo", "modulos"],
    "funil": ["pagina_vendas"],
}


def slug_seguro(slug):
    """Impede sair da pasta de produtos: reduz o slug ao formato a-z0-9-."""
    s = slugify(str(slug))
    if not s:
        raise SystemExit("SLUG_INVALIDO: use só letras, números e hífen.")
    return s


def dir_produto(slug):
    return pasta_produtos() / slug_seguro(slug)


def caminho(slug, arquivo="produto"):
    return dir_produto(slug) / f"{arquivo}.json"


def validar(slug, arquivo="produto"):
    p = caminho(slug, arquivo)
    if not p.exists():
        return [f"{p.name} não existe em {p.parent}"]
    try:
        dados = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{p.name} tem JSON inválido: {e}"]
    erros = [f"falta '{c}'" for c in OBRIGATORIOS[arquivo] if not dados.get(c)]
    if arquivo == "produto":
        if not isinstance(dados.get("preco"), (int, float)) or dados.get("preco", 0) <= 0:
            erros.append("'preco' precisa ser um número maior que zero (ex.: 19.9)")
        for i, ob in enumerate(dados.get("order_bumps") or []):
            if not ob.get("nome") or not isinstance(ob.get("preco"), (int, float)):
                erros.append(f"order_bumps[{i}] precisa de 'nome' e 'preco' numérico")
    if arquivo == "conteudo":
        for i, m in enumerate(dados.get("modulos") or []):
            if not m.get("titulo"):
                erros.append(f"modulos[{i}] sem 'titulo'")
            if not m.get("itens"):
                erros.append(f"modulos[{i}] sem 'itens'")
            for j, it in enumerate(m.get("itens") or []):
                if not it.get("titulo"):
                    erros.append(f"modulos[{i}].itens[{j}] sem 'titulo'")
                if not (it.get("conteudo") or it.get("arquivo") or it.get("video")):
                    erros.append(f"modulos[{i}].itens[{j}] precisa de 'conteudo', 'arquivo' ou 'video'")
    if arquivo == "funil":
        pv = dados.get("pagina_vendas") or {}
        if not pv.get("headline"):
            erros.append("pagina_vendas sem 'headline'")
        planos = pv.get("planos") or {}
        if not (planos.get("basico") or planos.get("completo")):
            erros.append("pagina_vendas.planos sem 'basico' ou 'completo' (pelo menos um plano)")
        for nome in ("basico", "completo"):
            pl = planos.get(nome)
            if pl and not pl.get("por"):
                erros.append(f"planos.{nome} sem 'por' (preço)")
    return erros


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "novo":
        nome = " ".join(sys.argv[2:]).strip()
        if not nome:
            sys.exit("informe o nome do produto")
        slug = slugify(nome)
        pasta = dir_produto(slug)
        pasta.mkdir(parents=True, exist_ok=True)
        p = pasta / "produto.json"
        if p.exists():
            print(f"JA_EXISTE: {p}")
        else:
            dados = dict(MODELO_PRODUTO, nome=nome, slug=slug)
            p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"CRIADO: {p}")
        print(f"SLUG: {slug}")
    elif cmd == "listar":
        itens = []
        for d in sorted(pasta_produtos().iterdir()):
            p = d / "produto.json"
            if p.exists():
                dados = json.loads(p.read_text(encoding="utf-8"))
                feitos = [n for n in ("ficha.md", "conteudo.json", "infoapp", "funil.json", "pagina", "criativos.md",
                                      "campanha.md") if (d / n).exists()]
                itens.append({"slug": d.name, "nome": dados.get("nome"), "preco": dados.get("preco"),
                              "modo": dados.get("modo"), "feito": feitos})
        print(json.dumps(itens, ensure_ascii=False, indent=1))
    elif cmd == "mostrar":
        c = caminho(sys.argv[2])
        if not c.exists():
            sys.exit(f"NAO_ENCONTRADO: {c}")
        print(c.read_text(encoding="utf-8"))
    elif cmd == "validar":
        arq = sys.argv[3] if len(sys.argv) > 3 else "produto"
        erros = validar(sys.argv[2], arq)
        print("VALIDO" if not erros else "INVALIDO:\n  - " + "\n  - ".join(erros))
        sys.exit(0 if not erros else 1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
