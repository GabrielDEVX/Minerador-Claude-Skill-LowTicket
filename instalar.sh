#!/bin/bash
# Instalador da Central Escala para macOS. Cole no Terminal:
#   curl -fsSL https://raw.githubusercontent.com/GabrielDEVX/Minerador-Claude-Skill-LowTicket-Nutra/main/instalar.sh | bash
set -e
MARKET="GabrielDEVX/Minerador-Claude-Skill-LowTicket-Nutra"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   CENTRAL ESCALA · instalacao"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v claude >/dev/null 2>&1; then
  echo "→ Instalando o Claude Code..."
  curl -fsSL https://claude.ai/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "⚠️  Claude Code instalado, mas o Terminal ainda nao o encontrou."
  echo "    Feche e abra o Terminal e rode este comando de novo."
  exit 1
fi
echo "✓ Claude Code: $(claude --version 2>/dev/null || echo ok)"

echo "→ Adicionando o catalogo e instalando o plugin..."
claude plugin marketplace add "$MARKET" 2>/dev/null || claude plugin marketplace update legacy-mentoring 2>/dev/null || true
claude plugin uninstall lowticket@legacy-mentoring 2>/dev/null || true
claude plugin install escala@legacy-mentoring

echo ""
echo "✅ Instalado!"
echo ""
echo "Agora, dentro do Claude Code, digite uma vez:"
echo "    /escala:escala"
echo "e escolha a opcao 1 (setup). Depois disso, basta digitar /escala."
