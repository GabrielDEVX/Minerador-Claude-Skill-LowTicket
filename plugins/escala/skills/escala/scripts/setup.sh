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
rm -f "$DADOS/.navegador_ok"
"$VENV/bin/python" -m playwright install chromium || { echo "ERRO_CHROMIUM: não baixou o navegador. Verifique a internet e rode a opção 1 de novo."; exit 1; }
touch "$DADOS/.navegador_ok"

echo "== Atalho /escala"
# aponta para a cópia do catálogo (atualizada a cada 'claude plugin marketplace update'); se não existir, para esta pasta
ALVO="$HOME/.claude/plugins/marketplaces/legacy-mentoring/plugins/escala/skills/escala"
[ -f "$ALVO/SKILL.md" ] || ALVO="$(cd "$SCRIPTS/.." && pwd)"
ATALHO="$HOME/.claude/skills/escala"
mkdir -p "$HOME/.claude/skills"
if [ -L "$ATALHO" ] || { [ -f "$ATALHO/SKILL.md" ] && grep -q "atalho-central-escala" "$ATALHO/SKILL.md"; }; then
  rm -rf "$ATALHO"
fi
if [ -e "$ATALHO" ]; then
  echo "ATALHO_EXISTE: já existe outra skill chamada 'escala' em $ATALHO; use /escala:escala."
else
  ln -s "$ALVO" "$ATALHO" && echo "ATALHO_OK: agora dá para abrir a ferramenta digitando /escala"
fi

echo "== 4/4 Diagnóstico na Biblioteca de Anúncios"
"$VENV/bin/python" "$SCRIPTS/minerar_meta.py" --diagnostico
echo "SETUP_CONCLUIDO"
