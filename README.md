# Legacy Mentoring · Central Low Ticket + Nutra

Criado por **Gabriel Rodrigues** · [@gabrielrodriguesfx](https://instagram.com/gabrielrodriguesfx)

[![Siga no Instagram](https://img.shields.io/badge/Siga%20no%20Instagram-@gabrielrodriguesfx-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/gabrielrodriguesfx)

## Sobre mim

Sou o **Gabriel Rodrigues** ([@gabrielrodriguesfx](https://instagram.com/gabrielrodriguesfx)), fundador da **Legacy Mentoring**.

Hoje faturo **mais de 1 milhão de euros por mês** vendendo nutra na Europa, mas sei bem quais são os gargalos de quem está começando.

Por isso resolvi ajudar com o meu conhecimento, e esta ferramenta é uma das formas de fazer isso. Como eu já rodei e comecei pelo low ticket, esta ferramenta auxilia iniciantes no mercado digital!

## O que é

Plugin para o Claude Code que minera ofertas escaladas na Biblioteca de Anúncios da Meta, em segundo plano e sem abrir o seu navegador. Ele tem dois modos:

**🏷️ Low ticket (Brasil)**
- Encontra infoprodutos baratos (packs, kits, apostilas, mapas mentais · R$ 7 a 47) por nicho e palavra-chave.
- Descarta grandes empresas e e-commerce (Alibaba, Shopee, Amazon, lojas de produto físico).
- Reconhece a estrutura da copy de low ticket: gancho de dor, "+100 …", "Ideal para:" com lista de emojis, CTA "saiba mais" e preço âncora.
- Também minera pelo Reclame Aqui: os produtos mais reclamados nas plataformas BR (Kiwify, Hotmart, Cakto…).
- E pelo **urlscan.io**: encontra páginas que usam o rastreador da **UTMify** (ofertas do digital rodando tráfego) e entrega o link para conferir os anúncios de cada domínio na biblioteca. Não precisa de setup.

**💊 Nutra (qualquer país)**
- Escolha o país (EUA, Alemanha, França, Espanha, Itália, Reino Unido, Portugal, Brasil ou qualquer outro) e a busca é feita **no idioma daquele país**.
- 7 categorias com mais de 100 mecanismos prontos: emagrecimento, diabetes, ED, próstata, prosperidade, renda extra e relacionamento.
- Exemplos: truque do cavalo, truque do bicarbonato (*baking soda trick*), truque da gelatina, truque da aveia, truque da canela, truque do gengibre…
- Identifica a plataforma (Digistore24, ClickBank, BuyGoods, MaxWeb) e os sinais de VSL/advertorial.

**Em todos os modos**, a ferramenta mostra os sinais de escala:
- 🔥 **escala**: página com 5+ anúncios ativos
- 💰 **lucrativo**: anúncio rodando há 30+ dias
- 🎬 **testando**: vídeos com variações

E entrega o link da biblioteca de cada página.

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
2. Depois, **2 (minerar ofertas escaladas)**:
   - **Low ticket**: escolha o método (Reclame Aqui, Biblioteca de Anúncios ou urlscan.io), o nicho e a palavra-chave.
   - **Nutra**: escolha o país, a categoria e o mecanismo.

Os resultados ficam em `~/mineracao/` (para abrir: `open ~/mineracao`).

## Novidades

**1.4.0**
- Novo método **urlscan.io**: busca páginas que carregam a UTMify, agrupa por domínio, mostra título, data do último scan, plataforma e o print do urlscan, com o link pronto para a Biblioteca de Anúncios.
- Configurações › 15 e 16: chave grátis do urlscan.io (opcional, aumenta o limite) e rastreadores buscados.
- Correção: o status só fica PRONTO quando o navegador foi realmente baixado. Se você já tinha feito o setup antes, rode a opção 1 de novo uma vez.

**1.3.0**
- Filtro de nutra treinado com anúncios reais (DE/FR): gancho de dor em pergunta em vários idiomas, lista de benefícios com ✨, CTA "Klicken Sie hier / Click here", promessa de transformação e advertorial ("L'énigme est résolue").
- Lê o **nome do produto** (ex.: Slim Jara) e reconhece página com nome de pessoa.
- Nova coluna **tipo provável** da landing (advertorial, VSL, presell, quiz, checkout, loja), deduzido pelo link e pelo título. A página não é aberta: para ver a landing de verdade, abra o anúncio pelo celular.
- As correções de fábrica agora chegam a todos nas atualizações; o que você ensinou ao filtro continua salvo.

**1.2.0**
- Modo **Nutra**: mineração por mecanismo em qualquer país, com busca no idioma local.
- 7 categorias e mais de 100 mecanismos prontos (os principais aparecem primeiro; os outros ficam a um toque).
- Filtro próprio para nutra e detecção de plataforma (Digistore24, ClickBank, BuyGoods, MaxWeb).

**1.1.1**
- Créditos ao criador nos menus.

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
| `LIMITE` (urlscan.io) | Espere alguns minutos ou cadastre uma chave grátis do urlscan.io (Configurações › 15) |

---

## Me siga

Gostou da ferramenta? Me segue no Instagram para receber as atualizações, novas skills e conteúdo de low ticket:

👉 **[instagram.com/gabrielrodriguesfx](https://instagram.com/gabrielrodriguesfx)**

Feito por **Gabriel Rodrigues** · [@gabrielrodriguesfx](https://instagram.com/gabrielrodriguesfx) · Legacy Mentoring
