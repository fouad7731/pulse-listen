"""Collecte unique + export statique, pour la GitHub Action (cron gratuit).

Enchaine : collecte Bluesky -> collecte News multi-pays (France incluse) ->
regeneration du bundle statique + PDF. La GitHub Action commit ensuite les
fichiers mis a jour, ce qui declenche un redeploiement Vercel.
"""
from __future__ import annotations

from . import export_static
from .data import collect_bulk, collect_news, storage

NEWS_COUNTRIES = ["US", "GB", "CA", "AU", "FR"]


def main() -> None:
    storage.init_db()
    print("== Collecte Bluesky ==", flush=True)
    try:
        collect_bulk.collect_all(pages=2, limit=100)
    except Exception as e:
        print(f"[warn] Bluesky : {e}", flush=True)

    print("== Collecte News (US/GB/CA/AU/FR) ==", flush=True)
    try:
        collect_news.collect_all(limit=30, countries=NEWS_COUNTRIES)
    except Exception as e:
        print(f"[warn] News : {e}", flush=True)

    print("== Export statique ==", flush=True)
    export_static.main()
    print("== Termine ==", flush=True)


if __name__ == "__main__":
    main()
