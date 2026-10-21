#!/usr/bin/env python3
"""Mostra quantos pontos de low ticket uma copy soma.

  python testar.py "copy do anúncio" [--pagina "Nome"] [--link "https://..."]
  echo "copy" | python testar.py -
"""
import argparse
import sys

from comum import carregar_config, carregar_filtros, classificar_lowticket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("copy", help="texto do anúncio, ou - para ler da entrada")
    ap.add_argument("--pagina", default="")
    ap.add_argument("--link", default="")
    a = ap.parse_args()
    texto = sys.stdin.read() if a.copy == "-" else a.copy
    cfg, _ = carregar_config()
    ad = {"pagina": a.pagina, "link": a.link, "texto": texto, "titulo_link": "", "curtidas": 0, "cta": ""}
    pontos, motivo, sinais = classificar_lowticket(ad, carregar_filtros(), cfg)
    minimo = cfg.get("min_score_lowticket", 3)
    if motivo:
        print(f"DESCARTADO: {motivo}")
    else:
        print(f"PONTOS: {pontos} (mínimo {minimo}) → {'LOW TICKET' if pontos >= minimo else 'DESCARTADO'}")
    for s in sinais:
        print(f"  · {s}")


if __name__ == "__main__":
    main()
