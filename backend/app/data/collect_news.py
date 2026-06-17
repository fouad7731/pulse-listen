"""Collecteur Google News via flux RSS public (gratuit, sans auth, sans cle).

Reddit ayant ferme son acces JSON public (403 sans OAuth), on ajoute une 2e
source reellement accessible : Google News RSS. Angle complementaire interessant
pour la veille : Bluesky = parole sociale, News = couverture mediatique.

Endpoint : https://news.google.com/rss/search?q=<mot-cle>&hl=en-US&gl=US&ceid=US:en

Meme pipeline que Bluesky : memes themes/mots-cles, filtre longueur, regex
word-boundary, sentiment VADER, stockage. Tagge source='news'.

Dimension PAYS : Google News expose une edition par pays via le param `gl`
(US / GB / CA ...). C'est une donnee REELLE (edition mediatique du pays), pas
une geoloc inventee. On collecte donc par defaut sur plusieurs pays et on
tagge chaque post avec son pays d'origine.

Usage :
    python3 -m app.data.collect_news
    python3 -m app.data.collect_news --limit 30
    python3 -m app.data.collect_news --countries US,GB,CA
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

from . import storage, zones
from .sentiment import analyze_text

RSS_BASE = "https://news.google.com/rss/search"

# Editions Google News par pays : (code_pays, gl, ceid). hl reste en anglais
# (VADER = anglais) ; seul le marche mediatique (gl/ceid) change.
COUNTRIES: dict[str, tuple[str, str]] = {
    "US": ("US", "US:en"),   # Etats-Unis
    "GB": ("GB", "GB:en"),   # Royaume-Uni
    "CA": ("CA", "CA:en"),   # Canada
    "AU": ("AU", "AU:en"),   # Australie
}
DEFAULT_COUNTRIES = ["US", "GB", "CA"]

_KEYWORD_PATTERNS: dict[str, re.Pattern] = {
    kw.lower(): re.compile(r"\b" + re.escape(kw.lower()) + r"\b")
    for t in zones.THEMES for kw in t.keywords
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pulse-listen/1.0)"}

_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    """Retire le HTML residuel des descriptions RSS."""
    return _TAG_RE.sub("", text or "").strip()


def _matches_keyword(text: str, keyword: str) -> bool:
    pattern = _KEYWORD_PATTERNS.get(keyword.lower())
    return bool(pattern.search(text.lower())) if pattern else True


def _to_iso(pub_date: str) -> str:
    try:
        return parsedate_to_datetime(pub_date).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return ""


def _parse_item(item: ET.Element, keyword: str, theme: str, country: str) -> dict | None:
    title = _clean(item.findtext("title", ""))
    link = item.findtext("link", "") or ""
    source_el = item.find("source")
    media = (source_el.text if source_el is not None else "") or "news"
    text = title

    if len(text) < zones.MIN_TEXT_LEN:
        return None
    if not _matches_keyword(text, keyword):
        return None
    if not link:
        return None

    return {
        # le lien + pays font office d'identifiant unique (un meme article peut
        # apparaitre dans plusieurs editions pays)
        "uri": f"news:{country}:{link}",
        "author_handle": media,
        "text": text,
        "created_at": _to_iso(item.findtext("pubDate", "")),
        "lang": zones.LANG,
        "like_count": 0,
        "repost_count": 0,
        "reply_count": 0,
        "keyword": keyword,
        "theme": theme,
        "source": "news",
        "country": country,
    }


def fetch_keyword(keyword: str, theme: str, limit: int, country: str = "US") -> list[dict]:
    gl, ceid = COUNTRIES.get(country, ("US", "US:en"))
    url = f"{RSS_BASE}?q={quote_plus(keyword)}&hl=en-US&gl={gl}&ceid={ceid}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
    except requests.RequestException as e:
        print(f"  [warn] '{keyword}' ({country}) erreur reseau : {e}", flush=True)
        return []
    if resp.status_code != 200:
        print(f"  [warn] '{keyword}' ({country}) HTTP {resp.status_code}", flush=True)
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"  [warn] '{keyword}' ({country}) parse RSS : {e}", flush=True)
        return []

    out = []
    for item in root.iter("item"):
        parsed = _parse_item(item, keyword, theme, country)
        if parsed:
            out.append(parsed)
        if len(out) >= limit:
            break
    return out


def collect_all(limit: int = 30, countries: list[str] | None = None) -> int:
    storage.init_db()
    countries = countries or DEFAULT_COUNTRIES
    total_fetched = 0
    total_inserted = 0
    n = len(zones.ALL_QUERIES)
    print(
        f"[collect_news] {n} mots-cles x {len(countries)} pays "
        f"({', '.join(countries)}) via Google News RSS\n"
    )

    for country in countries:
        print(f"--- Pays : {country} ---", flush=True)
        for i, (keyword, theme) in enumerate(zones.ALL_QUERIES, 1):
            posts = fetch_keyword(keyword, theme, limit, country)
            total_fetched += len(posts)
            for p in posts:
                label, score = analyze_text(p["text"])
                p["sentiment_label"] = label
                p["sentiment_score"] = score
            inserted = storage.save_posts(posts)
            total_inserted += inserted
            print(
                f"[{country}][{i:>2}/{n}] {keyword:<18} theme={theme:<12} "
                f"recup={len(posts):>3}  nouveaux={inserted:>3}",
                flush=True,
            )
            time.sleep(0.5)

    print(
        f"\n[collect_news] Termine. {total_fetched} recuperes, "
        f"{total_inserted} nouveaux. Total base : {storage.count_posts()}."
    )
    return total_inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Collecte Google News RSS (no auth)")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument(
        "--countries",
        type=str,
        default=",".join(DEFAULT_COUNTRIES),
        help="Codes pays separes par virgule (US,GB,CA,AU)",
    )
    args = parser.parse_args()
    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    collect_all(limit=args.limit, countries=countries)
    sys.exit(0)


if __name__ == "__main__":
    main()
