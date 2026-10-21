"""Funções compartilhadas: config, preços, parse do JSON da biblioteca da Meta."""
import json
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # pasta da skill (padrões)
DADOS = Path(os.path.expanduser("~/.lowticket"))       # pasta do usuário (sobrevive a atualizações)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")


def pasta_config():
    """Copia os arquivos padrão para ~/.lowticket/config na primeira vez e usa de lá."""
    destino = DADOS / "config"
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("config.json", "nichos.json"):
        if not (destino / nome).exists():
            (destino / nome).write_text((RAIZ / "config" / nome).read_text(encoding="utf-8"), encoding="utf-8")
    return destino


def carregar_config():
    pasta = pasta_config()
    cfg = json.loads((pasta / "config.json").read_text(encoding="utf-8"))
    nichos = json.loads((pasta / "nichos.json").read_text(encoding="utf-8"))
    cfg["pasta_saida"] = os.path.expanduser(cfg.get("pasta_saida", "~/mineracao"))
    return cfg, nichos


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
        "texto": " ".join(p for p in partes if p).strip()[:600],
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
