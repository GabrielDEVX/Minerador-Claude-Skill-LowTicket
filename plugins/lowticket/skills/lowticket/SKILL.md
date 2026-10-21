---
name: lowticket
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/run.sh *)
description: Central de operação low ticket com menu numerado (setup, minerar ofertas escaladas na Biblioteca de Anúncios da Meta ou no Reclame Aqui, analisar produto, gerar entregável, modelar funil, criativos, Meta Ads, configurações). Use quando o usuário digitar /lowticket, pedir o menu, ou pedir para minerar ofertas, packs, kits ou infoprodutos baratos (9,90, 19,90).
---

# Central Low Ticket

Você conduz o usuário por menus numerados. Responda sempre em português.

Todos os comandos passam por um único script (sempre exatamente assim):

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh <comando> [argumentos]
```

Os dados do usuário (ambiente Python, configurações) ficam em `~/.lowticket/`. As minerações ficam em `~/mineracao/`.

## Como mostrar os menus

- Mostre cada menu **exatamente** como está nos blocos abaixo, **dentro de um bloco de código** (três crases), para manter o alinhamento. Troque só os valores entre `{chaves}`.
- Não escreva nada antes do menu além de, no máximo, uma linha de contexto (ex.: o resultado da etapa anterior).
- Depois do menu, pare e espere a resposta. Aceite o número, o nome da opção ou um texto que deixe a escolha clara.
- Em qualquer menu, `0` volta para o anterior e `m` volta ao menu principal.
- A linha de trilha (`início › mineração › …`) mostra onde o usuário está; mantenha-a atualizada.

---

## Menu principal

```
╭──────────────────────────────────────────────╮
│          CENTRAL LOW TICKET  ·  Legacy       │
│          por @gabrielrodriguesfx             │
╰──────────────────────────────────────────────╯

  início

  [1]  ⚙️   Setup e diagnóstico
  [2]  🔎  Minerar ofertas escaladas
  [3]  🧪  Analisar e definir produto
  [4]  📦  Gerar entregável
  [5]  🧭  Modelar funil
  [6]  🎨  Gerar criativos
  [7]  📈  Meta Ads
  [8]  🛠️   Configurações

  ──────────────────────────────────────────────
  ➜  digite o número da opção

  criado por @gabrielrodriguesfx · Legacy Mentoring
  📸 siga no instagram: instagram.com/gabrielrodriguesfx
```

Na primeira vez que o usuário abrir o menu, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh status` antes. Se a saída for `SETUP_PENDENTE`, mostre esta linha acima do menu:

`⚠️  Primeira vez aqui? Rode a opção 1 antes de minerar.`

---

## 1 · Setup e diagnóstico

Mostre `⚙️  Preparando o ambiente… (leva alguns minutos na primeira vez)` e rode:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh setup
```

Interprete a saída e responda com um destes blocos:

- `SETUP_CONCLUIDO` + `META_OK anuncios_lidos=N` com N > 0:

  ```
  ✅  Tudo pronto
      Python ............ ok
      Navegador ......... ok
      Biblioteca Meta ... ok ({N} anúncios lidos no teste)
  ```
- `PYTHON_FALTANDO` → peça para rodar `xcode-select --install`, aceitar a instalação e escolher 1 de novo.
- `anuncios_lidos=0` ou `bloqueado=True` → a Meta não entregou anúncios ao navegador invisível. Sugira esperar alguns minutos e rodar de novo; se persistir, rode com `--visivel` para ver a tela: `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh meta --diagnostico --visivel`.
- Qualquer `ERRO_*` → mostre a mensagem e a linha relevante.

Depois, mostre o menu principal.

---

## 2 · Minerar ofertas escaladas

### Passo 1 — método

```
  início › mineração

  🔎  MINERAÇÃO DE OFERTAS
  ──────────────────────────────────────────────
  Escolha o método:

  [1]  📣  Reclame Aqui
           grátis · lê reclamações dos gateways BR
           (Kiwify, Hotmart, Cakto, Perfect Pay…)

  [2]  📚  Biblioteca de Anúncios
           Meta · encontra páginas escaladas

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

### Passo 2 — nicho

Leia `~/.lowticket/config/nichos.json` (se não existir, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` antes) e monte a lista com o campo `nome` de cada nicho, na ordem do arquivo. Use os emojis abaixo para os nichos padrão; para nichos que o usuário criou, use `•`.

```
  início › mineração › {método}

  🎯  ESCOLHA O NICHO
  ──────────────────────────────────────────────
  [1]  🌐  Geral (todos os nichos)
  [2]  🥗  Saúde / emagrecimento
  [3]  🧶  Artesanato
  [4]  🍰  Culinária
  [5]  💅  Beleza
  [6]  🎓  Educação / concurso
  [7]  💰  Renda / digital
  [8]  🔮  Esotérico
  [9]  🖌️   Design / social media

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

### Passo 3 — palavra-chave

Obrigatório no método 2; no método 1 é opcional (mostre a linha `[Enter]  pular` também). Leia a lista `palavras` de `~/.lowticket/config/nichos.json` e mostre em duas colunas, na ordem do arquivo:

```
  início › mineração › {método} › {nicho}

  🔑  PALAVRA-CHAVE
  ──────────────────────────────────────────────
  [1]   pack              [7]   atividades
  [2]   mega pack         [8]   projetos
  [3]   kit completo      [9]   19,90
  [4]   +500              [10]  9,90
  [5]   +1000             [11]  por apenas 9,90
  [6]   combo

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número ou escreva a sua palavra
     (várias de uma vez: 1, 3, 9)
```

Se o usuário escolher várias, rode uma mineração para cada uma, em sequência.

### Passo 4 — rodar (em segundo plano)

**NUNCA use Claude in Chrome, Playwright MCP ou qualquer ferramenta de navegador para isto.** A mineração roda num navegador invisível dentro do script, sem abrir nada na tela do usuário.

Mostre:

```
  ⏳  Minerando "{palavra}" · {nicho}
      roda em segundo plano · leva de 2 a 6 minutos
```

E rode (timeout de 10 min):

Método 2 — biblioteca:
```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh meta --palavra "{PALAVRA}" --nicho {ID_DO_NICHO}
```

Método 1 — Reclame Aqui:
```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh reclameaqui --nicho {ID_DO_NICHO} [--palavra "{PALAVRA}"]
```

`{ID_DO_NICHO}` é o campo `id` em `nichos.json` (geral, saude, artesanato, culinaria, beleza, educacao, renda, esoterico, design).

**Filtro low ticket (ligado por padrão):** o script descarta grandes empresas e e-commerce (Alibaba, Shopee, Amazon, bancos, marcas, lojas de produto físico) e só mantém páginas com cara de infoproduto. Ele pontua:
- **estrutura da copy**: gancho de dor em pergunta ("Cansado de…?"), quantidade + conteúdo ("+100 mapas mentais"), "Ideal para:" com lista de emojis (📌 ✅), promessa de organização ("tudo organizado", "de forma visual e prática"), CTA de conhecer o material ("Clique no link e saiba mais", "veja por dentro"), preço âncora ("hoje por", "de 97 por");
- **termos de infoproduto**: PDF, apostila, pack, mapas mentais, acesso imediato;
- **preço** de R$ 7 a R$ 47; **checkout ou landing** de infoproduto (Kiwify, Hotmart, Cakto, subdomínio por produto); **página com nome de pessoa**.

Se o usuário pedir "sem filtro", acrescente `--sem-filtro` ao comando.

Se a saída trouxer `NENHUM_LOWTICKET`, diga quantos anúncios foram lidos, mostre 3–5 exemplos de `DESCARTADAS` com o motivo, e sugira uma palavra mais específica (ex.: "pack pdf", "mapas mentais", "apostila", "moldes") ou outro nicho.

Se a saída trouxer `NENHUM_ANUNCIO`, `NENHUMA_RECLAMACAO` ou `BLOQUEIO`, diga o que aconteceu em uma frase e ofereça: outra palavra, o outro método ou a opção 1 para diagnosticar.

### Passo 5 — entregar o resultado (método 2)

Comece com o resumo:

```
  ✅  MINERAÇÃO CONCLUÍDA · "{palavra}" · {nicho}
  ──────────────────────────────────────────────
  {ANUNCIOS_LIDOS} anúncios lidos
  {LOWTICKET} com cara de low ticket
  {DESCARTADAS} páginas descartadas (empresas grandes / e-commerce)
```

Depois, uma tabela markdown (fora do bloco de código, para os links funcionarem) com as **até 15 melhores**:

| # | Página | Ativos | Dias | Vídeos | Preço | Sinais | Biblioteca |
|---|---|---|---|---|---|---|---|

- **Biblioteca**: `link_biblioteca` como `[abrir](url)`. Se vier vazio, use `anuncio_top`.
- **Ativos**: `ativos_pagina` (se vazio, `anuncios_na_busca` seguido de `+`).
- **Vídeos**: `variacoes_video`.
- **Sinais**: troque cada sinal por um ícone curto: `🔥 escala`, `💰 lucrativo`, `🎬 testando`, `🏷️ low ticket`.

Embaixo da tabela, a legenda (uma vez só):

```
  🔥 escala ...... página com 5+ anúncios ativos
  💰 lucrativo ... anúncio rodando há 30+ dias
  🎬 testando .... vídeos com variações (sinal de que funciona)
  🏷️ low ticket .. preço entre R$ 7 e R$ 47 nos criativos
```

Depois:
1. **⭐ Mais fortes:** em 2–3 linhas, as páginas com 🔥 + 💰 juntas.
2. Onde ficaram os arquivos: `{PASTA}/ranking.md`, `ranking.csv` e `descartadas.md`. Se o usuário perguntar por que uma página entrou, use o campo `por_que_lowticket`.
3. Feche com:

```
  💡  ENCONTROU UMA OFERTA BOA?
  ──────────────────────────────────────────────
  copie o nome da página ou o link do anúncio e:

  [3]  🧪  analisar e definir produto
  [5]  🧭  modelar funil (se já tem o link da página)

  [e]  ✏️   ensinar o filtro: "a página X é low ticket"
           ou "a página Y não é"
  [m]  ↩   menu principal
```

Se o usuário escolher `e`, siga a seção **Ensinar o filtro** (opção 8 › 12).

### Passo 5 — entregar o resultado (método 1)

Resumo no mesmo estilo (`✅ MINERAÇÃO CONCLUÍDA · Reclame Aqui · {nicho}` + reclamações lidas + produtos encontrados) e tabela `# | Produto | Menções | Plataformas | Buscar na biblioteca` (link `[buscar](url)`). Explique em uma linha que muita reclamação = muita venda, e sugira rodar o método 2 com o nome do produto que mais chamou atenção para confirmar se está escalado. Feche com o bloco "ENCONTROU UMA OFERTA BOA?".

---

## 3 a 7 · Em construção

Para as opções 3, 4, 5, 6 e 7, mostre:

```
  🚧  {NOME DA OPÇÃO}
  ──────────────────────────────────────────────
  essa opção ainda está sendo montada.

  [m]  ↩  menu principal
```

---

## 8 · Configurações

Leia `~/.lowticket/config/config.json` (se não existir, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` antes) e mostre com os valores reais:

```
  início › configurações

  🛠️   CONFIGURAÇÕES
  ──────────────────────────────────────────────
  MINERAÇÃO
  [1]   país ............................ {pais}
  [2]   anúncios por busca .............. {max_anuncios}
  [3]   mínimo de ativos (🔥 escala) ..... {min_ativos_escala}
  [4]   mínimo de dias (💰 lucrativo) .... {min_dias_lucrativo}
  [5]   faixa de preço (🏷️ low ticket) .. R$ {preco_min} a R$ {preco_max}
  [6]   páginas para contar ativos ...... {paginas_para_contar}
  [7]   pausa entre rolagens ............ {pausa_rolagem_seg} s

  NICHOS E PALAVRAS
  [8]   editar nichos e palavras-chave

  FILTRO LOW TICKET
  [9]   filtro .......................... {ligado|desligado}
  [10]  rigor (pontos mínimos) .......... {min_score_lowticket}
  [11]  lista negra e termos do filtro
  [12]  ✏️  ensinar o filtro com um anúncio

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

Ao escolher um item de 1 a 7, 9 ou 10, pergunte o novo valor e grave em `~/.lowticket/config/config.json` com a ferramenta de edição. Confirme com `✅  {item} atualizado: {antigo} → {novo}` e mostre as configurações de novo.

- **8**: mostre os nichos e palavras de `~/.lowticket/config/nichos.json` e permita adicionar/remover palavras ou termos de um nicho.
- **9**: alterne `filtro_lowticket` (true/false).
- **10**: `min_score_lowticket`. Explique: 3 = solto (entra mais coisa), 5 = padrão, 8+ = rigoroso.
- **11**: edite `~/.lowticket/config/filtros.json`: `lista_negra` (empresas/marcas a ignorar), `termos_infoproduto` (somam pontos), `termos_ecommerce` (tiram pontos), `dominios_lowticket` (checkouts e construtores de página). Para tirar um item que veio de fábrica, adicione-o à lista `removidos` do mesmo arquivo. Se o usuário disser que uma página grande ainda apareceu, ofereça adicioná-la à lista negra.

### 12 · Ensinar o filtro com um anúncio

Use quando o usuário colar a copy de um anúncio (texto ou print) ou disser "a página X é / não é low ticket".

```
  ✏️   ENSINAR O FILTRO
  ──────────────────────────────────────────────
  cole a legenda de um anúncio (ou mande o print)
  e diga se ele É ou NÃO É low ticket.
```

Se for **É low ticket**:
1. Leia a copy e identifique o que a caracteriza: o gancho de abertura, a forma de citar quantidade, a estrutura de lista, o tipo de promessa, o CTA, o preço, o público, o tipo de entrega.
2. Compare com os `padroes_copy` e `termos_infoproduto` atuais (os padrões de fábrica estão em `${CLAUDE_SKILL_DIR}/config/filtros.json`; os do usuário em `~/.lowticket/config/filtros.json`).
3. Para o que ainda não é coberto, proponha **no máximo 5** adições: termos novos (palavras ou expressões curtas) e/ou padrões novos (`{"nome": "...", "peso": 1 ou 2, "regex": "..."}`). A regex deve ser genérica, sem acento, e casar com variações da mesma estrutura, não só com esse anúncio.
4. Mostre as propostas numeradas e pergunte quais gravar. Grave no `~/.lowticket/config/filtros.json` do usuário (crie as listas se não existirem; não edite o arquivo de fábrica).

Se for **NÃO é low ticket**: proponha adicionar o nome da página/domínio à `lista_negra` ou expressões típicas à `termos_ecommerce`.

Depois de gravar, teste em silêncio: confirme que a copy colada agora soma os pontos esperados (ou é descartada) rodando:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh testar "COPY COLADA AQUI"
```

E mostre `✅  filtro atualizado · esse anúncio agora soma {N} pontos (mínimo {min})`.

---

## Créditos

Criado por **Gabriel Rodrigues · @gabrielrodriguesfx** (Legacy Mentoring). Se o usuário perguntar quem criou a ferramenta, responda isso. Mantenha os créditos nos menus.

## Regras

- Nunca abra o navegador do usuário (Claude in Chrome) para minerar.
- Nunca preencha formulários, compre ou se cadastre em nada.
- Uma mineração por vez. Se a Meta bloquear, pare e entregue o que já foi coletado.
- Não invente números: tudo na tabela vem da saída do script.
