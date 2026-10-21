#!/bin/bash
# Ponto único de entrada (Mac, Linux e Windows com Git Bash).
# run.sh <setup|status|config|filtros|testar|urlscan|radar|favoritos|comparar|versao|analisar|produto|infoapp|pagina|utm|meta|reclameaqui> [argumentos]
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
OK="$HOME/.lowticket/.navegador_ok"

# python do venv: bin/python (Mac/Linux) ou Scripts/python.exe (Windows)
PY=""
for p in "$HOME/.lowticket/.venv/bin/python" "$HOME/.lowticket/.venv/Scripts/python.exe"; do
  [ -x "$p" ] && PY="$p" && break
done
# python do sistema (antes do setup, para os comandos que só usam a biblioteca padrão)
if command -v python3 >/dev/null 2>&1; then SYS=python3; elif command -v python >/dev/null 2>&1; then SYS=python; else SYS=python3; fi
PYRUN="$SYS"   # comandos que só usam a biblioteca padrão rodam com o python do sistema (o venv é só para a mineração)

cmd="$1"; shift

case "$cmd" in
  setup)       exec bash "$SCRIPTS/setup.sh" ;;
  status)      { [ -n "$PY" ] && [ -f "$OK" ]; } && echo "PRONTO" || echo "SETUP_PENDENTE" ;;
  config)      "$PYRUN" -c "import sys, json; sys.path.insert(0, r'$SCRIPTS'); from comum import config_efetiva; print(json.dumps(config_efetiva(), ensure_ascii=False, indent=1))" ;;
  filtros)     "$PYRUN" -c "import sys, json; sys.path.insert(0, r'$SCRIPTS'); from comum import carregar_filtros; print(json.dumps(carregar_filtros(), ensure_ascii=False, indent=1))" ;;
  testar)      exec "$PYRUN" "$SCRIPTS/testar.py" "$@" ;;
  urlscan)     exec "$PYRUN" "$SCRIPTS/minerar_urlscan.py" "$@" ;;
  radar)       exec "$PYRUN" "$SCRIPTS/radar.py" "$@" ;;
  favoritos)   exec "$PYRUN" "$SCRIPTS/favoritos.py" "$@" ;;
  comparar)    exec "$PYRUN" "$SCRIPTS/comparar_nutra.py" "$@" ;;
  versao)      exec "$PYRUN" "$SCRIPTS/versao.py" ;;
  analisar)    exec "$PYRUN" "$SCRIPTS/analisar.py" "$@" ;;
  produto)     exec "$PYRUN" "$SCRIPTS/produtos.py" "$@" ;;
  infoapp)     exec "$PYRUN" "$SCRIPTS/gerar_infoapp.py" "$@" ;;
  pagina)      exec "$PYRUN" "$SCRIPTS/gerar_pagina.py" "$@" ;;
  utm)         exec "$PYRUN" "$SCRIPTS/utm.py" "$@" ;;
  meta|reclameaqui)
    { [ -n "$PY" ] && [ -f "$OK" ]; } || { echo "SETUP_PENDENTE: rode a opção 1 (setup e diagnóstico)."; exit 2; }
    [ "$cmd" = meta ] && alvo=minerar_meta.py || alvo=minerar_reclameaqui.py
    exec "$PY" "$SCRIPTS/$alvo" "$@" ;;
  *) echo "uso: run.sh setup|status|config|filtros|testar|urlscan|radar|favoritos|comparar|versao|analisar|produto|infoapp|pagina|utm|meta|reclameaqui [args]"; exit 1 ;;
esac
