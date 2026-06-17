"""Collecteur bulk de posts Bluesky via l'endpoint public searchPosts.

Decouverte cle : le host `api.bsky.app` autorise app.bsky.feed.searchPosts
SANS authentification (reponse 200 + curseur de pagination), contrairement a
`public.api.bsky.app` qui renvoie 403.

On itere sur tous les mots-cles de zones.ALL_QUERIES, on pagine via cursor,
on filtre (langue EN, longueur min, dedup regex), on enrichit en sentiment,
puis on stocke en SQLite.

Usage :
    python3 -m app.data.collect_bulk                  # collecte standard
    python3 -m app.data.collect_bulk --pages 5        # 5 pages par mot-cle
    python3 -m app.data.collect_bulk --limit 100      # 100 posts par page
"""
from __future__ import annotations

import argparse
import re
import sys
import time

import requests

from . import storage, zones
from .sentiment import analyze_text

SEARCH_URL = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"

# Compilation regex word-boundary par mot-cle (anti faux-positifs)
_KEYWORD_PATTERNS: dict[str, re.Pattern] = {
    kw.lower(): re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
    for _, kws in [(t.code, t.keywords) for t in zones.THEMES]
    for kw in kws
}

HEADERS = {"User-Agent": "pulse-listen/1.0 (social-listening demo)"}


def _matches_keyword(text: str, keyword: str) -> bool:
    """Verifie que le mot-cle apparait bien en tant que mot (word boundary)."""
    pattern = _KEYWORD_PATTERNS.get(keyword.lower())
    if not pattern:
        return True
    return bool(pattern.search(text.lower()))


def _parse_post(item: dict, keyword: str, theme: str) -> dict | None:
    """Transforme un item searchPosts en dict normalise, ou None si filtre."""
    post = item or {}
    record = post.get("record") or {}
    text = (record.get("text") or "").strip()

    if len(text) < zones.MIN_TEXT_LEN:
        return None

    langs = record.get("langs") or []
    if zones.LANG not in langs:
        return None

    if not _matches_keyword(text, keyword):
        return None

    author = post.get("author") or {}
    return {
        "uri": post.get("uri", ""),
        "author_handle": author.get("handle", ""),
        "text": text,
        "created_at": record.get("createdAt", ""),
        "lang": zones.LANG,
        "like_count": post.get("likeCount", 0),
        "repost_count": post.get("repostCount", 0),
        "reply_count": post.get("replyCount", 0),
        "keyword": keyword,
        "theme": theme,
        "source": "bluesky",
        "country": "global",  # Bluesky ne fournit pas de geoloc fiable par post
    }


def fetch_keyword(keyword: str, theme: str, pages: int, limit: int) -> list[dict]:
    """Pagine searchPosts pour un mot-cle. Retourne les posts filtres."""
    collected: list[dict] = []
    cursor: str | None = None

    for page in range(pages):
        params = {
            "q": keyword,
            "limit": limit,
            "lang": zones.LANG,
            "sort": "latest",
        }
        if cursor:
            params["cursor"] = cursor

        try:
            resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
        except requests.RequestException as e:
            print(f"  [warn] '{keyword}' p{page+1} erreur reseau : {e}", flush=True)
            break

        if resp.status_code != 200:
            print(f"  [warn] '{keyword}' p{page+1} HTTP {resp.status_code}", flush=True)
            break

        data = resp.json()
        posts = data.get("posts", [])
        if not posts:
            break

        for item in posts:
            parsed = _parse_post(item, keyword, theme)
            if parsed and parsed["uri"]:
                collected.append(parsed)

        cursor = data.get("cursor")
        if not cursor:
            break

        time.sleep(0.4)  # politesse API

    return collected


def collect_all(pages: int = 3, limit: int = 100) -> int:
    """Collecte tous les mots-cles, enrichit en sentiment, stocke. Retourne nb insere."""
    storage.init_db()

    total_fetched = 0
    total_inserted = 0
    n_queries = len(zones.ALL_QUERIES)

    print(f"[collect_bulk] {n_queries} mots-cles, {pages} pages x {limit} posts max\n")

    for i, (keyword, theme) in enumerate(zones.ALL_QUERIES, 1):
        posts = fetch_keyword(keyword, theme, pages, limit)
        total_fetched += len(posts)

        for p in posts:
            label, score = analyze_text(p["text"])
            p["sentiment_label"] = label
            p["sentiment_score"] = score

        inserted = storage.save_posts(posts)
        total_inserted += inserted

        print(
            f"[{i:>2}/{n_queries}] {keyword:<18} theme={theme:<12} "
            f"recup={len(posts):>3}  nouveaux={inserted:>3}",
            flush=True,
        )

    total_db = storage.count_posts()
    print(
        f"\n[collect_bulk] Termine. "
        f"{total_fetched} posts recuperes, {total_inserted} nouveaux inseres."
    )
    print(f"[collect_bulk] Total en base : {total_db} posts.")
    return total_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte bulk Bluesky (no auth)")
    parser.add_argument("--pages", type=int, default=3,
                        help="Nombre de pages par mot-cle (defaut 3)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Posts par page, max 100 (defaut 100)")
    args = parser.parse_args()

    inserted = collect_all(pages=args.pages, limit=args.limit)
    sys.exit(0 if inserted >= 0 else 1)


if __name__ == "__main__":
    main()
