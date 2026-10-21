#!/bin/bash
# Ponto único de entrada: run.sh <setup|status|config|filtros|testar|urlscan|meta|reclameaqui> [argumentos]
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/.lowticket/.venv/bin/python"
OK="$HOME/.lowticket/.navegador_ok"
cmd="$1"; shift

case "$cmd" in
  setup)       exec bash "$SCRIPTS/setup.sh" ;;
  status)      [ -x "$PY" ] && [ -f "$OK" ] && echo "PRONTO" || echo "SETUP_PENDENTE" ;;
  config)      python3 -c "import sys, json; sys.path.insert(0, '$SCRIPTS'); from comum import config_efetiva; print(json.dumps(config_efetiva(), ensure_ascii=False, indent=1))" ;;
  filtros)     python3 -c "import sys, json; sys.path.insert(0, '$SCRIPTS'); from comum import carregar_filtros; print(json.dumps(carregar_filtros(), ensure_ascii=False, indent=1))" ;;
  testar)      exec python3 "$SCRIPTS/testar.py" "$@" ;;
  urlscan)     exec python3 "$SCRIPTS/minerar_urlscan.py" "$@" ;;
  meta|reclameaqui)
    { [ -x "$PY" ] && [ -f "$OK" ]; } || { echo "SETUP_PENDENTE: rode a opção 1 (setup e diagnóstico)."; exit 2; }
    [ "$cmd" = meta ] && alvo=minerar_meta.py || alvo=minerar_reclameaqui.py
    exec "$PY" "$SCRIPTS/$alvo" "$@" ;;
  *) echo "uso: run.sh setup|status|config|filtros|testar|urlscan|meta|reclameaqui [args]"; exit 1 ;;
esac
