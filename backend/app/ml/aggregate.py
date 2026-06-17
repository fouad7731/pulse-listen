"""Agregation des tendances : volume + sentiment par jour / theme.

Equivalent honnete du module forecast de Pulse, mais sans inventer de stats :
- on agrege le volume reel de posts et le sentiment moyen
- on calcule une tendance simple (moyenne mobile + delta vs periode precedente)
- le 'forecast' est explicitement marque comme indisponible tant qu'on n'a pas
  assez d'historique (garde-fou : pas de fausse prediction ML).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd

from ..data import storage, zones

# Nb min de jours distincts requis pour tenter une vraie projection
MIN_DAYS_FOR_FORECAST = 14


def _load_df() -> pd.DataFrame:
    conn = storage.get_connection()
    df = pd.read_sql_query("SELECT * FROM posts", conn)
    conn.close()
    if df.empty:
        return df
    # format="mixed" : les dates RSS melangent les offsets (-04:00, Z, +00:00).
    # Sans ca, pandas infere un format unique et coerce a NaT les lignes qui
    # ne matchent pas -> perte silencieuse des posts News multi-pays.
    df["created_at"] = pd.to_datetime(
        df["created_at"], errors="coerce", utc=True, format="mixed"
    )
    df = df.dropna(subset=["created_at"])
    df["date"] = df["created_at"].dt.date.astype(str)
    return df


def _filter(df: pd.DataFrame, theme: str | None = None,
            country: str | None = None) -> pd.DataFrame:
    """Filtre commun par theme et/ou pays."""
    if theme:
        df = df[df["theme"] == theme]
    if country:
        df = df[df["country"] == country]
    return df


def overview(country: str | None = None) -> dict:
    """KPIs globaux + repartition par theme + repartition par pays."""
    df = _load_df()
    if df.empty:
        return {
            "total_posts": 0,
            "sentiment_avg": 0.0,
            "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
            "by_theme": [],
            "by_country": [],
            "n_days": 0,
        }

    # repartition pays calculee sur tout le dataset (avant filtre pays)
    by_country = []
    for c in sorted(df["country"].fillna("global").unique()):
        subc = df[df["country"].fillna("global") == c]
        by_country.append({
            "country": c,
            "posts": int(len(subc)),
            "sentiment_avg": round(float(subc["sentiment_score"].mean()), 4),
        })

    if country:
        df = df[df["country"] == country]
        if df.empty:
            return {
                "total_posts": 0,
                "sentiment_avg": 0.0,
                "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
                "by_theme": [],
                "by_country": by_country,
                "n_days": 0,
            }

    breakdown = df["sentiment_label"].value_counts().to_dict()
    by_theme = []
    for code in sorted(df["theme"].unique()):
        sub = df[df["theme"] == code]
        try:
            name = zones.get_theme(code).name
        except KeyError:
            name = code
        by_theme.append({
            "theme": code,
            "name": name,
            "posts": int(len(sub)),
            "sentiment_avg": round(float(sub["sentiment_score"].mean()), 4),
            "positive": int((sub["sentiment_label"] == "positive").sum()),
            "neutral": int((sub["sentiment_label"] == "neutral").sum()),
            "negative": int((sub["sentiment_label"] == "negative").sum()),
        })

    return {
        "total_posts": int(len(df)),
        "sentiment_avg": round(float(df["sentiment_score"].mean()), 4),
        "sentiment_breakdown": {
            "positive": int(breakdown.get("positive", 0)),
            "neutral": int(breakdown.get("neutral", 0)),
            "negative": int(breakdown.get("negative", 0)),
        },
        "by_theme": by_theme,
        "by_country": by_country,
        "n_days": int(df["date"].nunique()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def timeline(theme: str | None = None, country: str | None = None) -> list[dict]:
    """Volume + sentiment par jour (filtre optionnel theme et/ou pays)."""
    df = _load_df()
    if df.empty:
        return []
    df = _filter(df, theme, country)
    if df.empty:
        return []

    grouped = (
        df.groupby("date")
        .agg(
            posts=("uri", "count"),
            sentiment_avg=("sentiment_score", "mean"),
            positive=("sentiment_label", lambda s: int((s == "positive").sum())),
            negative=("sentiment_label", lambda s: int((s == "negative").sum())),
        )
        .reset_index()
        .sort_values("date")
    )
    grouped["sentiment_avg"] = grouped["sentiment_avg"].round(4)
    return grouped.to_dict(orient="records")


def trend(theme: str | None = None, country: str | None = None) -> dict:
    """Tendance simple : volume total, delta derniere moitie vs premiere moitie."""
    tl = timeline(theme, country)
    if not tl:
        return {"available": False, "reason": "no_data"}

    n = len(tl)
    half = n // 2 or 1
    first = sum(d["posts"] for d in tl[:half]) or 1
    second = sum(d["posts"] for d in tl[half:])
    delta_pct = round((second - first) / first * 100, 1)

    return {
        "available": True,
        "n_days": n,
        "total_posts": sum(d["posts"] for d in tl),
        "first_half_posts": first,
        "second_half_posts": second,
        "delta_pct": delta_pct,
        "direction": "up" if delta_pct > 5 else "down" if delta_pct < -5 else "flat",
    }


def forecast(theme: str | None = None, country: str | None = None) -> dict:
    """Projection HONNETE : refuse de predire si historique insuffisant.

    Pas de fausse stat ML : tant qu'on n'a pas MIN_DAYS_FOR_FORECAST jours
    distincts, on renvoie un garde-fou clair. Sinon, on extrapole une moyenne
    mobile 7j (methode naive transparente, pas un modele entraine deguise).
    """
    tl = timeline(theme, country)
    n_days = len(tl)

    if n_days < MIN_DAYS_FOR_FORECAST:
        return {
            "available": False,
            "reason": "insufficient_history",
            "n_days": n_days,
            "min_required": MIN_DAYS_FOR_FORECAST,
            "message": (
                f"Historique insuffisant ({n_days} jours sur "
                f"{MIN_DAYS_FOR_FORECAST} requis). La collecte continue : "
                "une projection fiable sera disponible apres accumulation."
            ),
        }

    series = pd.Series([d["posts"] for d in tl])
    ma7 = series.rolling(window=7, min_periods=1).mean()
    next_estimate = round(float(ma7.iloc[-1]), 1)
    return {
        "available": True,
        "method": "naive_moving_average_7d",
        "n_days": n_days,
        "next_day_estimate": next_estimate,
        "note": "Estimation naive (moyenne mobile 7j), pas un modele ML entraine.",
    }


def top_posts(theme: str | None = None, limit: int = 15,
              country: str | None = None) -> list[dict]:
    """Posts les plus engageants (par likes)."""
    df = _load_df()
    if df.empty:
        return []
    df = _filter(df, theme, country)
    if df.empty:
        return []
    cols = ["author_handle", "text", "theme", "keyword", "source", "country",
            "sentiment_label", "sentiment_score", "like_count", "repost_count"]
    top = df.sort_values("like_count", ascending=False).head(limit)
    return top[cols].to_dict(orient="records")


def top_keywords(theme: str | None = None, limit: int = 12,
                 country: str | None = None) -> list[dict]:
    """Mots-cles (sujets boissons) les plus presents, avec sentiment moyen.

    On s'appuie sur la colonne `keyword` : le terme de recherche qui a remonte
    chaque post. C'est honnete et directement lie au domaine boissons (pas de
    bruit type stopwords). Filtrable par theme et/ou pays.
    """
    df = _load_df()
    if df.empty:
        return []
    df = _filter(df, theme, country)
    df = df[df["keyword"].notna() & (df["keyword"] != "")]
    if df.empty:
        return []

    grouped = (
        df.groupby("keyword")
        .agg(
            posts=("uri", "count"),
            sentiment_avg=("sentiment_score", "mean"),
            theme=("theme", "first"),
        )
        .reset_index()
        .sort_values("posts", ascending=False)
        .head(limit)
    )
    grouped["sentiment_avg"] = grouped["sentiment_avg"].round(4)
    return grouped.to_dict(orient="records")
