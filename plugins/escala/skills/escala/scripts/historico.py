"""Radar: histórico de cada página ao longo do tempo (acompanhamento no tempo).

Guarda, a cada mineração, quantos anúncios ativos cada página tinha. Numa nova
mineração mostra quem está SUBINDO (escalando agora) e quem parou.

Base única em ~/.lowticket/radar.json:
  { "BR": { "<page_id>": { "pagina": "...", "historico": [{"data","ativos","anuncios"}] } } }
"""
import json
from datetime import datetime, timezone

from comum import DADOS

ARQUIVO = DADOS / "radar.json"


def _carregar():
    if ARQUIVO.exists():
        try:
            return json.loads(ARQUIVO.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _salvar(dados):
    DADOS.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def registrar(linhas, pais, quando=None):
    """Grava um ponto no histórico de cada página e devolve as linhas com a tendência."""
    data = (quando or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    dados = _carregar()
    pais_d = dados.setdefault(pais, {})
    for l in linhas:
        pid = str(l.get("page_id") or l.get("pagina") or "")
        if not pid:
            continue
        ativos = int(l.get("ativos_pagina") or 0) or int(l.get("anuncios_na_busca") or 0)
        reg = pais_d.setdefault(pid, {"pagina": l.get("pagina"), "historico": []})
        reg["pagina"] = l.get("pagina") or reg.get("pagina")
        hist = reg["historico"]
        if hist and hist[-1]["data"] == data:
            hist[-1] = {"data": data, "ativos": max(ativos, hist[-1]["ativos"]), "anuncios": l.get("anuncios_na_busca")}
        else:
            hist.append({"data": data, "ativos": ativos, "anuncios": l.get("anuncios_na_busca")})
        reg["historico"] = hist[-30:]
        l["tendencia"] = _tendencia(hist, ativos)
    _salvar(dados)
    return linhas


def _tendencia(hist, ativos_agora):
    """NOVA, SUBINDO (+N), ESTÁVEL, CAINDO (-N) comparando com o ponto anterior."""
    anteriores = [h for h in hist[:-1]] if hist and hist[-1].get("ativos") == ativos_agora else hist
    if not anteriores:
        return {"estado": "NOVA", "variacao": 0, "antes": None, "pontos": [h["ativos"] for h in hist]}
    antes = anteriores[-1]["ativos"]
    dif = ativos_agora - antes
    if antes <= 0:
        estado = "SUBINDO" if ativos_agora > 0 else "ESTÁVEL"
    elif dif >= max(3, round(antes * 0.25)):
        estado = "SUBINDO"
    elif dif <= -max(3, round(antes * 0.25)):
        estado = "CAINDO"
    else:
        estado = "ESTÁVEL"
    return {"estado": estado, "variacao": dif, "antes": antes, "pontos": [h["ativos"] for h in hist]}


def resumo(pais):
    """Para o comando 'radar': páginas que mais subiram desde o penúltimo ponto."""
    dados = _carregar().get(pais, {})
    linhas = []
    for pid, reg in dados.items():
        hist = reg.get("historico") or []
        if len(hist) < 2:
            continue
        atual, antes = hist[-1]["ativos"], hist[-2]["ativos"]
        linhas.append({"page_id": pid, "pagina": reg.get("pagina"), "ativos": atual, "antes": antes,
                       "variacao": atual - antes, "scans": len(hist), "primeiro": hist[0]["data"],
                       "ultimo": hist[-1]["data"], "pontos": [h["ativos"] for h in hist]})
    linhas.sort(key=lambda r: r["variacao"], reverse=True)
    return linhas
