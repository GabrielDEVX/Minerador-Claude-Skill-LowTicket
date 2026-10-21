#!/bin/bash
# Instala o ambiente da skill (Python + Playwright + navegador invisível) e faz o diagnóstico.
# Funciona no Mac, no Linux e no Windows (com Git Bash).
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
DADOS="$HOME/.lowticket"
VENV="$DADOS/.venv"
mkdir -p "$DADOS"

# detecta o sistema e o python
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*) SO=windows ;;
  Darwin) SO=mac ;;
  *) SO=linux ;;
esac
if command -v python3 >/dev/null 2>&1; then PYSYS=python3
elif command -v python >/dev/null 2>&1; then PYSYS=python
else
  if [ "$SO" = windows ]; then
    echo "PYTHON_FALTANDO: instale o Python em https://www.python.org/downloads/ (marque 'Add Python to PATH'), feche e abra o terminal e rode o setup de novo."
  elif [ "$SO" = mac ]; then
    echo "PYTHON_FALTANDO: rode 'xcode-select --install' no Terminal, conclua a instalação e rode o setup de novo."
  else
    echo "PYTHON_FALTANDO: instale o python3 pelo gerenciador de pacotes e rode o setup de novo."
  fi
  exit 1
fi

echo "== 1/4 Python ($SO)"
"$PYSYS" --version

# caminho do python dentro do venv: Mac/Linux em bin/, Windows em Scripts/
venv_py(){ [ -x "$VENV/bin/python" ] && echo "$VENV/bin/python" || echo "$VENV/Scripts/python.exe"; }

echo "== 2/4 Ambiente da skill"
if [ ! -x "$(venv_py)" ]; then
  "$PYSYS" -m venv "$VENV" || { echo "ERRO_VENV: não consegui criar o ambiente Python."; exit 1; }
fi
VP="$(venv_py)"
"$VP" -m pip install -q --upgrade pip >/dev/null 2>&1
"$VP" -m pip install -q playwright || { echo "ERRO_PIP: não instalou o Playwright."; exit 1; }

echo "== 3/4 Navegador invisível (Chromium)"
rm -f "$DADOS/.navegador_ok"
"$VP" -m playwright install chromium || { echo "ERRO_CHROMIUM: não baixou o navegador. Verifique a internet e rode a opção 1 de novo."; exit 1; }
: > "$DADOS/.navegador_ok"

echo "== Atalho /escala"
# aponta para a cópia do catálogo (atualizada a cada 'claude plugin marketplace update'); se não existir, para esta pasta
ALVO="$HOME/.claude/plugins/marketplaces/legacy-mentoring/plugins/escala/skills/escala"
[ -f "$ALVO/SKILL.md" ] || ALVO="$(cd "$SCRIPTS/.." && pwd)"
ATALHO="$HOME/.claude/skills/escala"
mkdir -p "$HOME/.claude/skills"
# remove um atalho nosso anterior (link, ou cópia marcada)
if [ -L "$ATALHO" ] || { [ -f "$ATALHO/SKILL.md" ] && grep -q "atalho-central-escala" "$ATALHO/SKILL.md" 2>/dev/null; }; then
  rm -rf "$ATALHO"
fi
if [ -e "$ATALHO" ]; then
  echo "ATALHO_EXISTE: já existe outra skill chamada 'escala' em $ATALHO; use /escala:escala."
elif ln -s "$ALVO" "$ATALHO" 2>/dev/null; then
  echo "ATALHO_OK: agora dá para abrir a ferramenta digitando /escala"
elif cp -r "$ALVO" "$ATALHO" 2>/dev/null; then
  # Windows/sem symlink: cópia (marcada para poder atualizar depois)
  printf '\n<!-- atalho-central-escala -->\n' >> "$ATALHO/SKILL.md" 2>/dev/null
  echo "ATALHO_OK: agora dá para abrir a ferramenta digitando /escala"
else
  echo "ATALHO_PULADO: não consegui criar o atalho; use /escala:escala para abrir."
fi

echo "== 4/4 Diagnóstico na Biblioteca de Anúncios"
"$VP" "$SCRIPTS/minerar_meta.py" --diagnostico
echo "SETUP_CONCLUIDO"
