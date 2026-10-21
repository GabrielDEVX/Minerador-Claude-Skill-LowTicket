#!/usr/bin/env python3
"""Swipe file: guarda ofertas e criativos favoritos em ~/.lowticket/favoritos.json.

  python3 favoritos.py add --json '{"pagina":"...","link_biblioteca":"..."}' --tags "nutra,DE"
  python3 favoritos.py listar [--tag nutra] [--busca receita]
  python3 favoritos.py remover <id>
"""
import argparse, json, sys, time
from comum import DADOS

ARQ = DADOS / "favoritos.json"


def _ler():
    if ARQ.exists():
        try:
            return json.loads(ARQ.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _gravar(d):
    DADOS.mkdir(parents=True, exist_ok=True)
    ARQ.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("--json", required=True); a.add_argument("--tags", default="")
    a.add_argument("--nota", default="")
    l = sub.add_parser("listar"); l.add_argument("--tag", default=""); l.add_argument("--busca", default="")
    r = sub.add_parser("remover"); r.add_argument("id")
    args = ap.parse_args()
    favs = _ler()
    if args.cmd == "add":
        try:
            item = json.loads(args.json)
        except Exception as e:
            sys.exit(f"JSON inválido: {e}")
        chave = str(item.get("page_id") or item.get("link_biblioteca") or item.get("landing") or item.get("pagina") or "")
        if any(str(f.get("page_id") or f.get("link_biblioteca") or f.get("landing") or f.get("pagina")) == chave for f in favs):
            print("JA_SALVO"); return
        item["id"] = str(int(time.time() * 1000))[-9:]
        item["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
        if args.nota:
            item["nota"] = args.nota
        item["quando"] = time.strftime("%Y-%m-%d")
        favs.append(item); _gravar(favs)
        print(f"SALVO: {item['id']} · {item.get('pagina','')}")
    elif args.cmd == "listar":
        res = favs
        if args.tag:
            res = [f for f in res if args.tag.lower() in [t.lower() for t in f.get("tags", [])]]
        if args.busca:
            b = args.busca.lower()
            res = [f for f in res if b in json.dumps(f, ensure_ascii=False).lower()]
        print(f"TOTAL: {len(res)}")
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif args.cmd == "remover":
        n = len(favs); favs = [f for f in favs if f.get("id") != args.id]
        _gravar(favs)
        print("REMOVIDO" if len(favs) < n else "NAO_ENCONTRADO")


if __name__ == "__main__":
    main()
