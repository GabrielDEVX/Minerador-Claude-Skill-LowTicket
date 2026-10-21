"""Funções compartilhadas: config, preços, parse do JSON da biblioteca da Meta."""
import json
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # pasta da skill (padrões)
DADOS = Path(os.path.expanduser("~/.lowticket"))       # pasta do usuário (sobrevive a atualizações)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")


MODELOS_USUARIO = {
    # o usuário guarda só o que mudou/acrescentou; os padrões de fábrica sempre vêm da versão instalada
    "config.json": {"_como_funciona": "Coloque aqui só os valores que você quer mudar. O resto vem da versão instalada."},
    "filtros.json": {"_como_funciona": "Seus acréscimos ao filtro. Somados aos de fábrica a cada versão. "
                                       "Para desligar um item de fábrica, coloque o texto (ou o nome do padrão) em 'removidos'.",
                     "termos_infoproduto": [], "termos_ecommerce": [], "dominios_lowticket": [], "lista_negra": [],
                     "padroes_copy": [], "dominios_nutra": [], "padroes_nutra": [], "tipos_landing": [], "removidos": []},
    "nutra.json": {"_como_funciona": "Seus países e mecanismos extras de nutra. Somados aos de fábrica a cada versão.",
                   "paises": [], "categorias": []},
}


def pasta_config():
    """Cria ~/.lowticket/config na primeira vez. nichos.json é copiado inteiro (o usuário edita a lista)."""
    destino = DADOS / "config"
    destino.mkdir(parents=True, exist_ok=True)
    if not (destino / "nichos.json").exists():
        (destino / "nichos.json").write_text((RAIZ / "config" / "nichos.json").read_text(encoding="utf-8"), encoding="utf-8")
    for nome, modelo in MODELOS_USUARIO.items():
        if not (destino / nome).exists():
            (destino / nome).write_text(json.dumps(modelo, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def _ler(caminho):
    return json.loads(caminho.read_text(encoding="utf-8"))


def carregar_config():
    pasta = pasta_config()
    cfg = _ler(RAIZ / "config" / "config.json")        # padrões novos de cada versão
    cfg.update(_ler(pasta / "config.json"))             # valores que o usuário mudou
    nichos = _ler(pasta / "nichos.json")
    cfg["pasta_saida"] = os.path.expanduser(cfg.get("pasta_saida", "~/mineracao"))
    return cfg, nichos


def carregar_filtros():
    """Junta os filtros padrão da versão instalada com o que o usuário adicionou (nada se perde)."""
    padrao = _ler(RAIZ / "config" / "filtros.json")
    usuario = _ler(pasta_config() / "filtros.json")
    removidos = {_sem_acento(x) for x in usuario.get("removidos", [])}
    out = {}
    for chave in ("termos_infoproduto", "termos_ecommerce", "dominios_lowticket", "lista_negra", "dominios_nutra"):
        vistos, lista = set(), []
        for item in padrao.get(chave, []) + usuario.get(chave, []):
            k = _sem_acento(item)
            if k not in vistos and k not in removidos:
                vistos.add(k)
                lista.append(item)
        out[chave] = lista
    por_nome = {p["nome"]: p for p in usuario.get("padroes_copy", [])}
    por_nome.update({p["nome"]: p for p in padrao.get("padroes_copy", [])})   # fábrica vence: correções chegam a todos
    out["padroes_copy"] = [p for n, p in por_nome.items() if _sem_acento(n) not in removidos]
    por_nome = {p["nome"]: p for p in usuario.get("padroes_nutra", [])}
    por_nome.update({p["nome"]: p for p in padrao.get("padroes_nutra", [])})
    out["padroes_nutra"] = [p for n, p in por_nome.items() if _sem_acento(n) not in removidos]
    out["tipos_landing"] = usuario.get("tipos_landing", []) + padrao.get("tipos_landing", [])
    return out


def carregar_nutra():
    """Países e mecanismos de nutra: padrão da versão + o que o usuário adicionou."""
    padrao = _ler(RAIZ / "config" / "nutra.json")
    usuario = _ler(pasta_config() / "nutra.json")
    paises = {p["codigo"]: p for p in padrao["paises"]}
    paises.update({p["codigo"]: p for p in usuario.get("paises", [])})
    cats = {c["id"]: {**c, "principais": list(c["principais"]), "outras": list(c.get("outras", []))}
            for c in padrao["categorias"]}
    removidos = {_sem_acento(x) for x in usuario.get("removidos", [])}
    for c in usuario.get("categorias", []):
        base = cats.setdefault(c["id"], {**c, "principais": [], "outras": []})
        for k in ("principais", "outras"):
            for m in c.get(k, []):
                if m not in base["principais"] and m not in base["outras"]:
                    base[k].append(m)
    for c in cats.values():
        for k in ("principais", "outras"):
            c[k] = [m for m in c[k] if _sem_acento(m) not in removidos]
    return {"paises": list(paises.values()), "categorias": list(cats.values())}


def config_efetiva():
    """Configuração final (fábrica + usuário) para mostrar no menu de configurações."""
    cfg, nichos = carregar_config()
    cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
    if cfg.get("urlscan_api_key"):
        cfg["urlscan_api_key"] = "configurada"          # nunca mostra a chave
    return {"arquivo_usuario": str(pasta_config()), "config": cfg, "nichos": nichos, "nutra": carregar_nutra()}


def plataforma(link):
    l = (link or "").lower()
    for nome, marcas in [("Digistore24", ["digistore24", "ds24"]), ("ClickBank", ["clickbank", "clkbank", "hop."]),
                         ("BuyGoods", ["buygoods"]), ("MaxWeb", ["maxweb"]), ("CartPanda", ["cartpanda"]),
                         ("Shopify", ["myshopify", "/products/"]), ("Hotmart", ["hotmart"]), ("Kiwify", ["kiwify"]),
                         ("Cakto", ["cakto"]), ("Monetizze", ["monetizze"]), ("Braip", ["braip"])]:
        if any(m in l for m in marcas):
            return nome
    return ""


def _checar_lista_negra(ad, filtros, cfg):
    pagina = ad.get("pagina") or ""
    pag_norm = _sem_acento(pagina).strip()
    host, base, _ = _dominio_base(ad.get("link"))
    negra = {_sem_acento(b) for b in filtros["lista_negra"]}
    if base and base.replace("-", "") in {b.replace(" ", "").replace("-", "") for b in negra}:
        return f"grande empresa ({host})"
    for b in negra:
        if pag_norm == b or any(pag_norm == f"{b} {s}" for s in ("brasil", "br", "oficial", "store", "loja", "shop")):
            return f"grande empresa ({pagina})"
    curtidas = ad.get("curtidas") or 0
    if curtidas and curtidas > cfg.get("max_curtidas_pagina", 300000):
        return f"página grande ({curtidas:,} curtidas)".replace(",", ".")
    return ""


def classificar_nutra(ad, filtros, cfg):
    """Devolve (pontos, motivo_descartado_ou_vazio, sinais) para o modo nutra."""
    motivo = _checar_lista_negra(ad, filtros, cfg)
    if motivo:
        return 0, motivo, []
    pontos, sinais = 0, []
    link = (ad.get("link") or "").lower()
    plat = plataforma(link)
    if plat:
        pontos += 3
        sinais.append(f"plataforma {plat}")
    elif any(d in link for d in filtros.get("dominios_nutra", [])):
        pontos += 2
        sinais.append("landing de VSL/advertorial")
    txt = _sem_acento(ad.get("texto", "") + "\n" + ad.get("titulo_link", ""))
    padroes = [p for p in filtros.get("padroes_nutra", []) if _regex(p["regex"]).search(txt)]
    if padroes:
        pontos += min(9, sum(int(p.get("peso", 1)) for p in padroes))
        sinais.append("copy: " + ", ".join(p["nome"] for p in padroes[:5]))
    produto = nome_produto(ad)
    if produto:
        pontos += 1
        sinais.append(f"produto: {produto}")
    pagina = (ad.get("pagina") or "").strip()
    if NOME_PESSOA_RE.match(pagina) and not SUFIXO_EMPRESA.search(pagina):
        pontos += 1
        sinais.append("página com nome de pessoa")
    if (ad.get("videos") or ad.get("formato") == "VIDEO"):
        pontos += 1
        sinais.append("criativo em vídeo")
    return pontos, "", sinais


_PALAVRAS_COMUNS = {"mit", "sie", "ihre", "ihr", "der", "die", "das", "und", "the", "you", "your", "with", "this", "avec",
                    "vous", "votre", "les", "con", "tu", "su", "com", "seu", "sua", "para", "per", "il", "la", "le",
                    "jetzt", "heute", "now", "today", "starten", "start", "klicken", "click", "cliquez", "clique",
                    "warten", "reduzieren", "unterstutzt", "hilft", "fordert", "facebook", "instagram"}


def nome_produto(ad):
    """Nome de produto que aparece na legenda E no título do link (ex.: 'Slim Jara')."""
    titulo = ad.get("titulo_link") or ""
    texto = ad.get("texto") or ""
    if not titulo or not texto:
        return ""
    candidatos = re.findall(r"\b([A-ZÀ-Ú][a-zà-ú0-9]{2,}(?:[ -][A-ZÀ-Ú][a-zà-ú0-9]{1,})?)\b", titulo)
    for c in candidatos:
        if " " not in c and "-" not in c:
            continue          # só nomes de 2 palavras (no alemão todo substantivo tem maiúscula)
        if any(_sem_acento(w) in _PALAVRAS_COMUNS for w in re.split(r"[ -]", c)):
            continue
        if c in texto:
            return c
    return ""


def tipo_landing(ad, filtros):
    """Tipo provável da landing pelo link, domínio e título (a página não é aberta)."""
    alvo = _sem_acento((ad.get("link") or "") + " " + (ad.get("titulo_link") or ""))
    for t in filtros.get("tipos_landing", []):
        if _regex(t["regex"]).search(alvo):
            return t["tipo"]
    return ""


# ---------- filtro low ticket ----------
def _sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")


def _dominio_base(link):
    from urllib.parse import urlparse
    host = urlparse(link or "").netloc.lower().split(":")[0]
    partes = [p for p in host.split(".") if p and p != "www"]
    # remove sufixos tipo com.br / net / org
    sufixos = {"com", "br", "net", "org", "io", "app", "co", "site", "online", "store", "shop", "info", "biz",
               "de", "fr", "es", "it", "uk", "pt", "us", "ch", "at", "lu", "nl", "be", "ca", "au", "mx", "ar", "eu", "ie"}
    while len(partes) > 1 and partes[-1] in sufixos:
        partes.pop()
    # partes agora = [subdominio..., dominio]; ex.: nutricao.guiapractico.com -> ['nutricao', 'guiapractico']
    return host, (partes[-1] if partes else ""), len(partes)


NOME_PESSOA_RE = re.compile(r"^[A-ZÀ-Ú][a-zà-ú]+(?:\s+(?:d[aeo]s?\s+|van\s+|von\s+|de\s+la\s+)?[A-ZÀ-Úa-zà-ú][a-zà-ú]+){1,3}$")
SUFIXO_EMPRESA = re.compile(r"\b(ltda|s\.?a\.?|eireli|me|group|grupo|brasil|oficial|store|loja|shop|imoveis|imóveis|"
                            r"bank|banco|seguros|motors|veiculos|veículos|farma|clinica|clínica|hospital)\b", re.I)


_REGEX_CACHE = {}


def _regex(padrao):
    if padrao not in _REGEX_CACHE:
        try:
            import unicodedata  # tira acentos sem mudar maiúsculas (\W, \S, \D precisam continuar maiúsculos)
            limpo = "".join(c for c in unicodedata.normalize("NFD", padrao) if unicodedata.category(c) != "Mn")
            _REGEX_CACHE[padrao] = re.compile(limpo, re.M | re.I)
        except re.error:
            _REGEX_CACHE[padrao] = re.compile(r"(?!x)x")   # padrão inválido nunca casa
    return _REGEX_CACHE[padrao]


def classificar_lowticket(ad, filtros, cfg):
    """Devolve (pontos, motivo_descartado_ou_vazio, sinais)."""
    pagina = ad.get("pagina") or ""
    pag_norm = _sem_acento(pagina).strip()
    host, base, n_labels = _dominio_base(ad.get("link"))
    texto = _sem_acento(" ".join([ad.get("texto", ""), ad.get("titulo_link", "")]))

    negra = {_sem_acento(b) for b in filtros["lista_negra"]}
    negra_sem_espaco = {b.replace(" ", "").replace("-", "") for b in negra}
    if base and base.replace("-", "") in negra_sem_espaco:
        return 0, f"grande empresa ({host})", []
    for b in negra:
        if pag_norm == b or any(pag_norm == f"{b} {s}" for s in ("brasil", "br", "oficial", "store", "loja", "shop")):
            return 0, f"grande empresa ({pagina})", []

    curtidas = ad.get("curtidas") or 0
    if curtidas and curtidas > cfg.get("max_curtidas_pagina", 300000):
        return 0, f"página grande ({curtidas:,} curtidas)".replace(",", "."), []

    pontos, sinais = 0, []
    achados = [t for t in filtros["termos_infoproduto"] if _sem_acento(t) in texto]
    if achados:
        pontos += min(6, 2 * len(achados))
        sinais.append("termos: " + ", ".join(achados[:4]))

    ps = [p for p in precos(ad.get("texto", "") + " " + ad.get("titulo_link", ""))
          if cfg["preco_min"] <= p <= cfg["preco_max"]]
    if ps:
        pontos += 3
        sinais.append("preço low ticket")

    if any(d in (ad.get("link") or "").lower() for d in filtros["dominios_lowticket"]):
        pontos += 3
        sinais.append("checkout/landing de infoproduto")
    elif n_labels >= 2:
        pontos += 1
        sinais.append("subdomínio por produto")

    if NOME_PESSOA_RE.match(pagina.strip()) and not SUFIXO_EMPRESA.search(pagina):
        pontos += 1
        sinais.append("página com nome de pessoa")

    # estrutura da copy (gancho de dor, "+100 X", "ideal para:", lista com emoji, CTA...)
    copy_txt = _sem_acento(ad.get("texto", ""))
    padroes = [p for p in filtros.get("padroes_copy", []) if _regex(p["regex"]).search(copy_txt)]
    if padroes:
        pontos += min(8, sum(int(p.get("peso", 1)) for p in padroes))
        sinais.append("copy: " + ", ".join(p["nome"] for p in padroes[:4]))

    if _sem_acento(ad.get("cta", "")) in ("saiba mais", "ver detalhes", "comprar agora", "baixar", "obter oferta"):
        pontos += 1

    eco = [t for t in filtros["termos_ecommerce"] if _sem_acento(t) in texto]
    if eco:
        pontos -= 2 * len(eco)
        sinais.append("e-commerce: " + ", ".join(eco[:3]))

    return pontos, "", sinais


# ---------- preços ----------
PRECO_RE = re.compile(
    r"R\$\s*(\d{1,4}(?:[.,]\d{2})?)"           # R$ 19,90 / R$19 / R$ 1.000
    r"|(?<![\d,.])(\d{1,3},\d{2})(?![\d])",    # 19,90 solto
    re.I,
)


def precos(texto):
    out = []
    for m in PRECO_RE.finditer(texto or ""):
        bruto = m.group(1) or m.group(2)
        if "," in bruto:
            valor = bruto.replace(".", "").replace(",", ".")
        else:
            valor = bruto.replace(".", "")
        try:
            v = float(valor)
        except ValueError:
            continue
        if 1 <= v <= 5000:
            out.append(v)
    return out


def fmt_preco(v):
    return ("R$ %.2f" % v).replace(".", ",")


# ---------- parse da Meta ----------
def iter_dicts(obj):
    pilha = [obj]
    while pilha:
        atual = pilha.pop()
        if isinstance(atual, dict):
            yield atual
            pilha.extend(atual.values())
        elif isinstance(atual, list):
            pilha.extend(atual)


def parse_payload(texto):
    """Respostas do /api/graphql: um ou vários JSONs (às vezes com prefixo 'for (;;);')."""
    texto = (texto or "").strip()
    if texto.startswith("for (;;);"):
        texto = texto[len("for (;;);"):]
    try:
        return [json.loads(texto)]
    except Exception:
        pass
    objs = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            objs.append(json.loads(linha))
        except Exception:
            continue
    return objs


SCRIPT_JSON_RE = re.compile(r'<script type="application/json"[^>]*>(.*?)</script>', re.S)


def parse_html(html):
    """Dados embutidos no HTML inicial da biblioteca."""
    objs = []
    for bloco in SCRIPT_JSON_RE.findall(html or ""):
        if "ad_archive_id" not in bloco and "search_results_connection" not in bloco:
            continue
        try:
            objs.append(json.loads(bloco))
        except Exception:
            continue
    return objs


def _texto(v):
    if isinstance(v, dict):
        t = v.get("text")
        if not t and isinstance(v.get("markup"), dict):
            t = re.sub(r"<[^>]+>", " ", v["markup"].get("__html") or "")
        return t or ""
    return str(v or "")


def normalizar_anuncio(d):
    snap = d.get("snapshot") or {}
    cards = snap.get("cards") or []
    partes = [_texto(snap.get("body")), snap.get("title") or "", snap.get("link_description") or "",
              snap.get("caption") or ""]
    for c in cards:
        partes += [_texto(c.get("body")), c.get("title") or "", c.get("link_description") or ""]
    link = snap.get("link_url") or next((c.get("link_url") for c in cards if c.get("link_url")), "") or ""
    videos = len(snap.get("videos") or []) + sum(
        1 for c in cards if c.get("video_hd_url") or c.get("video_sd_url"))
    formato = (snap.get("display_format") or ("VIDEO" if videos else "IMAGE")).upper()
    return {
        "ad_id": str(d.get("ad_archive_id")),
        "page_id": str(d.get("page_id") or snap.get("page_id") or ""),
        "pagina": d.get("page_name") or snap.get("page_name") or "",
        "inicio_ts": d.get("start_date") or 0,
        "duplicados": int(d.get("collation_count") or 1),
        "link": link,
        "texto": "\n".join(p for p in partes if p).strip()[:1500],
        "titulo_link": " ".join(x for x in [snap.get("title") or "", snap.get("link_description") or ""] if x),
        "curtidas": int(snap.get("page_like_count") or 0),
        "cta": snap.get("cta_text") or next((c.get("cta_text") for c in cards if c.get("cta_text")), "") or "",
        "videos": videos,
        "formato": formato,
        "ativo": d.get("is_active", True),
    }


def extrair_anuncios(objs):
    for obj in objs:
        for d in iter_dicts(obj):
            if "ad_archive_id" in d and ("snapshot" in d or "page_id" in d):
                try:
                    yield normalizar_anuncio(d)
                except Exception:
                    continue


def extrair_total(objs):
    """Total de resultados da busca/página (search_results_connection.count)."""
    for obj in objs:
        for d in iter_dicts(obj):
            conn = d.get("search_results_connection")
            if isinstance(conn, dict) and isinstance(conn.get("count"), int):
                return conn["count"]
    return None


TOTAL_TEXTO_RE = re.compile(r"~?\s*([\d.,]+)\s*(?:mil\s*)?(resultados|results)", re.I)


def total_do_texto(texto):
    m = TOTAL_TEXTO_RE.search(texto or "")
    if not m:
        return None
    bruto = m.group(1)
    try:
        if "mil" in m.group(0).lower():
            return int(round(float(bruto.replace(".", "").replace(",", ".")) * 1000))
        return int(bruto.replace(".", "").replace(",", ""))
    except ValueError:
        return None
