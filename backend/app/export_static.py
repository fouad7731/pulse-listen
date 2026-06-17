"""Export STATIQUE des donnees pour un hebergement gratuit (Vercel + GitHub).

Au lieu d'un backend allume 24/7 (payant), on genere ici tout ce dont le
frontend a besoin sous forme de fichiers statiques :
  - frontend/public/data/data.json : bundle (overview, timeline, trend,
    forecast, top_posts, keywords, alerts) pour chaque combinaison
    theme x pays utilisee par le dashboard.
  - frontend/public/reports/*.pdf  : rapports PDF pre-generes.

Une GitHub Action relance la collecte + cet export toutes les 6h, commit, et
Vercel redeploie -> dashboard a jour, sans serveur.
"""
from __future__ import annotations

import json
from pathlib import Path

from .data import storage, zones
from .ml import aggregate, alerts, report

# Racine repo -> frontend/public
_PUBLIC = Path(__file__).resolve().parents[2] / "frontend" / "public"
_DATA_DIR = _PUBLIC / "data"
_REPORTS_DIR = _PUBLIC / "reports"

# "all" = pas de filtre. Les pays viennent des donnees reelles.
_ALL = "all"


def _country_keys() -> list[str]:
    counts = storage.count_by_country()
    return [_ALL] + sorted(counts.keys())


def _theme_keys() -> list[str]:
    return [_ALL] + [t.code for t in zones.THEMES]


def _opt(v: str) -> str | None:
    return None if v == _ALL else v


def build_bundle() -> dict:
    countries = _country_keys()
    themes = _theme_keys()

    overview: dict[str, dict] = {}
    alerts_map: dict[str, dict] = {}
    for c in countries:
        overview[c] = aggregate.overview(_opt(c))
        alerts_map[c] = alerts.summary(_opt(c))

    timeline: dict[str, list] = {}
    trend: dict[str, dict] = {}
    forecast: dict[str, dict] = {}
    top_posts: dict[str, list] = {}
    keywords: dict[str, list] = {}
    for t in themes:
        for c in countries:
            key = f"{t}|{c}"
            timeline[key] = aggregate.timeline(_opt(t), _opt(c))
            trend[key] = aggregate.trend(_opt(t), _opt(c))
            forecast[key] = aggregate.forecast(_opt(t), _opt(c))
            top_posts[key] = aggregate.top_posts(_opt(t), 15, _opt(c))
            keywords[key] = aggregate.top_keywords(_opt(t), 12, _opt(c))

    return {
        "themes": [
            {"code": t.code, "name": t.name, "keywords": t.keywords}
            for t in zones.THEMES
        ],
        "countries": [c for c in countries if c != _ALL],
        "overview": overview,
        "alerts": alerts_map,
        "timeline": timeline,
        "trend": trend,
        "forecast": forecast,
        "top_posts": top_posts,
        "keywords": keywords,
    }


def build_reports() -> int:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in _theme_keys():
        for c in _country_keys():
            pdf = report.build_pdf(_opt(c), _opt(t))
            (_REPORTS_DIR / f"{t}__{c}.pdf").write_bytes(pdf)
            n += 1
    return n


def main() -> None:
    storage.init_db()
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle()
    (_DATA_DIR / "data.json").write_text(
        json.dumps(bundle, ensure_ascii=False), encoding="utf-8"
    )
    n_pdf = build_reports()
    print(
        f"[export_static] data.json ecrit ({len(bundle['countries'])} pays, "
        f"{len(bundle['timeline'])} combinaisons) + {n_pdf} PDF."
    )


if __name__ == "__main__":
    main()
