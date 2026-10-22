#!/usr/bin/env python3
"""Breakdown de copy/VSL: extrai sinais objetivos de uma copy (ou texto de landing)
para o Claude dissecar o angulo, o mecanismo e a estrutura.

O script faz a parte mecanica (preco, plataforma pelo link, gatilhos, blocos);
a interpretacao (angulo, promessa, lead) fica com o Claude.

  python3 breakdown.py "cole a copy aqui" [--link https://...]
  echo "copy" | python3 breakdown.py -
"""
import argparse
import json
import re
import sys

from comum import _regex, _sem_acento, carregar_filtros, plataforma, precos

# gatilhos clássicos de resposta direta (rótulo -> regex, multi-idioma básico)
GATILHOS = {
    "pergunta de abertura (gancho)": r"^\W*[^.?!]{0,180}\?",
    "urgência / escassez": r"(agora|hoje|so hoje|ultim[oa]s|acaba|expira|vagas|limitad|antes que|before|today|jetzt|maintenant)",
    "prova / autoridade": r"(estudo|cientist|medic|doutor|dr\.|comprovad|pesquisa|aprovad|study|doctor|clinically|ärzte)",
    "prova social": r"(\d[\d.\s]*(mil|mi|milhoes|pessoas|clientes|alunos|k\b)|mais de \d|todo mundo|everyone|\d+\.\d{3})",
    "história / identificação": r"(eu (tinha|era|vivia|descobri|passei)|minha (vida|historia)|quando eu|aconteceu comigo|i was|my story)",
    "inimigo comum / vilão": r"(industria|big pharma|midia|governo|eles nao querem|escondem|segredo que|the truth|verdade que)",
    "mecanismo único": r"(metodo|truque|ritual|protocolo|sistema|formula|segredo|descoberta|method|trick|secret)",
    "garantia / reversão de risco": r"(garantia|risco zero|devolv|reembolso|satisfa|money back|guarantee)",
    "promessa de tempo / rapidez": r"(\d+\s*(dias|dia|semanas|minutos|horas|seg)|rapid|em poucos|imediato|hoje mesmo|days|minutes)",
    "escada de valor / bônus": r"(bonus|bônus|brinde|de r?\$?\s?\d+\s*por|leve \d|gratis|free)",
    "CTA": r"(clique|compre|garanta|acesse|baixe|quero|adicione|click|buy|order now|get|comecar)",
}

# estrutura típica de VSL / carta (marcos)
BLOCOS = [
    ("abertura/gancho", r"(voce (sabia|ja|quer|precisa)|imagine|e se|descobri|pare de|atencao|cansad[oa]|mude davon|tired of)"),
    ("agitação do problema", r"(problema|dor|sofr|cansad|frustrad|tentou de tudo|nada funciona|struggl|frustrat)"),
    ("virada/descoberta", r"(mas (entao|quando|foi quando)|ate que|descobri|a verdade e|o segredo|turns out|the truth)"),
    ("mecanismo/solução", r"(metodo|sistema|protocolo|formula|funciona assim|por isso|e por isso que|how it works)"),
    ("prova", r"(resultado|antes e depois|veja|olha o que|depoiment|caso|result|testimonial)"),
    ("oferta", r"(hoje por|por apenas|de r?\$?\s?\d|investimento|valor|plano|acesso|offer|only)"),
    ("urgência/fechamento", r"(ultim[ao]s|agora|nao perca|clique|garanta|decis[aã]o|don.t wait|last chance)"),
]


def achar(texto):
    t = _sem_acento(texto)
    gat = [nome for nome, rx in GATILHOS.items() if _regex(rx).search(t)]
    blocos = [nome for nome, rx in BLOCOS if _regex(rx).search(t)]
    return gat, blocos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("copy", help="texto da copy/VSL, ou - para ler da entrada")
    ap.add_argument("--link", default="", help="link da landing/checkout, se tiver")
    a = ap.parse_args()
    texto = sys.stdin.read() if a.copy == "-" else a.copy
    if not texto.strip():
        sys.exit("cole a copy a ser analisada")

    gat, blocos = achar(texto)
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    ps = sorted(set(precos(texto)))
    plat = plataforma(a.link) if a.link else ""
    palavras = len(re.findall(r"\w+", texto))

    saida = {
        "gancho_provavel": (re.split(r"(?<=[.?!])\s", linhas[0])[0][:160] if linhas else ""),
        "palavras": palavras,
        "tamanho": "VSL/carta longa" if palavras > 350 else ("copy média" if palavras > 120 else "copy curta"),
        "precos_citados": [("R$ %.2f" % p).replace(".", ",") for p in ps],
        "plataforma": plat,
        "gatilhos_detectados": gat,
        "estrutura_detectada": blocos,
        "faltando_na_estrutura": [nome for nome, _ in BLOCOS if nome not in blocos],
    }
    print("SINAIS:")
    print(json.dumps(saida, ensure_ascii=False, indent=1))
    print("\nAGORA_O_CLAUDE: use estes sinais + a leitura da copy para montar o breakdown "
          "(ângulo, público, dor, promessa, mecanismo, prova, oferta, estrutura e o que copiar do ÂNGULO "
          "com palavras próprias). Não copie frases do concorrente.")


if __name__ == "__main__":
    main()
