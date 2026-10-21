#!/bin/bash
# Ponto único de entrada: run.sh <setup|meta|reclameaqui|status|config> [argumentos]
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/.lowticket/.venv/bin/python"
cmd="$1"; shift

case "$cmd" in
  setup)       exec bash "$SCRIPTS/setup.sh" ;;
  status)      [ -x "$PY" ] && echo "PRONTO" || echo "SETUP_PENDENTE" ;;
  config)      python3 -c "import sys; sys.path.insert(0, '$SCRIPTS'); from comum import pasta_config; print(pasta_config())" ;;
  meta|reclameaqui)
    [ -x "$PY" ] || { echo "SETUP_PENDENTE: rode a opção 1 (setup e diagnóstico)."; exit 2; }
    [ "$cmd" = meta ] && alvo=minerar_meta.py || alvo=minerar_reclameaqui.py
    exec "$PY" "$SCRIPTS/$alvo" "$@" ;;
  *) echo "uso: run.sh setup|status|config|meta|reclameaqui [args]"; exit 1 ;;
esac
