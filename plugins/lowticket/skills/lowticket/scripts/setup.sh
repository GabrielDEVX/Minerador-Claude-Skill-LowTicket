#!/bin/bash
# Instala o ambiente da skill (Python + Playwright + Chromium invisível) e faz o diagnóstico.
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
DADOS="$HOME/.lowticket"
VENV="$DADOS/.venv"
mkdir -p "$DADOS"

echo "== 1/4 Python"
if ! command -v python3 >/dev/null 2>&1; then
  echo "PYTHON_FALTANDO: rode 'xcode-select --install' no Terminal, conclua a instalação e rode o setup de novo."
  exit 1
fi
python3 --version

echo "== 2/4 Ambiente da skill ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV" || { echo "ERRO_VENV"; exit 1; }
fi
"$VENV/bin/python" -m pip install -q --upgrade pip >/dev/null 2>&1
"$VENV/bin/python" -m pip install -q playwright || { echo "ERRO_PIP: não instalou o Playwright"; exit 1; }

echo "== 3/4 Navegador invisível (Chromium)"
"$VENV/bin/python" -m playwright install chromium || { echo "ERRO_CHROMIUM"; exit 1; }

echo "== 4/4 Diagnóstico na Biblioteca de Anúncios"
"$VENV/bin/python" "$SCRIPTS/minerar_meta.py" --diagnostico
echo "SETUP_CONCLUIDO"
