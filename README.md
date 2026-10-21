# Legacy Mentoring · Central Low Ticket

Plugin para o Claude Code que minera ofertas low ticket escaladas na Biblioteca de Anúncios da Meta e no Reclame Aqui. Ele roda em segundo plano, sem abrir o seu navegador.

## Antes de começar

- Mac (macOS 13 ou mais novo)
- Conta paga do Claude (Pro, Max, Team ou Enterprise)
- Claude Code instalado. Se não tiver, cole no Terminal:

  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  ```

  Depois feche e abra o Terminal e rode `claude` uma vez para fazer login.

## Instalar

No Terminal:

```bash
claude plugin marketplace add GabrielDEVX/Minerador-Claude-Skill-LowTicket
claude plugin install lowticket@legacy-mentoring
```

## Usar

```bash
cd ~ && claude
```

Dentro do Claude Code, digite:

```
/lowticket:lowticket
```

1. Na primeira vez, escolha **1 (setup e diagnóstico)**. Leva alguns minutos.
2. Depois, **2 (minerar ofertas escaladas)**: escolha o método, o nicho e a palavra-chave.

Os resultados ficam em `~/mineracao/` (para abrir: `open ~/mineracao`).

## Novidades

**1.1.0**
- Filtro low ticket: ignora Alibaba, Shopee, Amazon, bancos, marcas e lojas de produto físico.
- Reconhece a estrutura da copy de infoproduto (gancho de dor, "+100 …", "Ideal para:" com lista de emojis, CTA "saiba mais / veja por dentro", preço âncora).
- Menus novos, mais organizados.
- Configurações › 12: ensine o filtro colando a legenda de um anúncio.

## Atualizar

```bash
claude plugin marketplace update legacy-mentoring
```

As suas configurações (nichos, palavras-chave, faixa de preço) ficam em `~/.lowticket/` e não se perdem nas atualizações.

## Problemas comuns

| Mensagem | O que fazer |
|---|---|
| `command not found: claude` | Instale o Claude Code (comando acima) e abra um Terminal novo |
| `PYTHON_FALTANDO` | Rode `xcode-select --install`, conclua e rode o setup de novo |
| `anuncios_lidos=0` ou `BLOQUEIO` | Espere alguns minutos e tente de novo, com menos palavras por vez |
| `SETUP_PENDENTE` | Rode a opção 1 do menu |
