#!/usr/bin/env python3
"""Monta o link de checkout com UTMs dinamicos da Meta (compativel com a UTMify).

  python3 utm.py "https://pay.cakto.com.br/abc"
"""
import sys
from urllib.parse import urlparse, urlencode

# campos dinamicos que a Meta substitui no clique (lidos pela UTMify)
PADRAO = {
    "utm_source": "facebook",
    "utm_medium": "paid",
    "utm_campaign": "{{campaign.name}}|{{campaign.id}}",
    "utm_content": "{{ad.name}}|{{ad.id}}",
    "utm_term": "{{adset.name}}|{{adset.id}}",
    "utm_medium_placement": "{{placement}}",
}


def montar(base):
    sep = "&" if urlparse(base).query else "?"
    return base + sep + urlencode(PADRAO, safe="{}|")


def main():
    if len(sys.argv) < 2:
        sys.exit('uso: utm.py "https://seu-checkout"')
    link = montar(sys.argv[1])
    print(link)
    print("\nCole este link no destino do anuncio. A UTMify le esses campos e mostra "
          "a origem de cada venda (campanha, conjunto e anuncio).")


if __name__ == "__main__":
    main()
