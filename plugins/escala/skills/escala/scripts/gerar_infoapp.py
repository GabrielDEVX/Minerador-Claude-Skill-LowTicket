#!/usr/bin/env python3
"""Opcao 4: gera o entregavel em formato de app (infoapp / PWA).

Le ~/mineracao/produtos/{slug}/produto.json e conteudo.json e monta a pasta infoapp/:
  index.html  manifest.webmanifest  sw.js  icone.svg  arquivos/
e um infoapp.zip pronto para subir (Netlify Drop, Vercel, Hostinger...).

  python3 gerar_infoapp.py {slug}
"""
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

from produtos import caminho, pasta_produtos, validar

RAIZ = Path(__file__).resolve().parent.parent
TEMPLATE = RAIZ / "templates" / "infoapp.html"


def iniciais(nome):
    ws = [w for w in re.findall(r"[0-9A-Za-zÀ-ú]+", nome) if len(w) > 1]
    return ("".join(w[0] for w in ws[:2]) or (nome[:2] if nome else "AP")).upper()


def icone_svg(nome, cor):
    ini = "".join(c for c in unicodedata.normalize("NFD", iniciais(nome)) if unicodedata.category(c) != "Mn")
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<rect width="512" height="512" rx="110" fill="{cor}"/>'
            '<text x="50%" y="53%" font-family="Arial,Helvetica,sans-serif" font-size="200" font-weight="700" '
            f'fill="#ffffff" text-anchor="middle" dominant-baseline="central">{ini}</text></svg>')


def copiar_arquivos(conteudo, base, destino):
    """Arquivos locais citados no conteudo vao para infoapp/arquivos; links http ficam como estao."""
    pasta = destino / "arquivos"
    faltando = []
    for m in conteudo.get("modulos", []):
        for it in m.get("itens", []):
            for campo in ("arquivo", "video", "imagem"):
                v = it.get(campo)
                if not v or re.match(r"^https?://", v):
                    continue
                origem = Path(v).expanduser()
                if not origem.is_absolute():
                    origem = base / v
                if not origem.exists():
                    faltando.append(v)
                    continue
                pasta.mkdir(exist_ok=True)
                shutil.copy2(origem, pasta / origem.name)
                it[campo] = "arquivos/" + origem.name
    return faltando


def main():
    if len(sys.argv) < 2:
        sys.exit("informe o slug do produto")
    slug = sys.argv[1]
    from produtos import dir_produto
    base = dir_produto(slug)
    erros = validar(slug, "produto")
    if erros:
        sys.exit("INVALIDO_PRODUTO:\n  - " + "\n  - ".join(erros))
    erros = validar(slug, "conteudo")
    if erros:
        sys.exit("INVALIDO_CONTEUDO:\n  - " + "\n  - ".join(erros))
    produto = json.loads(caminho(slug, "produto").read_text(encoding="utf-8"))
    conteudo = json.loads(caminho(slug, "conteudo").read_text(encoding="utf-8"))

    destino = base / "infoapp"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    faltando = copiar_arquivos(conteudo, base, destino)

    cores = produto.get("cores") or {}
    cor = cores.get("primaria", "#7c3aed")
    fundo = cores.get("fundo", "#0e0e14")
    # bonus: podem vir do conteudo.json (com conteudo/arquivo/link) ou dos order_bumps/bonus do produto
    bonus = conteudo.get("bonus")
    if bonus is None:
        bonus = []
        for b in (produto.get("bonus") or produto.get("order_bumps") or []):
            if isinstance(b, dict):
                bonus.append({"titulo": b.get("nome") or b.get("titulo"), "descricao": b.get("descricao", "Bônus incluso"),
                              "link": b.get("link", ""), "img": b.get("img", "")})
    # copia imagens/arquivos citados nos bônus (mesma logica dos itens)
    for b in bonus:
        for campo in ("arquivo", "video", "imagem", "img"):
            v = b.get(campo)
            if not v or re.match(r"^https?://", v):
                continue
            origem = Path(v).expanduser()
            if not origem.is_absolute():
                origem = base / v
            if origem.exists():
                (destino / "arquivos").mkdir(exist_ok=True)
                shutil.copy2(origem, destino / "arquivos" / origem.name)
                b[campo] = "arquivos/" + origem.name
            else:
                faltando.append(v)
    suporte = conteudo.get("suporte") or produto.get("suporte") or {}
    titulo = conteudo.get("titulo") or produto.get("nome") or "Meu App"
    descricao = produto.get("promessa") or ""
    dados = {"titulo": titulo, "slug": slug, "promessa": descricao, "modulos": conteudo.get("modulos", []),
             "bonus": bonus, "suporte": suporte}

    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("__TITULO__", _esc(titulo)).replace("__TITULO_CURTO__", _esc(titulo[:28]))
            .replace("__PROMESSA__", _esc(descricao)).replace("__COR__", cor).replace("__FUNDO__", fundo)
            .replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")))
    (destino / "index.html").write_text(html, encoding="utf-8")
    (destino / "icone.svg").write_text(icone_svg(titulo, cor), encoding="utf-8")
    manifest = {"name": titulo, "short_name": titulo[:18], "start_url": "./index.html", "display": "standalone",
                "background_color": fundo, "theme_color": cor,
                "icons": [{"src": "icone.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}]}
    (destino / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    (destino / "sw.js").write_text(SW.replace("__V__", str(abs(hash(titulo)) % 100000)), encoding="utf-8")

    zip_path = base / "infoapp.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(destino.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(destino))

    n_itens = sum(len(m.get("itens", [])) for m in conteudo.get("modulos", []))
    print(f"INFOAPP: {destino / 'index.html'}")
    print(f"ZIP: {zip_path}")
    print(f"MODULOS: {len(conteudo.get('modulos', []))} · ITENS: {n_itens} · BONUS: {len(bonus)} · SUPORTE: {'sim' if suporte else 'não'}")
    if faltando:
        print("ARQUIVOS_FALTANDO: " + json.dumps(faltando, ensure_ascii=False))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


SW = """const C='app-__V__';
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(['./','./index.html','./manifest.webmanifest','./icone.svg'])))});
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(n=>n!==C).map(n=>caches.delete(n))))));
self.addEventListener('fetch',e=>{if(e.request.method!=='GET')return;e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).then(res=>{try{if(res.ok&&new URL(e.request.url).origin===location.origin){const cp=res.clone();caches.open(C).then(c=>c.put(e.request,cp))}}catch(_){}return res}).catch(()=>caches.match('./index.html'))))});
"""


if __name__ == "__main__":
    main()
