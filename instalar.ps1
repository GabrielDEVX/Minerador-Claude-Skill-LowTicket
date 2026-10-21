# Instalador da Central Escala para Windows. Cole no PowerShell:
#   irm https://raw.githubusercontent.com/GabrielDEVX/Minerador-Claude-Skill-LowTicket/main/instalar.ps1 | iex
Write-Host "=== CENTRAL ESCALA - instalacao (Windows) ===" -ForegroundColor Green
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "-> Instalando o Claude Code..."
  irm https://claude.ai/install.ps1 | iex
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Host "Claude Code instalado. Feche e abra o PowerShell e rode este comando de novo." -ForegroundColor Yellow
  return
}
Write-Host "-> Adicionando o catalogo e instalando a skill..."
claude plugin marketplace add GabrielDEVX/Minerador-Claude-Skill-LowTicket 2>$null
claude plugin marketplace update legacy-mentoring 2>$null
claude plugin uninstall lowticket@legacy-mentoring 2>$null
claude plugin install escala@legacy-mentoring
Write-Host ""
Write-Host "OK! Dentro do Claude Code, digite /escala:escala e escolha a opcao 1 (setup)." -ForegroundColor Green
Write-Host "IMPORTANTE: no Windows e preciso ter o 'Git para Windows' instalado (https://git-scm.com/downloads/win)."
