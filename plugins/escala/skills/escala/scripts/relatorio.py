"""Relatório visual: transforma as linhas da mineração numa página HTML premium.

Gera relatorio.html na pasta da mineração: cards por oferta com sinais, tendência
(mini-gráfico), copy, plataforma, preço e botões (ver na biblioteca, abrir landing,
favoritar). Filtros e ordenação funcionam na própria página, sem internet.
"""
import html
import json
from datetime import datetime


def _spark(pontos, cor="#8b5cf6"):
    pts = [p for p in (pontos or []) if isinstance(p, (int, float))]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1
    w, h = 72, 22
    passo = w / (len(pts) - 1)
    d = " ".join(f"{i*passo:.1f},{h - (p-lo)/rng*(h-3) - 1.5:.1f}" for i, p in enumerate(pts))
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<polyline points="{d}" fill="none" stroke="{cor}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round"/></svg>')


TEND_COR = {"SUBINDO": "#22c55e", "NOVA": "#38bdf8", "ESTÁVEL": "#a1a1aa", "CAINDO": "#f87171"}
TEND_ICONE = {"SUBINDO": "▲", "NOVA": "✦", "ESTÁVEL": "→", "CAINDO": "▼"}


def _card(l, i, modo):
    t = l.get("tendencia") or {}
    estado = t.get("estado", "")
    cor = TEND_COR.get(estado, "#a1a1aa")
    sinais = [s.strip() for s in (l.get("sinais") or "").split(",") if s.strip()]
    chips = "".join(f'<span class="chip s-{html.escape(s.split()[0].lower())}">{html.escape(s)}</span>' for s in sinais)
    tend_txt = estado + (f' {t["variacao"]:+d}' if t.get("variacao") else "")
    ativos = l.get("ativos_pagina") or l.get("anuncios_na_busca") or 0
    preco = l.get("precos") or ""
    produto = l.get("produto") or ""
    tipo = l.get("tipo_provavel") or ""
    plat = l.get("plataforma") or ""
    bib = l.get("link_biblioteca") or l.get("anuncio_top") or ""
    land = l.get("landing") or ""
    copy = (l.get("copy_top") or "")[:240]
    dados_fav = html.escape(json.dumps({"pagina": l.get("pagina"), "page_id": l.get("page_id"),
                                        "link_biblioteca": bib, "landing": land, "plataforma": plat,
                                        "produto": produto, "sinais": l.get("sinais")}, ensure_ascii=False), quote=True)
    return f"""<article class="card" data-sinais="{html.escape(('|'.join(sinais)).lower())}" data-tend="{html.escape(estado.lower())}"
  data-ativos="{ativos}" data-dias="{l.get('dias_max',0)}" data-busca="{html.escape((str(l.get('pagina',''))+' '+produto+' '+copy).lower(), quote=True)}">
  <div class="top">
    <span class="rank">{i}</span>
    <div class="nome">
      <b>{html.escape(str(l.get('pagina') or '—'))}</b>
      {f'<span class="prod">{html.escape(produto)}</span>' if produto else ''}
    </div>
    <span class="tend" style="color:{cor}">{TEND_ICONE.get(estado,'')} {html.escape(tend_txt)}{_spark(t.get('pontos'), cor)}</span>
  </div>
  <div class="chips">{chips}</div>
  <div class="nums">
    <span title="anúncios ativos">📣 <b>{ativos}</b> ativos</span>
    <span title="dias rodando">📅 {l.get('dias_max',0)} dias</span>
    {f'<span title="variações de vídeo">🎬 {l.get("variacoes_video",0)}</span>' if l.get('variacoes_video') else ''}
    {f'<span title="preço">🏷️ {html.escape(preco)}</span>' if preco else ''}
    {f'<span title="plataforma">🛒 {html.escape(plat)}</span>' if plat else ''}
    {f'<span class="tipo">{html.escape(tipo)}</span>' if tipo else ''}
  </div>
  {f'<p class="copy">{html.escape(copy)}</p>' if copy else ''}
  <div class="acoes">
    {f'<a href="{html.escape(bib)}" target="_blank" rel="noopener">📚 Ver anúncios</a>' if bib else ''}
    {f'<a href="{html.escape(land)}" target="_blank" rel="noopener" class="sec">🔗 Landing</a>' if land else ''}
    <button class="fav" data-fav="{dados_fav}" title="Salvar nos favoritos">☆ Salvar</button>
  </div>
</article>"""


def gerar(linhas, pasta, meta):
    cards = "\n".join(_card(l, i + 1, meta.get("modo", "lowticket")) for i, l in enumerate(linhas))
    titulo = html.escape(meta.get("titulo", "Mineração"))
    subt = html.escape(meta.get("subtitulo", ""))
    quando = datetime.now().strftime("%d/%m/%Y %H:%M")
    n = len(linhas)
    subindo = sum(1 for l in linhas if (l.get("tendencia") or {}).get("estado") == "SUBINDO")
    novas = sum(1 for l in linhas if (l.get("tendencia") or {}).get("estado") == "NOVA")
    pagina = PAGINA.replace("__TITULO__", titulo).replace("__SUBT__", subt).replace("__QUANDO__", quando) \
        .replace("__N__", str(n)).replace("__SUBINDO__", str(subindo)).replace("__NOVAS__", str(novas)) \
        .replace("__CARDS__", cards)
    (pasta / "relatorio.html").write_text(pagina, encoding="utf-8")
    return pasta / "relatorio.html"


PAGINA = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITULO__ · Central Escala</title>
<style>
*{box-sizing:border-box;margin:0}:root{--bg:#0b0b10;--card:#15151f;--card2:#1b1b27;--tx:#ececf1;--mut:#8b8b99;--bd:#262633;--ac:#8b5cf6}
body{background:var(--bg);color:var(--tx);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;padding:0 0 60px}
header{position:sticky;top:0;z-index:9;background:rgba(11,11,16,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--bd);padding:16px 18px}
h1{font-size:19px;font-weight:800;letter-spacing:-.3px}h1 b{color:var(--ac)}
.sub{color:var(--mut);font-size:13px;margin-top:2px}
.stats{display:flex;gap:16px;margin-top:10px;flex-wrap:wrap}.stats span{font-size:13px;color:var(--mut)}.stats b{color:var(--tx);font-size:16px}
.bar{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
input,select{background:var(--card2);border:1px solid var(--bd);color:var(--tx);border-radius:9px;padding:8px 11px;font-size:13px;outline:none}
input:focus,select:focus{border-color:var(--ac)}input{flex:1;min-width:150px}
.grid{max-width:900px;margin:18px auto;padding:0 14px;display:grid;gap:12px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:15px;padding:15px 16px;transition:.15s}
.card:hover{border-color:#36364a;transform:translateY(-1px)}
.top{display:flex;align-items:flex-start;gap:11px}
.rank{background:var(--card2);color:var(--mut);font-weight:700;font-size:12px;width:26px;height:26px;border-radius:8px;display:grid;place-items:center;flex:none}
.nome{flex:1;min-width:0}.nome b{font-size:16px;font-weight:700}.prod{display:block;color:var(--ac);font-size:12.5px;font-weight:600;margin-top:1px}
.tend{font-size:12px;font-weight:700;display:flex;align-items:center;gap:5px;white-space:nowrap}.spark{display:block}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 0}
.chip{font-size:11px;font-weight:700;padding:3px 8px;border-radius:20px;background:#23232f;color:#c3c3d0;letter-spacing:.2px}
.chip.s-escala{background:#3b1d1d;color:#fca5a5}.chip.s-lucrativo{background:#13331f;color:#86efac}
.chip.s-testando{background:#2a2140;color:#c4b5fd}.chip.s-low{background:#2a2410;color:#fcd34d}.chip.s-vsl{background:#102a33;color:#7dd3fc}
.nums{display:flex;gap:14px;flex-wrap:wrap;margin-top:11px;font-size:13px;color:var(--mut)}.nums b{color:var(--tx)}
.tipo{background:#23232f;padding:1px 8px;border-radius:6px;font-size:11.5px}
.copy{margin-top:10px;color:#b8b8c6;font-size:13px;max-height:3em;overflow:hidden}
.acoes{display:flex;gap:8px;margin-top:13px;flex-wrap:wrap}
.acoes a,.acoes button{font-size:12.5px;font-weight:700;padding:7px 12px;border-radius:9px;border:0;cursor:pointer;text-decoration:none}
.acoes a{background:var(--ac);color:#fff}.acoes a.sec{background:var(--card2);color:var(--tx);border:1px solid var(--bd)}
.acoes .fav{background:var(--card2);color:var(--tx);border:1px solid var(--bd)}.acoes .fav.on{background:#2a2410;color:#fcd34d;border-color:#5b4d1a}
.vazio{text-align:center;color:var(--mut);padding:40px}
footer{text-align:center;color:var(--mut);font-size:12px;margin-top:26px}footer a{color:var(--ac);text-decoration:none}
</style></head><body>
<header>
  <h1>Central <b>Escala</b> · __TITULO__</h1>
  <div class="sub">__SUBT__ · gerado em __QUANDO__</div>
  <div class="stats"><span><b>__N__</b> ofertas</span><span>▲ <b>__SUBINDO__</b> subindo</span><span>✦ <b>__NOVAS__</b> novas</span></div>
  <div class="bar">
    <input id="q" placeholder="🔎 buscar por página, produto ou copy…">
    <select id="fs"><option value="">todos os sinais</option><option value="escala">🔥 escala</option><option value="lucrativo">💰 lucrativo</option><option value="testando">🎬 testando</option><option value="low">🏷️ low ticket</option><option value="vsl">🎥 vsl</option></select>
    <select id="ft"><option value="">tendência: todas</option><option value="subindo">▲ subindo</option><option value="nova">✦ novas</option><option value="estável">→ estável</option><option value="caindo">▼ caindo</option></select>
    <select id="or"><option value="">ordem original</option><option value="ativos">mais ativos</option><option value="dias">mais dias</option><option value="sobe">quem mais subiu</option></select>
  </div>
</header>
<div class="grid" id="grid">
__CARDS__
<div class="vazio" id="vazio" hidden>Nada encontrado com esses filtros.</div>
</div>
<footer>Central Escala · <a href="https://instagram.com/gabrielrodriguesfx" target="_blank">@gabrielrodriguesfx</a> · os favoritos ficam salvos neste navegador</footer>
<script>
const grid=document.getElementById('grid'),cards=[...grid.querySelectorAll('.card')];
const q=document.getElementById('q'),fs=document.getElementById('fs'),ft=document.getElementById('ft'),or=document.getElementById('or');
function aplicar(){
 const tq=q.value.toLowerCase().trim(),vs=fs.value,vt=ft.value;let vis=0;
 cards.forEach(c=>{
  let ok=(!tq||c.dataset.busca.includes(tq))&&(!vs||c.dataset.sinais.includes(vs))&&(!vt||c.dataset.tend===vt);
  c.hidden=!ok;if(ok)vis++;
 });
 document.getElementById('vazio').hidden=vis>0;
 const v=or.value;if(v){const s=[...cards].filter(c=>!c.hidden).sort((a,b)=>{
  if(v==='ativos')return b.dataset.ativos-a.dataset.ativos;
  if(v==='dias')return b.dataset.dias-a.dataset.dias;
  if(v==='sobe')return (b.querySelector('.tend')?.textContent.match(/[+-]\d+/)||[0])[0]-(a.querySelector('.tend')?.textContent.match(/[+-]\d+/)||[0])[0];
  return 0;});s.forEach(c=>grid.insertBefore(c,document.getElementById('vazio')));}
}
[q,fs,ft,or].forEach(e=>e.addEventListener('input',aplicar));
const K='escala_favoritos';
function favs(){try{return JSON.parse(localStorage.getItem(K)||'[]')}catch(e){return[]}}
function marca(){const ids=favs().map(f=>f.page_id+'');document.querySelectorAll('.fav').forEach(b=>{
 try{const d=JSON.parse(b.dataset.fav);const on=ids.includes(d.page_id+'');b.classList.toggle('on',on);b.textContent=on?'★ Salvo':'☆ Salvar';}catch(e){}});}
document.querySelectorAll('.fav').forEach(b=>b.addEventListener('click',()=>{
 let d;try{d=JSON.parse(b.dataset.fav)}catch(e){return}let f=favs();const i=f.findIndex(x=>x.page_id+''===d.page_id+'');
 if(i>=0)f.splice(i,1);else f.push({...d,quando:new Date().toISOString().slice(0,10)});
 localStorage.setItem(K,JSON.stringify(f));marca();}));
marca();
</script></body></html>"""
