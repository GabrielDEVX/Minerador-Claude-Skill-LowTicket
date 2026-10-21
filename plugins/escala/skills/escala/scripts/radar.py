#!/usr/bin/env python3
"""Comando 'radar': mostra as paginas que mais subiram desde a ultima mineracao."""
import argparse, json, sys
from comum import carregar_config
import historico

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pais")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    cfg, _ = carregar_config()
    pais = (a.pais or cfg["pais"]).upper()
    linhas = historico.resumo(pais)
    if not linhas:
        print(f"RADAR_VAZIO: ainda nao ha historico suficiente para {pais}. "
              "O radar compara minearacoes do mesmo termo feitas em dias diferentes; "
              "rode a mesma busca de novo daqui a alguns dias.")
        sys.exit(3)
    print(f"PAIS: {pais} · PAGINAS: {len(linhas)}")
    print(json.dumps(linhas[: a.top], ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
