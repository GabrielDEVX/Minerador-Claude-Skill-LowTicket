---
name: lowticket
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/run.sh *)
description: Central de operação low ticket com menu numerado (setup, minerar ofertas escaladas na Biblioteca de Anúncios da Meta ou no Reclame Aqui, analisar produto, gerar entregável, modelar funil, criativos, Meta Ads, configurações). Use quando o usuário digitar /lowticket, pedir o menu, ou pedir para minerar ofertas, packs, kits ou infoprodutos baratos (9,90, 19,90).
---

# Central Low Ticket

Você conduz o usuário por menus numerados. **Sempre mostre o menu exatamente no formato abaixo e espere o número.** Aceite também o nome da opção ou um texto livre que deixe a escolha clara. Responda sempre em português.

Todos os comandos passam por um único script (sempre exatamente assim):

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh <comando> [argumentos]
```

Os dados do usuário (ambiente Python, configurações) ficam em `~/.lowticket/`. As minerações ficam em `~/mineracao/`.

## Menu principal

```
1  setup e diagnóstico
2  minerar ofertas escaladas
3  analisar e definir produto
4  gerar entregável
5  modelar funil
6  gerar criativos
7  meta ads
8  configurações

digite o número
```

Na primeira vez que o usuário abrir o menu, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh status`. Se a saída for `SETUP_PENDENTE`, avise em uma linha que é preciso rodar a opção 1 antes da 2.

---

## 1 · Setup e diagnóstico

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh setup
```

Leva alguns minutos na primeira vez (baixa o navegador invisível). Interprete a saída:
- `SETUP_CONCLUIDO` + `META_OK anuncios_lidos=N` com N > 0 → tudo pronto. Diga isso e volte ao menu.
- `PYTHON_FALTANDO` → peça para rodar `xcode-select --install`, aceitar a instalação e escolher 1 de novo.
- `anuncios_lidos=0` ou `bloqueado=True` → a Meta não entregou anúncios ao navegador invisível. Sugira esperar alguns minutos e rodar de novo; se persistir, rode com `--visivel` para ver a tela: `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh meta --diagnostico --visivel`.
- Qualquer `ERRO_*` → mostre a mensagem e a linha relevante.

---

## 2 · Minerar ofertas escaladas

### Passo 1 — método

```
mineração de ofertas

método

1  reclame aqui (grátis · scraps gateways BR)
2  biblioteca de anúncios (meta · busca visual)

digite o número
```

### Passo 2 — nicho

Leia a lista em `~/.lowticket/config/nichos.json` (se não existir, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` antes) (campo `nichos`) e mostre numerada, com o `nome` de cada uma:

```
escolha o nicho para buscar

1  geral (todos os nichos)
2  saúde / emagrecimento
3  artesanato
4  culinária
5  beleza
6  educação / concurso
7  renda / digital
8  esotérico
9  design / social media

digite o número
```

### Passo 3 — palavra-chave (só no método 2; no método 1 é opcional)

Mostre a lista `palavras` de `~/.lowticket/config/nichos.json`, numerada:

```
palavras-chave

1   pack
2   mega pack
3   kit completo
4   +500
5   +1000
6   combo
7   atividades
8   projetos
9   19,90
10  9,90
11  por apenas 9,90

escolha uma palavra-chave ou digite a sua
```

Se o usuário digitar várias (ex. "1, 3, 9"), rode uma mineração para cada uma, em sequência.

### Passo 4 — rodar (em segundo plano)

**NUNCA use Claude in Chrome, Playwright MCP ou qualquer ferramenta de navegador para isto.** A mineração roda num navegador invisível dentro do script, sem abrir nada na tela do usuário.

Avise em uma linha: "Minerando em segundo plano, leva de 2 a 6 minutos." Depois rode (timeout de 10 min):

Método 2 — biblioteca:
```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh meta --palavra "{PALAVRA}" --nicho {ID_DO_NICHO}
```

Método 1 — Reclame Aqui:
```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh reclameaqui --nicho {ID_DO_NICHO} [--palavra "{PALAVRA}"]
```

`{ID_DO_NICHO}` é o campo `id` em `nichos.json` (geral, saude, artesanato, culinaria, beleza, educacao, renda, esoterico, design).

Se a saída trouxer `NENHUM_ANUNCIO`, `NENHUMA_RECLAMACAO` ou `BLOQUEIO`, diga o que aconteceu em uma frase e ofereça: outra palavra, o outro método ou a opção 1 para diagnosticar.

### Passo 5 — entregar o resultado (método 2)

O script imprime `PASTA:` e um JSON com as páginas ranqueadas. Mostre uma tabela com as **até 15 melhores**, nesta ordem de colunas:

| # | Página | Ativos | Dias | Variações vídeo | Preço | Sinais | Biblioteca |
|---|---|---|---|---|---|---|---|

- **Biblioteca**: o `link_biblioteca` como link markdown `[abrir](url)`. Se vier vazio, use `anuncio_top`.
- **Ativos**: `ativos_pagina` (se vazio, mostre `anuncios_na_busca` seguido de `+`).
- **Sinais**: os campos de `sinais`, com estes significados (explique a legenda uma vez, embaixo da tabela):
  - **ESCALA**: página com 5+ anúncios ativos
  - **LUCRATIVO**: anúncio rodando há 30+ dias
  - **TESTANDO VÍDEOS**: vídeos com variações (sinal de que está funcionando)
  - **LOW TICKET**: preço entre R$ 7 e R$ 47 nos criativos

Depois da tabela:
1. Destaque em 2–3 linhas as páginas que têm **ESCALA + LUCRATIVO** juntas (são as mais fortes).
2. Diga onde ficaram os arquivos: `{PASTA}/ranking.md` e `ranking.csv`.
3. Feche com o próximo passo, exatamente assim:

```
quando encontrar uma oferta boa

copie o nome da página ou o link do anúncio
→ rode 3 (analisar e definir produto)
→ ou rode 5 (modelar funil) se já tem o link da página
```

### Passo 5 — entregar o resultado (método 1)

Mostre tabela: `# | Produto | Menções | Plataformas | Buscar na biblioteca` (link `[buscar](url)`). Explique em uma linha que muita reclamação = muita venda, e sugira rodar o método 2 com o nome do produto que mais chamou atenção para confirmar se está escalado.

Ao final de qualquer resultado, mostre o menu principal de novo.

---

## 3 · Analisar e definir produto

Em construção. Diga: "Essa opção ainda está sendo montada. Me passe o que ela deve fazer que eu adiciono." Mostre o menu principal.

## 4 · Gerar entregável

Em construção (mesma mensagem da opção 3).

## 5 · Modelar funil

Em construção (mesma mensagem da opção 3).

## 6 · Gerar criativos

Em construção (mesma mensagem da opção 3).

## 7 · Meta Ads

Em construção (mesma mensagem da opção 3).

---

## 8 · Configurações

Leia `~/.lowticket/config/config.json` (se não existir, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` antes) e mostre numerado:

```
configurações

1  país ............................ BR
2  anúncios por busca .............. 150
3  mínimo de ativos (escala) ....... 5
4  mínimo de dias (lucrativo) ...... 30
5  faixa de preço low ticket ....... R$ 7 a R$ 47
6  páginas para contar ativos ...... 15
7  pausa entre rolagens ............ 2,5 s
8  editar nichos e palavras-chave
0  voltar

digite o número
```

(use os valores reais do arquivo). Ao escolher um item, pergunte o novo valor e grave em `~/.lowticket/config/config.json` com a ferramenta de edição. Na opção 8, mostre os nichos e palavras de `~/.lowticket/config/nichos.json` e permita adicionar/remover palavras ou termos de um nicho. Confirme a mudança em uma linha e volte para as configurações.

---

## Regras

- Nunca abra o navegador do usuário (Claude in Chrome) para minerar.
- Nunca preencha formulários, compre ou se cadastre em nada.
- Uma mineração por vez. Se a Meta bloquear, pare e entregue o que já foi coletado.
- Não invente números: tudo na tabela vem da saída do script.
