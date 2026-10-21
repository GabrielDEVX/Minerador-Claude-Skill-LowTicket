---
name: lowticket
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/run.sh *)
description: Central de operação low ticket e nutra com menu numerado (setup, minerar ofertas escaladas na Biblioteca de Anúncios da Meta ou no Reclame Aqui, minerar nutra por mecanismo em qualquer país e idioma, analisar produto, gerar entregável, modelar funil, criativos, Meta Ads, configurações). Use quando o usuário digitar /lowticket, pedir o menu, ou pedir para minerar ofertas, packs, kits, infoprodutos baratos (9,90, 19,90) ou ofertas de nutra (truque do cavalo, truque da gelatina etc.) em países como EUA, Alemanha e França.
---

# Central Low Ticket

Você conduz o usuário por menus numerados. Responda sempre em português.

Todos os comandos passam por um único script (sempre exatamente assim):

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh <comando> [argumentos]
```

Os dados do usuário (ambiente Python, configurações) ficam em `~/.lowticket/`. As minerações ficam em `~/mineracao/`.

**Configurações:** para saber os valores, nichos, palavras, países e mecanismos atuais, rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` (mostra tudo já combinado: fábrica + usuário). Para mudar algo, edite os arquivos do usuário em `~/.lowticket/config/`:
- `config.json` e os acréscimos de `filtros.json` e `nutra.json` guardam **só o que o usuário mudou ou acrescentou** (os padrões de fábrica vêm sempre da versão instalada, então as atualizações chegam a todos);
- para desligar um item de fábrica, coloque o texto ou o nome do padrão na lista `removidos` do arquivo correspondente;
- `nichos.json` é a lista completa de nichos e palavras do low ticket e pode ser editada diretamente.

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

### Passo 0 — tipo de oferta

```
  início › mineração

  🔎  O QUE VOCÊ QUER MINERAR?
  ──────────────────────────────────────────────
  [1]  🏷️   Low ticket
           infoprodutos baratos no Brasil
           (packs, kits, apostilas · R$ 7 a 47)

  [2]  💊  Nutra
           ofertas de VSL por mecanismo
           (truque do cavalo, da gelatina…)
           em qualquer país e idioma

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

- **1** → siga os passos 1 a 5 abaixo (low ticket).
- **2** → pule para a seção **Mineração de nutra**.

### Passo 1 — método (low ticket)

```
  início › mineração › low ticket

  🔎  MINERAÇÃO LOW TICKET
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

Use os `nichos` da saída de `run.sh config` e monte a lista com o campo `nome` de cada nicho, na ordem do arquivo. Use os emojis abaixo para os nichos padrão; para nichos que o usuário criou, use `•`.

```
  início › mineração › low ticket › {método}

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

Obrigatório no método 2; no método 1 é opcional (mostre a linha `[Enter]  pular` também). Use a lista `palavras` de `nichos` (saída de `run.sh config`) e mostre em duas colunas, na ordem do arquivo:

```
  início › mineração › low ticket › {método} › {nicho}

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

## Mineração de nutra

Os países, as categorias e os mecanismos vêm do campo `nutra` da saída de `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` (fábrica + acréscimos do usuário em `~/.lowticket/config/nutra.json`).

### N1 — país

Mostre os `paises` do arquivo, na ordem, em duas colunas:

```
  início › mineração › nutra

  🌍  EM QUAL PAÍS?
  ──────────────────────────────────────────────
  [1]  🇺🇸  EUA             [5]  🇮🇹  Itália
  [2]  🇩🇪  Alemanha        [6]  🇬🇧  Reino Unido
  [3]  🇫🇷  França          [7]  🇵🇹  Portugal
  [4]  🇪🇸  Espanha         [8]  🇧🇷  Brasil

  [9]  ✏️   outro país (digite o nome)

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

Se for **outro país**: descubra o código ISO de 2 letras (ex.: Suíça = CH, Áustria = AT, Holanda = NL, Polônia = PL, Canadá = CA, México = MX) e o idioma dos anúncios. Se o país tiver mais de um idioma relevante (Suíça: alemão/francês/italiano; Bélgica: francês/holandês; Canadá: inglês/francês; Luxemburgo: francês/alemão), pergunte qual em uma linha:

```
  🗣️   A Suíça anuncia em mais de um idioma. Qual?
  [1] alemão   [2] francês   [3] italiano
```

Depois de confirmar, ofereça em uma linha salvar o país na lista (`paises` do nutra.json do usuário).

### N2 — categoria

```
  início › mineração › nutra › {bandeira} {país}

  🧬  CATEGORIA
  ──────────────────────────────────────────────
  [1]  🔥  Emagrecimento / metabolismo
  [2]  🩸  Diabetes / glicose
  [3]  🍆  Desempenho sexual / virilidade (ED)
  [4]  🔵  Próstata / hormônios
  [5]  💸  Prosperidade / manifestação
  [6]  📱  Renda extra / internet
  [7]  ❤️   Relacionamento / atração

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

(Use as `categorias` do arquivo, com `emoji` e `nome`; categorias criadas pelo usuário entram no fim.)

### N3 — mecanismo

Mostre **só os `principais`** da categoria, em duas colunas, com nomes curtos (pode encurtar "Truque do/da" para "T." se a linha passar de 50 caracteres):

```
  início › mineração › nutra › {bandeira} {país} › {categoria}

  🧪  MECANISMO
  ──────────────────────────────────────────────
  [1]  T. do cavalo           [5]  T. da melancia
  [2]  T. do bicarbonato      [6]  T. do rei Salomão
  [3]  T. do sal azul         [7]  Receita natural de viagra
  [4]  T. do mel amazônico    [8]  T. do touro indiano

  [+]  ver todos ({total} mecanismos)
  [*]  rodar todos os principais (um por vez)
  ✏️   ou digite o seu mecanismo

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o(s) número(s) · ex.: 1, 2
```

- **[+]**: mostre `principais` + `outras` numerados em sequência, em duas colunas, e peça o número de novo.
- **[*]**: avise `⏳ são {N} buscas, leva de {N×3} a {N×6} min. Recomendo até 3 por vez para a Meta não bloquear. Confirma? (s/n)`.
- Mecanismo digitado que não está na lista: depois do resultado, ofereça em uma linha salvar na categoria (`outras` do nutra.json do usuário).

### N4 — traduzir para o idioma do país

A busca **tem que ser no idioma do país** escolhido. Para cada mecanismo, crie **1 ou 2 variações** do jeito que os anúncios nativos desse país escrevem. Não faça tradução literal palavra por palavra: use o termo de busca que o público e os anunciantes usam ali.

Regras:
- Brasil: use o termo em português do Brasil como está.
- Use o nome local do ingrediente e o formato que os anúncios usam para "truque": EN "trick" / "hack", DE "Trick" (também composto: "Pferdetrick"), FR "astuce", ES "truco", IT "trucco", PT-PT "truque".
- Quando um ingrediente tem nome próprio no mercado, use esse nome. Exemplos: "bicarbonato" nos EUA é "baking soda"; "gelatina bariátrica" nos EUA é "gelatin trick" ou "jello trick"; "sal rosa" nos EUA é "pink salt trick"; "Mounjaro natural" nos EUA é "natural mounjaro" ou "nature's mounjaro".
- A 2ª variação deve ser uma forma alternativa real (sinônimo, grafia composta, ordem diferente), e não a mesma frase com outra pontuação.
- Não traduza nomes de marca ou de pessoa (Mounjaro, Ozempic, Salomão → Solomon em EN, Salomon em DE/FR).

Mostre antes de rodar:

```
  🗣️   buscando em {idioma} · {bandeira} {país}
      "Truque do cavalo" → "horse trick" · "horse hack"
```

### N5 — rodar (em segundo plano)

**NUNCA use Claude in Chrome nem outra ferramenta de navegador.** Mostre:

```
  ⏳  Minerando "{mecanismo}" · {bandeira} {país}
      roda em segundo plano · leva de 2 a 6 minutos
```

E rode (timeout de 10 min), um comando por mecanismo, com as variações em `--palavra` repetido:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh meta --modo nutra --pais {CODIGO} --nicho {ID_CATEGORIA} --rotulo "{MECANISMO EM PT}" --palavra "{VARIAÇÃO 1}" --palavra "{VARIAÇÃO 2}"
```

O **filtro de nutra** descarta grandes empresas (Amazon, lojas, marcas) mas **não** penaliza e-commerce (nutra físico usa frete grátis). Ele pontua, em vários idiomas:
- **link**: plataforma (Digistore24, ClickBank, BuyGoods, MaxWeb, CartPanda) ou domínio genérico de saúde, estilo de vida ou notícia (ex.: `aktivlebenheute.de`, `sante-decouvertes.fr`);
- **copy**: gancho de dor em pergunta ("Müde davon…?", "Tired of…?", "Fatiguée de…?"), lista de benefícios com ✨ ✅ 👉, verbos de benefício ("unterstützt", "hilft", "supports"), apetite/metabolismo, CTA ("Klicken Sie hier", "Click here", "Cliquez ici"), transformação ("neues Lebensgefühl", "new you"), advertorial/mistério ("L'énigme est résolue", "ce qui se cache vraiment", "the truth about"), vídeo, mecanismo, urgência e dose/tempo;
- **nome de produto** que aparece na legenda e no título (ex.: "Slim Jara");
- **página com nome de pessoa** (ex.: "Sofia Fischer") e **criativo em vídeo**.

A ferramenta **não abre as landings**. O `tipo_provavel` (advertorial, VSL, presell, quiz, plataforma/checkout, loja) é deduzido só pelo link, pelo domínio e pelo título do anúncio. Se o usuário pedir "sem filtro", acrescente `--sem-filtro`.

Se a saída trouxer `NENHUM_NUTRA`, mostre 3–5 exemplos de `DESCARTADAS` e sugira outras variações do termo no idioma do país. Para `NENHUM_ANUNCIO` ou `BLOQUEIO`, siga o mesmo tratamento do low ticket.

### N6 — resultado

```
  ✅  MINERAÇÃO NUTRA CONCLUÍDA · "{mecanismo}" · {bandeira} {país}
  ──────────────────────────────────────────────
  buscado como: "{variação 1}" · "{variação 2}"
  {ANUNCIOS_LIDOS} anúncios lidos
  {NUTRA} com cara de oferta de nutra
  {DESCARTADAS} páginas descartadas
```

Tabela markdown (fora do bloco de código), até 15 linhas:

| # | Página | Produto | Ativos | Dias | Vídeos | Tipo provável | Plataforma | Sinais | Biblioteca |
|---|---|---|---|---|---|---|---|---|---|

- **Produto**: campo `produto` (vazio → `—`).
- **Tipo provável**: campo `tipo_provavel` (vazio → `—`).
- **Plataforma**: campo `plataforma` (vazio → `—`).
- **Sinais**: `🔥 escala`, `💰 lucrativo`, `🎬 testando`, `🎥 VSL`.
- **Biblioteca**: `[abrir](link_biblioteca)` (vazio → `anuncio_top`).

Legenda (uma vez):

```
  🔥 escala ...... página com 5+ anúncios ativos
  💰 lucrativo ... anúncio rodando há 30+ dias
  🎬 testando .... vídeos com variações (sinal de que funciona)
  🎥 VSL ......... leva para VSL / plataforma de afiliado
```

Depois:
- **⭐ Mais fortes:** as páginas com 🔥 + 💰.
- **📱 Para ver a página de verdade:** uma linha explicando que o tipo é só provável e que, para ver o que a landing realmente diz, o ideal é abrir o anúncio pelo link da biblioteca **no celular**, clicando no botão do anúncio. Muitas páginas de nutra têm filtro de tráfego e mostram outra coisa para quem abre direto.
- Onde ficaram os arquivos (`ranking.md`, `ranking.csv`, `descartadas.md`).

E o bloco final:

```
  💡  PRÓXIMOS PASSOS
  ──────────────────────────────────────────────
  [1]  🔁  mesmo mecanismo em outro país
  [2]  🧪  outro mecanismo da mesma categoria
  [3]  🧪  analisar e definir produto
  [5]  🧭  modelar funil (se já tem o link da página)
  [m]  ↩   menu principal
```

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

Rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh config` e mostre com os valores do campo `config`:

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

  NUTRA
  [13]  países e mecanismos de nutra
  [14]  rigor do filtro nutra ........... {min_score_nutra}

  [0]  ← voltar

  ──────────────────────────────────────────────
  ➜  digite o número
```

Ao escolher um item de 1 a 7, 9, 10 ou 14, pergunte o novo valor e grave **só essa chave** em `~/.lowticket/config/config.json` com a ferramenta de edição. Confirme com `✅  {item} atualizado: {antigo} → {novo}` e mostre as configurações de novo.

- **8**: mostre os nichos e palavras de `~/.lowticket/config/nichos.json` e permita adicionar/remover palavras ou termos de um nicho.
- **9**: alterne `filtro_lowticket` (true/false).
- **13**: mostre as categorias do campo `nutra` (saída de `run.sh config`) e permita adicionar/remover mecanismos (em `principais` ou `outras`), criar uma categoria nova (`id`, `nome`, `emoji`) ou adicionar um país (`codigo`, `nome`, `bandeira`, `idioma`). Grave só os acréscimos, em `~/.lowticket/config/nutra.json` (para tirar um mecanismo de fábrica, coloque-o em `removidos`).
- **14**: `min_score_nutra`. Explique: 2 = solto, 3 = padrão, 5+ = rigoroso.
- **10**: `min_score_lowticket`. Explique: 3 = solto (entra mais coisa), 5 = padrão, 8+ = rigoroso.
- **11**: edite os acréscimos em `~/.lowticket/config/filtros.json`: `lista_negra` (empresas/marcas a ignorar), `termos_infoproduto` (somam pontos), `termos_ecommerce` (tiram pontos), `dominios_lowticket` (checkouts e construtores de página). Para tirar um item que veio de fábrica, adicione-o à lista `removidos` do mesmo arquivo. Se o usuário disser que uma página grande ainda apareceu, ofereça adicioná-la à lista negra.

### 12 · Ensinar o filtro com um anúncio

Use quando o usuário colar a copy de um anúncio (texto ou print) ou disser "a página X é / não é low ticket" (ou nutra). Para anúncio de nutra, os padrões vão em `padroes_nutra` e os domínios em `dominios_nutra`, e o teste usa `--modo nutra`.

```
  ✏️   ENSINAR O FILTRO
  ──────────────────────────────────────────────
  cole a legenda de um anúncio (ou mande o print)
  e diga se ele É ou NÃO É low ticket.
```

Se for **É low ticket**:
1. Leia a copy e identifique o que a caracteriza: o gancho de abertura, a forma de citar quantidade, a estrutura de lista, o tipo de promessa, o CTA, o preço, o público, o tipo de entrega.
2. Rode `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh filtros` para ver todos os padrões atuais (fábrica + usuário) e `bash ${CLAUDE_SKILL_DIR}/scripts/run.sh testar "COPY" [--modo nutra]` para ver quais já casam. Compare com `padroes_copy`/`termos_infoproduto` (low ticket) ou `padroes_nutra`/`dominios_nutra` (nutra). Os acréscimos do usuário ficam em `~/.lowticket/config/filtros.json`.
3. Para o que ainda não é coberto, proponha **no máximo 5** adições: termos novos (palavras ou expressões curtas) e/ou padrões novos (`{"nome": "...", "peso": 1 ou 2, "regex": "..."}`). A regex deve ser genérica, sem acento, e casar com variações da mesma estrutura, não só com esse anúncio.
4. Mostre as propostas numeradas e pergunte quais gravar. Grave no `~/.lowticket/config/filtros.json` do usuário (crie as listas se não existirem; não edite o arquivo de fábrica).

Se for **NÃO é low ticket**: proponha adicionar o nome da página/domínio à `lista_negra` ou expressões típicas à `termos_ecommerce`.

Depois de gravar, teste em silêncio: confirme que a copy colada agora soma os pontos esperados (ou é descartada) rodando:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/run.sh testar "COPY COLADA AQUI" [--modo nutra]
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
