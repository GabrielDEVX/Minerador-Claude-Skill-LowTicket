#!/bin/bash
# Ponto único de entrada (Mac, Linux e Windows com Git Bash).
# run.sh <setup|status|config|filtros|testar|urlscan|radar|favoritos|comparar|versao|analisar|produto|clonar|breakdown|cerebro|infoapp|pagina|utm|meta|reclameaqui> [argumentos]
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
  config)      ESCALA_SCRIPTS="$SCRIPTS" "$PYRUN" -c "import os,sys,json; sys.path.insert(0, os.environ['ESCALA_SCRIPTS']); from comum import config_efetiva; print(json.dumps(config_efetiva(), ensure_ascii=False, indent=1))" ;;
  filtros)     ESCALA_SCRIPTS="$SCRIPTS" "$PYRUN" -c "import os,sys,json; sys.path.insert(0, os.environ['ESCALA_SCRIPTS']); from comum import carregar_filtros; print(json.dumps(carregar_filtros(), ensure_ascii=False, indent=1))" ;;
  testar)      exec "$PYRUN" "$SCRIPTS/testar.py" "$@" ;;
  radar)       exec "$PYRUN" "$SCRIPTS/radar.py" "$@" ;;
  favoritos)   exec "$PYRUN" "$SCRIPTS/favoritos.py" "$@" ;;
  comparar)    exec "$PYRUN" "$SCRIPTS/comparar_nutra.py" "$@" ;;
  versao)      exec "$PYRUN" "$SCRIPTS/versao.py" ;;
  analisar)    exec "$PYRUN" "$SCRIPTS/analisar.py" "$@" ;;
  produto)     exec "$PYRUN" "$SCRIPTS/produtos.py" "$@" ;;
  infoapp)     exec "$PYRUN" "$SCRIPTS/gerar_infoapp.py" "$@" ;;
  pagina)      exec "$PYRUN" "$SCRIPTS/gerar_pagina.py" "$@" ;;
  utm)         exec "$PYRUN" "$SCRIPTS/utm.py" "$@" ;;
  clonar)      exec "$PYRUN" "$SCRIPTS/clonar.py" "$@" ;;
  breakdown)   exec "$PYRUN" "$SCRIPTS/breakdown.py" "$@" ;;
  cerebro)     exec "$PYRUN" "$SCRIPTS/cerebro.py" "$@" ;;
  meta|reclameaqui|urlscan)
    # trava de atualizacao: nao minera desatualizado (ESCALA_SEM_UPDATE=1 pula a trava)
    if [ "${ESCALA_SEM_UPDATE:-0}" != "1" ]; then
      estado="${ESCALA_ESTADO:-$("$PYRUN" "$SCRIPTS/versao.py" --curto 2>/dev/null)}"
      case "$estado" in
        DESATUALIZADA*) set -- $estado
          echo "DESATUALIZADA: ha uma versao mais nova (${3:-nova}, voce tem ${2:-?}). "
          echo "Atualize antes de minerar: claude plugin marketplace update legacy-mentoring"
          echo "(depois abra o Claude Code e rode a opcao 1). Para minerar mesmo assim: ESCALA_SEM_UPDATE=1"
          exit 5 ;;
      esac
    fi
    case "$cmd" in
      urlscan) { [ -n "$PY" ] || true; }; exec "$PYRUN" "$SCRIPTS/minerar_urlscan.py" "$@" ;;
      meta)    { [ -n "$PY" ] && [ -f "$OK" ]; } || { echo "SETUP_PENDENTE: rode a opção 1 (setup e diagnóstico)."; exit 2; }
               exec "$PY" "$SCRIPTS/minerar_meta.py" "$@" ;;
      reclameaqui) { [ -n "$PY" ] && [ -f "$OK" ]; } || { echo "SETUP_PENDENTE: rode a opção 1 (setup e diagnóstico)."; exit 2; }
               exec "$PY" "$SCRIPTS/minerar_reclameaqui.py" "$@" ;;
    esac ;;
  *) echo "uso: run.sh setup|status|config|filtros|testar|urlscan|radar|favoritos|comparar|versao|analisar|produto|clonar|breakdown|cerebro|infoapp|pagina|utm|meta|reclameaqui [args]"; exit 1 ;;
esac
